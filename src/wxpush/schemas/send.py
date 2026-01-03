"""发送消息的数据模型."""

from typing import Literal

from pydantic import BaseModel, Field


# 错误码常量
ERRCODE_INVALID_API_KEY = 40001
ERRCODE_INVALID_SIGNATURE = 40002
ERRCODE_TIMESTAMP_EXPIRED = 40003


class SendRequest(BaseModel):
    """发送消息请求模型."""

    api_key: str = Field(..., description="项目识别码（必填）")
    title: str = Field(..., min_length=1, max_length=200, description="消息标题（必填）")
    content: str = Field(..., min_length=1, max_length=5000, description="消息具体内容（必填）")
    appid: str = Field(..., min_length=1, description="微信 AppID（必填）")
    secret: str = Field(..., min_length=1, description="微信 AppSecret（必填）")
    userid: str = Field(..., min_length=1, description="接收用户的 OpenID（必填）")
    base_url: str | None = Field(
        default=None,
        max_length=500,
        description="消息详情跳转 URL（可选，默认使用服务默认页面）",
    )
    template_id: str | None = Field(
        default=None,
        description="模板消息 ID（可选，微信公众平台需要，如果不提供将使用配置的默认值）",
    )
    agentid: str | None = Field(
        default=None,
        description="应用 AgentID（可选，企业微信需要，如果不提供将使用配置的默认值）",
    )
    channel: Literal["wechat", "workwechat"] = Field(
        default="wechat",
        description="推送渠道：wechat（微信公众平台）或 workwechat（企业微信），默认 wechat",
    )
    timestamp: int | None = Field(
        default=None,
        description="时间戳（Unix 时间戳，秒），用于签名验证时必填",
    )
    signature: str | None = Field(
        default=None,
        description="HMAC-SHA256 签名（可选，启用签名验证时需要）",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "api_key": "your_api_key",
                "title": "服务器通知",
                "content": "服务已重启",
                "appid": "wx_appid",
                "secret": "wx_secret",
                "userid": "user_openid",
                "base_url": "https://example.com",
                "channel": "wechat",
            }
        }
    }


class SendResponse(BaseModel):
    """发送消息成功响应模型."""

    errcode: int = Field(default=0, description="错误码，0 表示成功")
    errmsg: str = Field(default="ok", description="错误信息")
    msgid: str | None = Field(default=None, description="消息 ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "errcode": 0,
                "errmsg": "ok",
                "msgid": "msg_123456",
            }
        }
    }


class ErrorResponse(BaseModel):
    """错误响应模型."""

    errcode: int = Field(..., description="错误码")
    errmsg: str = Field(..., description="错误描述")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "errcode": 40001,
                    "errmsg": "项目识别码无效",
                },
                {
                    "errcode": 40002,
                    "errmsg": "识别码签名验证失败",
                },
                {
                    "errcode": 40003,
                    "errmsg": "请求时间戳过期",
                },
            ]
        }
    }

