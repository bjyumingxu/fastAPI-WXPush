"""微信公众平台服务."""

import logging
from typing import Any

from wxpush.core.config import settings
from wxpush.utils.http_client import (
    fetch_json,
    get_access_token,
    get_http_client,
    post_json,
)

logger = logging.getLogger(__name__)

# 微信公众平台 API 地址
WECHAT_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WECHAT_TEMPLATE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"


class WeChatService:
    """微信公众平台服务类."""

    async def get_access_token(
        self, appid: str, secret: str
    ) -> tuple[str, int]:
        """获取微信 Access Token.

        Args:
            appid: 微信 AppID
            secret: 微信 AppSecret

        Returns:
            (access_token, expires_in) 元组

        Raises:
            ValueError: 如果获取 token 失败
        """
        try:
            access_token, expires_in = await get_access_token(
                token_url=WECHAT_TOKEN_URL,
                appid=appid,
                secret=secret,
                grant_type="client_credential",
            )
            logger.debug(f"成功获取微信 Access Token, expires_in: {expires_in}")
            return access_token, expires_in
        except ValueError as e:
            logger.error(f"获取微信 Access Token 失败: {e}")
            raise

    async def send_template_message(
        self,
        access_token: str,
        userid: str,
        title: str,
        content: str,
        base_url: str | None = None,
        template_id: str | None = None,
    ) -> dict[str, Any]:
        """发送微信模板消息.

        Args:
            access_token: 微信 Access Token
            userid: 接收用户的 OpenID
            title: 消息标题
            content: 消息内容
            base_url: 跳转链接（可选）
            template_id: 模板ID（可选，如果不提供则使用通用模板格式）

        Returns:
            微信 API 响应数据，包含 msgid 或错误信息

        Raises:
            ValueError: 如果发送失败
        """
        # 如果没有提供 template_id，尝试从配置中获取默认值
        if not template_id:
            template_id = settings.default_wechat_template_id

        # 微信模板消息必须提供 template_id
        if not template_id:
            raise ValueError(
                "template_id 是必需的。"
                "请在请求中提供 template_id 参数，或在配置中设置 default_wechat_template_id"
            )

        # 构建模板数据
        # 注意：模板数据格式需要与在微信公众平台配置的模板格式一致
        # 这里使用通用的字段名，要求模板包含 title 和 content 字段
        template_data = {
            "title": {
                "value": title,
                "color": "#173177",  # 默认颜色
            },
            "content": {
                "value": content,
                "color": "#173177",
            },
        }

        # 构建请求体
        request_body = {
            "touser": userid,
            "template_id": template_id,
            "data": template_data,
        }

        # 如果提供了 base_url，添加到请求中
        if base_url:
            request_body["url"] = base_url

        try:
            # 调用微信模板消息接口
            response_data = await post_json(
                f"{WECHAT_TEMPLATE_SEND_URL}?access_token={access_token}",
                json=request_body,
            )

            # 检查微信 API 返回的错误
            if "errcode" in response_data:
                errcode = response_data.get("errcode", 0)
                errmsg = response_data.get("errmsg", "Unknown error")
                if errcode != 0:
                    error_msg = f"微信 API 错误: errcode={errcode}, errmsg={errmsg}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"成功发送微信模板消息, msgid: {response_data.get('msgid')}"
            )
            return response_data

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"发送微信模板消息失败: {e}")
            raise ValueError(f"发送微信模板消息失败: {e}") from e

    async def send_message(
        self,
        appid: str,
        secret: str,
        userid: str,
        title: str,
        content: str,
        base_url: str | None = None,
        template_id: str | None = None,
    ) -> dict[str, Any]:
        """发送消息的统一接口.

        Args:
            appid: 微信 AppID
            secret: 微信 AppSecret
            userid: 接收用户的 OpenID
            title: 消息标题
            content: 消息内容
            base_url: 跳转链接（可选）
            template_id: 模板ID（可选）

        Returns:
            包含 errcode, errmsg, msgid 的字典

        Raises:
            ValueError: 如果发送失败
        """
        try:
            # 步骤1：获取 Access Token
            logger.debug(f"开始获取微信 Access Token, appid: {appid[:10]}...")
            access_token, _ = await self.get_access_token(appid, secret)

            # 步骤2：发送模板消息
            logger.debug(f"开始发送微信模板消息, userid: {userid[:10]}...")
            response_data = await self.send_template_message(
                access_token=access_token,
                userid=userid,
                title=title,
                content=content,
                base_url=base_url,
                template_id=template_id,
            )

            # 构造标准响应格式
            result = {
                "errcode": 0,
                "errmsg": "ok",
                "msgid": response_data.get("msgid"),
            }

            return result

        except ValueError as e:
            # 构造错误响应
            error_msg = str(e)
            # 尝试解析错误码（微信 API 返回的）
            errcode = 50000  # 默认错误码
            if "errcode=" in error_msg:
                try:
                    errcode_str = error_msg.split("errcode=")[1].split(",")[0]
                    errcode = int(errcode_str)
                except (ValueError, IndexError):
                    pass

            return {
                "errcode": errcode,
                "errmsg": error_msg,
                "msgid": None,
            }
        except Exception as e:
            logger.error(f"发送微信消息时发生未知错误: {e}")
            return {
                "errcode": 50000,
                "errmsg": f"发送消息失败: {str(e)}",
                "msgid": None,
            }

