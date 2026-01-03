# 微信消息推送服务

基于 Python + FastAPI 实现的微信消息推送服务，支持微信公众平台和企业微信两种渠道，提供简洁的 HTTP API 接口。

## 功能特性

- ✅ **多平台支持**：支持微信公众平台和企业微信消息推送
- ✅ **简洁的 API**：提供标准的 HTTP 接口（GET/POST），易于集成
- ✅ **安全认证**：API Key 认证机制，防止接口滥用
- ✅ **签名验证**：支持 HMAC-SHA256 签名验证（可选），防止重放攻击
- ✅ **原生体验**：支持微信原生弹窗提醒和声音提醒
- ✅ **消息详情页**：自动生成消息详情页面，支持自定义跳转链接
- ✅ **结构化日志**：完整的请求/响应日志记录
- ✅ **自动文档**：自动生成交互式 API 文档（Swagger/ReDoc）
- ✅ **易于部署**：支持 Docker 容器化部署

## 快速开始

### 环境要求

- Python >= 3.11
- pip 或 Poetry

### 安装依赖

```bash
# 使用 pip
pip install -e ".[dev]"

# 或使用 Poetry
poetry install
```

### 配置 API Keys

API Key 用于接口访问权限验证，有两种配置方式：

#### 方式一：环境变量（推荐）

创建 `.env` 文件：

```bash
# 必需的配置：有效的项目识别码列表（逗号分隔）
API_KEYS=your_api_key_1,your_api_key_2,your_api_key_3

# 可选：签名验证密钥（启用签名验证时需要）
API_KEY_SECRET=your_secret_key_here

# 可选：服务端口（默认 5566）
PORT=5566

# 可选：日志级别（默认 INFO）
LOG_LEVEL=INFO

# 可选：默认微信模板 ID（微信公众平台）
DEFAULT_WECHAT_TEMPLATE_ID=your_template_id

# 可选：默认企业微信 AgentID（企业微信）
DEFAULT_WORKWECHAT_AGENTID=1000001
```

#### 方式二：配置文件

复制示例文件并编辑：

```bash
cp api_keys.json.example api_keys.json
```

编辑 `api_keys.json`：

```json
{
  "valid_keys": [
    "your_api_key_1",
    "your_api_key_2",
    "your_api_key_3"
  ]
}
```

**优先级**：环境变量 > 配置文件

### 运行服务

```bash
# 方式一：直接运行
python -m wxpush.main

# 方式二：使用 uvicorn
uvicorn wxpush.main:app --host 0.0.0.0 --port 5566 --reload

# 方式三：使用启动脚本
# Windows
启动服务.bat

# Linux/macOS
./启动服务.sh
```

### 访问 API 文档

服务启动后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:5566/docs
- **ReDoc**: http://localhost:5566/redoc
- **健康检查**: http://localhost:5566/health

## API 使用说明

### 接口地址

- **基础路径**: `/send`
- **支持方法**: GET, POST
- **Content-Type**: `application/json` (POST 请求)

### 请求参数

| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|----------|------|
| api_key | String | 是 | 项目识别码（API Key） |
| title | String | 是 | 消息标题 |
| content | String | 是 | 消息具体内容 |
| appid | String | 是 | 微信 AppID（微信公众平台）或企业 ID Corpid（企业微信） |
| secret | String | 是 | 微信 AppSecret 或企业 Secret |
| userid | String | 是 | 接收用户的 OpenID（微信）或 UserID（企业微信） |
| base_url | String | 否 | 消息详情跳转 URL（默认使用服务自动生成的详情页） |
| channel | String | 否 | 推送渠道：`wechat`（微信公众平台）或 `workwechat`（企业微信），默认 `wechat` |
| template_id | String | 否 | 模板消息 ID（微信公众平台，可选，可通过配置设置默认值） |
| agentid | String | 否 | 应用 AgentID（企业微信，可选，可通过配置设置默认值） |
| timestamp | Integer | 否 | Unix 时间戳（签名验证时必填） |
| signature | String | 否 | HMAC-SHA256 签名（可选） |

### 响应格式

#### 成功响应

```json
{
  "errcode": 0,
  "errmsg": "ok",
  "msgid": "消息ID"
}
```

#### 错误响应

```json
{
  "errcode": 错误码,
  "errmsg": "错误描述"
}
```

### 使用示例

#### GET 请求

```bash
curl "http://localhost:5566/send?api_key=your_api_key&title=服务器通知&content=服务已重启&appid=wx123456&secret=your_secret&userid=openid123&channel=wechat"
```

#### POST 请求

```bash
curl -X POST "http://localhost:5566/send" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "title": "服务器通知",
    "content": "服务已重启",
    "appid": "wx123456",
    "secret": "your_secret",
    "userid": "openid123",
    "channel": "wechat",
    "base_url": "https://example.com/detail"
  }'
```

