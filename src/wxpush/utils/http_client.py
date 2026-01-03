"""HTTP 客户端封装模块 - 使用 httpx AsyncClient."""

from typing import Any

import httpx
from httpx import AsyncClient, Response, Timeout

# 全局 HTTP 客户端实例（单例模式）
_async_client: AsyncClient | None = None


def get_http_client() -> AsyncClient:
    """获取全局 HTTP 客户端实例.

    Returns:
        全局 AsyncClient 实例

    Raises:
        RuntimeError: 如果客户端未初始化
    """
    global _async_client
    if _async_client is None:
        raise RuntimeError("HTTP client not initialized. Call init_http_client() first.")
    return _async_client


def init_http_client() -> AsyncClient:
    """初始化全局 HTTP 客户端实例.

    在应用启动时调用，创建单例客户端实例。

    Returns:
        初始化的 AsyncClient 实例
    """
    global _async_client
    if _async_client is None:
        # 配置超时时间
        timeout = Timeout(
            connect=5.0,  # 连接超时：5秒
            read=10.0,  # 读取超时：10秒
            write=5.0,  # 写入超时：5秒
            pool=5.0,  # 连接池超时：5秒
        )

        _async_client = AsyncClient(
            timeout=timeout,
            http2=True,  # 启用 HTTP/2
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=100,
            ),
        )
    return _async_client


async def close_http_client() -> None:
    """关闭全局 HTTP 客户端实例.

    在应用关闭时调用，确保资源正确释放。
    """
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None


async def fetch_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: Timeout | float | None = None,
) -> dict[str, Any]:
    """发送 GET 请求并返回 JSON 响应.

    Args:
        url: 请求 URL
        params: 查询参数
        headers: 请求头
        timeout: 超时时间（可选，覆盖默认超时）

    Returns:
        解析后的 JSON 响应数据

    Raises:
        httpx.HTTPStatusError: 如果 HTTP 状态码表示错误
        httpx.RequestError: 如果请求失败
        ValueError: 如果响应不是有效的 JSON
    """
    client = get_http_client()
    response: Response = await client.get(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()  # 自动处理 HTTP 错误
    return response.json()


async def post_json(
    url: str,
    *,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: Timeout | float | None = None,
) -> dict[str, Any]:
    """发送 POST 请求并返回 JSON 响应.

    Args:
        url: 请求 URL
        json: JSON 数据（优先使用）
        data: 表单数据（如果 json 为 None）
        headers: 请求头
        timeout: 超时时间（可选，覆盖默认超时）

    Returns:
        解析后的 JSON 响应数据

    Raises:
        httpx.HTTPStatusError: 如果 HTTP 状态码表示错误
        httpx.RequestError: 如果请求失败
        ValueError: 如果响应不是有效的 JSON
    """
    client = get_http_client()
    response: Response = await client.post(
        url,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()  # 自动处理 HTTP 错误
    return response.json()


async def get_access_token(
    token_url: str,
    *,
    appid: str,
    secret: str,
    grant_type: str = "client_credential",
) -> tuple[str, int]:
    """获取访问令牌（Access Token）.

    通用的获取访问令牌函数，适用于微信公众平台和企业微信。

    Args:
        token_url: 获取 token 的 API 地址
        appid: 应用 ID（微信 AppID 或企业微信 Corpid）
        secret: 应用密钥（微信 AppSecret 或企业微信 Secret）
        grant_type: 授权类型，默认 "client_credential"

    Returns:
        (access_token, expires_in) 元组

    Raises:
        httpx.HTTPStatusError: 如果 HTTP 请求失败
        ValueError: 如果响应格式不正确或包含错误
    """
    params = {
        "grant_type": grant_type,
        "appid": appid,
        "secret": secret,
    }

    # 企业微信使用 corpid 和 corpsecret
    # 这里统一使用 appid 和 secret，调用方需要正确传递参数

    try:
        response_data = await fetch_json(token_url, params=params)

        # 检查是否有错误
        if "errcode" in response_data:
            errcode = response_data.get("errcode", 0)
            errmsg = response_data.get("errmsg", "Unknown error")
            if errcode != 0:
                raise ValueError(f"WeChat API error: errcode={errcode}, errmsg={errmsg}")

        # 提取 access_token 和 expires_in
        access_token = response_data.get("access_token")
        expires_in = response_data.get("expires_in", 7200)  # 默认 7200 秒

        if not access_token:
            raise ValueError("Access token not found in response")

        return access_token, expires_in

    except httpx.HTTPStatusError as e:
        raise ValueError(f"Failed to get access token: HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise ValueError(f"Failed to get access token: {e}") from e



