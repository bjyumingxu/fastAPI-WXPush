"""安全模块：API Key 验证和签名逻辑."""

import hmac
import time
from hashlib import sha256

from wxpush.core.config import settings

# 时间戳有效期（秒）- 5分钟
TIMESTAMP_VALIDITY_WINDOW = 300


def verify_api_key(api_key: str) -> bool:
    """验证 API Key 是否在有效列表中.

    Args:
        api_key: 待验证的 API Key

    Returns:
        True 如果 API Key 有效，False 否则
    """
    if not api_key:
        return False

    # 使用 api_keys_list 属性，确保从配置文件加载
    api_keys = settings.api_keys_list
    if not api_keys:
        # 如果没有配置 API Keys，拒绝所有请求
        return False

    return api_key in api_keys


def generate_signature(
    api_key: str, timestamp: int, payload: str, secret: str | None = None
) -> str:
    """生成 HMAC-SHA256 签名.

    Args:
        api_key: 项目识别码
        timestamp: 时间戳（Unix 时间戳，秒）
        payload: 请求载荷（通常是 JSON 字符串或关键参数的组合）
        secret: 签名密钥（如果为 None，使用配置中的密钥）

    Returns:
        HMAC-SHA256 签名的十六进制字符串
    """
    if secret is None:
        secret = settings.api_key_secret or ""

    if not secret:
        raise ValueError("Signature secret is required for generating signature")

    # 构造签名字符串：api_key + timestamp + payload
    message = f"{api_key}{timestamp}{payload}"

    # 生成 HMAC-SHA256 签名
    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        sha256,
    ).hexdigest()

    return signature


def verify_signature(
    api_key: str,
    timestamp: int,
    payload: str,
    signature: str,
    secret: str | None = None,
) -> bool:
    """验证 HMAC-SHA256 签名.

    Args:
        api_key: 项目识别码
        timestamp: 时间戳（Unix 时间戳，秒）
        payload: 请求载荷
        signature: 待验证的签名
        secret: 签名密钥（如果为 None，使用配置中的密钥）

    Returns:
        True 如果签名有效，False 否则
    """
    try:
        expected_signature = generate_signature(api_key, timestamp, payload, secret)
        # 使用安全的比较方法防止时间攻击
        return hmac.compare_digest(expected_signature, signature)
    except (ValueError, TypeError):
        return False


def verify_timestamp(timestamp: int, validity_window: int = TIMESTAMP_VALIDITY_WINDOW) -> bool:
    """验证时间戳是否在有效窗口内.

    Args:
        timestamp: 待验证的时间戳（Unix 时间戳，秒）
        validity_window: 有效时间窗口（秒），默认 5 分钟

    Returns:
        True 如果时间戳在有效窗口内，False 否则
    """
    current_time = int(time.time())
    time_diff = abs(current_time - timestamp)

    return time_diff <= validity_window


def validate_api_key_with_signature(
    api_key: str,
    timestamp: int | None = None,
    payload: str = "",
    signature: str | None = None,
) -> tuple[bool, str]:
    """验证 API Key 和签名（如果提供）.

    Args:
        api_key: 项目识别码
        timestamp: 时间戳（可选）
        payload: 请求载荷（可选）
        signature: 签名（可选）

    Returns:
        (是否有效, 错误消息) 元组
    """
    # 首先验证 API Key
    if not verify_api_key(api_key):
        return False, "项目识别码无效"

    # 如果提供了签名，验证签名
    if signature:
        if timestamp is None:
            return False, "使用签名验证时，时间戳参数必填"

        # 验证时间戳
        if not verify_timestamp(timestamp):
            return False, "请求时间戳过期"

        # 验证签名
        if not verify_signature(api_key, timestamp, payload, signature):
            return False, "识别码签名验证失败"

    # 如果未启用签名模式，只需要验证 API Key
    return True, "验证成功"