#### Python 示例

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:5566/send",
        json={
            "api_key": "your_api_key",
            "title": "测试消息",
            "content": "这是一条测试消息",
            "appid": "wx123456",
            "secret": "your_secret",
            "userid": "openid123",
            "channel": "wechat"
        }
    )
    print(response.json())
```

#### JavaScript 示例

```javascript
fetch('http://localhost:5566/send', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    api_key: 'your_api_key',
    title: '测试消息',
    content: '这是一条测试消息',
    appid: 'wx123456',
    secret: 'your_secret',
    userid: 'openid123',
    channel: 'wechat'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### 签名验证（可选）

如果启用了签名验证（设置了 `API_KEY_SECRET`），需要在请求中包含 `timestamp` 和 `signature` 参数。

#### 签名生成算法

1. 构造签名字符串：`api_key + timestamp + payload`
   - `payload` 为请求参数（JSON 字符串，按 key 排序，不包含 `signature`）
2. 使用 HMAC-SHA256 算法，密钥为 `API_KEY_SECRET`，对签名字符串进行加密
3. 将加密结果转换为十六进制字符串

#### Python 签名生成示例

```python
import hmac
import hashlib
import time
import json

def generate_signature(api_key: str, secret: str, payload: dict) -> tuple[int, str]:
    """生成签名."""
    timestamp = int(time.time())
    # 移除 signature 字段
    payload_clean = {k: v for k, v in payload.items() if k != 'signature'}
    # 按 key 排序并转换为 JSON
    payload_str = json.dumps(payload_clean, sort_keys=True, separators=(',', ':'))
    # 构造签名字符串
    message = f"{api_key}{timestamp}{payload_str}"
    # 生成 HMAC-SHA256 签名
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature

# 使用示例
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

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40001 | 项目识别码无效 |
| 40002 | 识别码签名验证失败 |
| 40003 | 请求时间戳过期 |
| 42200 | 请求参数验证失败 |
| 50000 | 服务器内部错误 |

## 消息详情页

当不提供 `base_url` 参数时，服务会自动生成指向消息详情页的 URL。详情页会显示消息的标题、内容和时间戳，支持移动端和桌面端访问。

访问示例：
```
http://localhost:5566/detail?title=测试标题&content=测试内容
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_security.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 代码格式化

```bash
# 使用 black 格式化代码
black src tests

# 使用 ruff 检查代码风格
ruff check src tests

# 自动修复
ruff check --fix src tests
```

### 类型检查

```bash
mypy src
```

## 部署说明

### 环境变量配置

部署时需要设置以下环境变量：

- `API_KEYS`：**必需**，有效的 API Key 列表（逗号分隔）
- `API_KEY_SECRET`：可选，签名验证密钥
- `PORT`：可选，服务端口（默认 5566）
- `LOG_LEVEL`：可选，日志级别（默认 INFO）
- `DEFAULT_WECHAT_TEMPLATE_ID`：可选，默认微信模板 ID
- `DEFAULT_WORKWECHAT_AGENTID`：可选，默认企业微信 AgentID

### 生产环境建议

1. **使用环境变量配置**：避免将 API Keys 写入代码或配置文件
2. **启用签名验证**：在生产环境中启用签名验证以提高安全性
3. **配置反向代理**：使用 Nginx 等反向代理服务器
4. **日志管理**：配置日志收集和分析系统
5. **监控告警**：配置服务监控和告警机制

### 常见问题

#### 1. API Key 验证失败

- 检查 `API_KEYS` 环境变量或 `api_keys.json` 文件是否配置正确
- 确认请求中的 `api_key` 参数值与配置的一致
- 检查是否有空格或特殊字符

#### 2. 签名验证失败

- 确认 `API_KEY_SECRET` 配置正确
- 检查签名生成算法是否正确
- 确认时间戳在有效窗口内（5 分钟）

#### 3. 微信 API 调用失败

- 检查 `appid` 和 `secret` 是否正确
- 确认微信应用配置正确（模板消息、企业微信应用等）
- 查看服务日志获取详细错误信息

## 项目结构

```
wxpush/
├── src/wxpush/          # 源代码
│   ├── core/            # 核心模块（配置、安全、日志）
│   ├── routers/         # 路由定义
│   ├── schemas/         # 数据模型
│   ├── services/        # 业务逻辑（微信服务）
│   ├── utils/           # 工具类（HTTP 客户端）
│   └── main.py          # 应用入口
├── tests/               # 测试代码
├── templates/           # HTML 模板
├── api_keys.json.example # API Key 配置示例
├── pyproject.toml       # 项目配置
└── README.md            # 项目文档
```

## 许可证

MIT License

## 参考文档

- [PRD 文档](./PRD.md)
- [开发清单](./开发阶段和步骤清单.md)
- [技术栈分析](./技术栈分析.md)
- [测试说明](./测试说明.md)

## 贡献

欢迎提交 Issue 和 Pull Request！
