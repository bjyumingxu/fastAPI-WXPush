"""FastAPI 依赖注入模块：API Key 验证."""

import json
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Query, Request, status

from wxpush.core.config import settings
from wxpush.core.security import validate_api_key_with_signature

if TYPE_CHECKING:
    from wxpush.schemas.send import SendRequest

# API Key 错误码（与 schemas 保持一致）
ERRCODE_INVALID_API_KEY = 40001
ERRCODE_INVALID_SIGNATURE = 40002
ERRCODE_TIMESTAMP_EXPIRED = 40003


async def verify_api_key_dependency(
    request: Request,
    api_key: str = Query(..., description="项目识别码"),
    timestamp: int | None = Query(None, description="时间戳（签名验证时必填）"),
    signature: str | None = Query(None, description="签名（可选）"),
) -> str:
    """验证 API Key 的依赖函数（用于 GET 请求）.

    Args:
        request: FastAPI 请求对象
        api_key: 项目识别码
        timestamp: 时间戳（可选）
        signature: 签名（可选）

    Returns:
        验证通过的 API Key

    Raises:
        HTTPException: 如果 API Key 验证失败
    """
    # 构造 payload（使用查询参数）
    # 对于签名验证，payload 可以是关键参数的组合
    payload = ""
    if signature:
        # 构建用于签名的 payload（排除 signature 参数）
        query_params = dict(request.query_params)
        query_params.pop("signature", None)
        # 按字母顺序排序并构造字符串
        sorted_params = sorted(query_params.items())
        payload = "&".join(f"{k}={v}" for k, v in sorted_params)

    is_valid, error_msg = validate_api_key_with_signature(
        api_key=api_key,
        timestamp=timestamp,
        payload=payload,
        signature=signature,
    )

    if not is_valid:
        # 根据错误消息确定错误码
        if "签名验证失败" in error_msg:
            errcode = ERRCODE_INVALID_SIGNATURE
        elif "时间戳过期" in error_msg:
            errcode = ERRCODE_TIMESTAMP_EXPIRED
        else:
            errcode = ERRCODE_INVALID_API_KEY

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "errcode": errcode,
                "errmsg": error_msg,
            },
        )

    return api_key


async def verify_api_key_from_body(
    send_request: "SendRequest",
) -> "SendRequest":
    """从请求体中验证 API Key（用于 POST 请求）.

    Args:
        send_request: 发送请求模型（已通过 Pydantic 验证，从 Body 解析）

    Returns:
        验证通过的请求模型

    Raises:
        HTTPException: 如果 API Key 验证失败
    """
    # 构建用于签名验证的 payload
    # 注意：由于 FastAPI 已经解析了 body，我们无法再读取原始 body
    # 所以使用 SendRequest 对象的字段重新构造 payload
    payload = ""
    if send_request.signature:
        # 使用关键字段构造 payload（排除 signature）
        payload_dict = {
            "api_key": send_request.api_key,
            "title": send_request.title,
            "content": send_request.content,
            "appid": send_request.appid,
            "secret": send_request.secret,
            "userid": send_request.userid,
        }
        # 添加可选字段（如果存在）
        if send_request.base_url:
            payload_dict["base_url"] = send_request.base_url
        if send_request.template_id:
            payload_dict["template_id"] = send_request.template_id
        if send_request.channel:
            payload_dict["channel"] = send_request.channel
        if send_request.timestamp is not None:
            payload_dict["timestamp"] = send_request.timestamp
        
        payload = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False)

    is_valid, error_msg = validate_api_key_with_signature(
        api_key=send_request.api_key,
        timestamp=send_request.timestamp,
        payload=payload,
        signature=send_request.signature,
    )

    if not is_valid:
        # 根据错误消息确定错误码
        if "签名验证失败" in error_msg:
            errcode = ERRCODE_INVALID_SIGNATURE
        elif "时间戳过期" in error_msg:
            errcode = ERRCODE_TIMESTAMP_EXPIRED
        else:
            errcode = ERRCODE_INVALID_API_KEY

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "errcode": errcode,
                "errmsg": error_msg,
            },
        )

    return send_request

