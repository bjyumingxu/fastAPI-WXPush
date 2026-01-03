# 部署文档

本文档说明如何部署微信消息推送服务。

## 部署方式

### 方式一：直接运行（开发/测试环境）

#### 1. 安装依赖

```bash
pip install -e ".[dev]"
```

#### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
export API_KEYS="your_api_key_1,your_api_key_2"
export API_KEY_SECRET="your_secret_key"  # 可选
export PORT=5566  # 可选
```

或使用 `.env` 文件（复制 `.env.example` 并修改）：

```bash
cp .env.example .env
# 编辑 .env 文件
```

#### 3. 启动服务

```bash
# 直接运行
python -m wxpush.main

# 或使用 uvicorn
uvicorn wxpush.main:app --host 0.0.0.0 --port 5566
```

### 方式二：使用 systemd（Linux 生产环境）

#### 1. 创建系统服务文件

创建 `/etc/systemd/system/wxpush.service`：

```ini
[Unit]
Description=微信消息推送服务
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/wxpush
Environment="PATH=/path/to/venv/bin"
Environment="API_KEYS=your_api_key_1,your_api_key_2"
Environment="API_KEY_SECRET=your_secret_key"
ExecStart=/path/to/venv/bin/uvicorn wxpush.main:app --host 0.0.0.0 --port 5566
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start wxpush

# 设置开机自启
sudo systemctl enable wxpush

# 查看服务状态
sudo systemctl status wxpush

# 查看日志
sudo journalctl -u wxpush -f
```

### 方式三：使用 Supervisor（推荐）

#### 1. 安装 Supervisor

```bash
pip install supervisor
```

#### 2. 创建配置文件

创建 `/etc/supervisor/conf.d/wxpush.conf`：

```ini
[program:wxpush]
command=/path/to/venv/bin/uvicorn wxpush.main:app --host 0.0.0.0 --port 5566
directory=/path/to/wxpush
user=your_user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/wxpush.log
environment=API_KEYS="your_api_key_1,your_api_key_2",API_KEY_SECRET="your_secret_key"
```

#### 3. 启动服务

```bash
# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start wxpush

# 查看状态
sudo supervisorctl status wxpush
```

### 方式四：使用 Nginx 反向代理（生产环境推荐）

#### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置 Nginx

创建 `/etc/nginx/sites-available/wxpush`：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    # 如果需要 HTTPS
    # listen 443 ssl;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5566;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 3. 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/wxpush /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

## 环境变量配置说明

### 必需配置

- **API_KEYS**：有效的项目识别码列表，多个值使用逗号分隔
  ```bash
  API_KEYS=key1,key2,key3
  ```

### 可选配置

- **API_KEY_SECRET**：签名验证密钥（启用签名验证时需要）
- **PORT**：服务端口（默认：5566）
- **LOG_LEVEL**：日志级别（默认：INFO）
- **DEFAULT_WECHAT_TEMPLATE_ID**：默认微信模板 ID
- **DEFAULT_WORKWECHAT_AGENTID**：默认企业微信 AgentID

### 配置优先级

1. 环境变量（最高优先级）
2. `.env` 文件
3. `api_keys.json` 文件（仅用于 API Keys）
4. 默认值

## API Key 配置和管理

### 方式一：环境变量（推荐）

```bash
export API_KEYS="key1,key2,key3"
```

### 方式二：配置文件

创建 `api_keys.json`：

```json
{
  "valid_keys": [
    "key1",
    "key2",
    "key3"
  ]
}
```

### 安全管理建议

1. **不要将 API Keys 提交到版本控制**
   - 使用 `.gitignore` 忽略 `.env` 和 `api_keys.json` 文件
   - 使用环境变量或密钥管理服务

2. **定期轮换 API Keys**
   - 定期更换 API Keys
   - 使用密钥管理服务（如 AWS Secrets Manager、Vault 等）

3. **最小权限原则**
   - 为不同项目分配不同的 API Keys
   - 限制 API Keys 的使用范围

## 签名验证使用说明（可选）

如果设置了 `API_KEY_SECRET`，需要在请求中包含签名信息。

### 签名生成步骤

1. **构造签名字符串**
   ```
   message = api_key + timestamp + payload
   ```
   - `payload` 为请求参数的 JSON 字符串（按 key 排序，不包含 `signature`）

2. **生成 HMAC-SHA256 签名**
   ```
   signature = HMAC-SHA256(message, API_KEY_SECRET)
   ```

3. **在请求中包含 `timestamp` 和 `signature`**

### Python 示例

```python
import hmac
import hashlib
import time
import json

