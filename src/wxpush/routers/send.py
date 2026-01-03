"""发送消息路由."""

import logging
from urllib.parse import urlencode

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status

from wxpush.core.dependencies import (
    ERRCODE_INVALID_API_KEY,
    verify_api_key_dependency,
    verify_api_key_from_body,
)
from wxpush.schemas.send import (
    ERRCODE_INVALID_SIGNATURE,
    ERRCODE_TIMESTAMP_EXPIRED,
    ErrorResponse,
    SendRequest,
    SendResponse,
)
from wxpush.services.wechat import WeChatService
from wxpush.services.workwechat import WorkWeChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/send", tags=["发送消息"])


def parse_send_request_from_query(
    request: Request,
    api_key: Annotated[str, Depends(verify_api_key_dependency)],
    title: str = Query(..., description="消息标题"),
    content: str = Query(..., description="消息具体内容"),
    appid: str = Query(..., description="微信 AppID"),
    secret: str = Query(..., description="微信 AppSecret"),
    userid: str = Query(..., description="接收用户的 OpenID"),
    base_url: str | None = Query(None, description="消息详情跳转 URL"),
    template_id: str | None = Query(None, description="模板消息 ID（可选，微信公众平台需要）"),
    agentid: str | None = Query(None, description="应用 AgentID（可选，企业微信需要）"),
    channel: str = Query("wechat", description="推送渠道：wechat 或 workwechat"),
    timestamp: int | None = Query(None, description="时间戳（签名验证时必填）"),
    signature: str | None = Query(None, description="签名（可选）"),
) -> SendRequest:
    """从查询参数构造 SendRequest 对象.

    Args:
        request: FastAPI 请求对象
        api_key: 已验证的 API Key
        title: 消息标题
        content: 消息内容
        appid: 微信 AppID
        secret: 微信 AppSecret
        userid: 接收用户 OpenID
        base_url: 跳转 URL
        channel: 推送渠道
        timestamp: 时间戳
        signature: 签名

    Returns:
        SendRequest 对象
    """
    # 验证 channel 参数
    if channel not in ("wechat", "workwechat"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "errcode": 40000,
                "errmsg": f"无效的 channel 参数: {channel}，必须是 'wechat' 或 'workwechat'",
            },
        )

    return SendRequest(
        api_key=api_key,
        title=title,
        content=content,
        appid=appid,
        secret=secret,
        userid=userid,
        base_url=base_url,
        template_id=template_id,
        agentid=agentid,
        channel=channel,  # type: ignore[arg-type]
        timestamp=timestamp,
        signature=signature,
    )


def generate_detail_url(request: Request, title: str, content: str) -> str:
    """生成消息详情页 URL.

    Args:
        request: FastAPI 请求对象
        title: 消息标题
        content: 消息内容

    Returns:
        消息详情页的完整 URL
    """
    # 获取请求的基础 URL（scheme + host + port）
    url = request.url
    base_url = f"{url.scheme}://{url.netloc}"

    # 构建详情页路径和查询参数
    query_params = {
        "title": title,
        "content": content,
    }
    detail_path = "/detail"
    detail_url = f"{base_url}{detail_path}?{urlencode(query_params)}"

    return detail_url


async def send_message_handler(
    request: Request, send_request: SendRequest
) -> SendResponse:
    """处理消息发送的业务逻辑.

    Args:
        request: FastAPI 请求对象（用于生成详情页 URL）
        send_request: 发送请求模型

    Returns:
        发送响应模型

    Raises:
        HTTPException: 如果发送失败
    """
    logger.info(
        "收到发送消息请求",
        extra={
            "channel": send_request.channel,
            "title": send_request.title[:50],  # 只记录标题前50字符
            "userid": send_request.userid[:10] + "...",  # 部分用户ID
            # 不记录 secret 和 api_key
        },
    )

    # 如果没有提供 base_url，自动生成指向详情页的 URL
    base_url = send_request.base_url
    if not base_url:
        base_url = generate_detail_url(
            request=request,
            title=send_request.title,
            content=send_request.content,
        )
        logger.debug(f"自动生成详情页 URL: {base_url[:100]}...")

    try:
        # 根据 channel 选择服务
        if send_request.channel == "workwechat":
            service = WorkWeChatService()
            # 企业微信服务
            result = await service.send_message(
                appid=send_request.appid,
                secret=send_request.secret,
                userid=send_request.userid,
                title=send_request.title,
                content=send_request.content,
                base_url=base_url,  # 使用处理后的 base_url
                agentid=send_request.agentid,
            )
        else:
            # 微信公众平台服务
            service = WeChatService()
            result = await service.send_message(
                appid=send_request.appid,
                secret=send_request.secret,
                userid=send_request.userid,
                title=send_request.title,
                content=send_request.content,
                base_url=base_url,  # 使用处理后的 base_url
                template_id=send_request.template_id,
            )

        # 检查是否有错误
        if result.get("errcode", 0) != 0:
            errcode = result.get("errcode", 50000)
            errmsg = result.get("errmsg", "Unknown error")
            logger.error(f"消息发送失败: errcode={errcode}, errmsg={errmsg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "errcode": errcode,
                    "errmsg": errmsg,
                },
            )

        # 返回成功响应
        return SendResponse(
            errcode=result.get("errcode", 0),
            errmsg=result.get("errmsg", "ok"),
            msgid=result.get("msgid"),
        )

    except HTTPException:
        # 重新抛出 HTTPException
        raise
    except Exception as e:
        logger.error(f"发送消息时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "errcode": 50000,
                "errmsg": f"服务器内部错误: {str(e)}",
            },
        )


@router.get(
    "",
    response_model=SendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "API Key 验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
    summary="发送消息（GET）",
    description="通过 GET 请求发送消息到指定微信用户",
)
async def send_message_get(
    request: Request,
    send_request: Annotated[SendRequest, Depends(parse_send_request_from_query)],
) -> SendResponse:
    """发送消息接口（GET 方法）.

    Args:
        request: FastAPI 请求对象
        send_request: 发送请求模型（从查询参数解析）

    Returns:
        发送响应模型
    """
    return await send_message_handler(request, send_request)


@router.post(
    "",
    response_model=SendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "API Key 验证失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
    summary="发送消息（POST）",
    description="通过 POST 请求发送消息到指定微信用户",
)
async def send_message_post(
    request: Request,
    send_request: SendRequest = Body(..., description="发送消息请求"),
) -> SendResponse:
    """发送消息接口（POST 方法）.

    Args:
        request: FastAPI 请求对象
        send_request: 发送请求模型（从请求体 JSON 解析）

    Returns:
        发送响应模型
    """
    # 验证 API Key
    await verify_api_key_from_body(send_request)
    
    return await send_message_handler(request, send_request)