def generate_signature(api_key: str, secret: str, payload: dict) -> tuple[int, str]:
    timestamp = int(time.time())
    # 移除 signature 字段
    payload_clean = {k: v for k, v in payload.items() if k != 'signature'}
    # 按 key 排序并转换为 JSON
    payload_str = json.dumps(payload_clean, sort_keys=True, separators=(',', ':'))
    # 构造签名字符串
    message = f"{api_key}{timestamp}{payload_str}"
    # 生成签名
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature

# 使用
payload = {
    "api_key": "your_api_key",
    "title": "测试",
    "content": "内容",
    "appid": "wx123456",
    "secret": "your_secret",
    "userid": "openid123"
}
timestamp, signature = generate_signature("your_api_key", "your_secret", payload)
payload["timestamp"] = timestamp
payload["signature"] = signature
```

### 时间戳验证

- 时间戳必须在当前时间的 ±5 分钟内
- 过期的时间戳会被拒绝（错误码：40003）

## 监控和日志

### 日志位置

- 控制台输出：结构化日志输出到 stdout
- 文件日志：如果使用 Supervisor，日志在 `/var/log/wxpush.log`

### 健康检查

```bash
curl http://localhost:5566/health
```

响应：
```json
{
  "status": "ok"
}
```

### 监控建议

1. **健康检查监控**
   - 定期调用 `/health` 接口
   - 设置告警规则

2. **日志监控**
   - 收集服务日志
   - 监控错误率和响应时间

3. **性能监控**
   - 监控服务 CPU、内存使用情况
   - 监控请求 QPS 和延迟

## 常见问题排查

### 1. 服务启动失败

**问题**：`ModuleNotFoundError: No module named 'wxpush'`

**解决**：
- 确认已安装依赖：`pip install -e "."`
- 确认 Python 版本 >= 3.11

### 2. API Key 验证失败

**问题**：返回 401 错误，错误码 40001

**解决**：
- 检查环境变量 `API_KEYS` 是否设置正确
- 检查请求中的 `api_key` 参数是否正确
- 确认没有额外的空格或特殊字符

### 3. 签名验证失败

**问题**：返回 401 错误，错误码 40002

**解决**：
- 确认 `API_KEY_SECRET` 配置正确
- 检查签名生成算法是否正确
- 确认时间戳在有效窗口内（±5 分钟）
- 确认 payload 中不包含 `signature` 字段

### 4. 微信 API 调用失败

**问题**：返回错误，提示微信 API 调用失败

**解决**：
- 检查 `appid` 和 `secret` 是否正确
- 确认微信应用配置正确
- 查看服务日志获取详细错误信息
- 确认网络连接正常

### 5. 端口被占用

**问题**：`Address already in use`

**解决**：
- 更改端口：设置环境变量 `PORT=其他端口`
- 或停止占用端口的进程

## 安全建议

1. **使用 HTTPS**：在生产环境中使用 HTTPS 加密传输
2. **启用签名验证**：提高 API 安全性
3. **限制访问**：使用防火墙或 Nginx 限制访问来源
4. **定期更新**：及时更新依赖包和安全补丁
5. **日志审计**：定期检查日志，发现异常访问

## 性能优化建议

1. **使用生产级 ASGI 服务器**
   ```bash
   uvicorn wxpush.main:app --workers 4 --host 0.0.0.0 --port 5566
   ```

2. **配置连接池**
   - HTTP 客户端已配置连接池，无需额外配置

3. **监控和调优**
   - 监控服务性能指标
   - 根据实际负载调整 worker 数量



