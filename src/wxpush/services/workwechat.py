"""企业微信服务."""

import logging
from typing import Any

from wxpush.core.config import settings
from wxpush.utils.http_client import (
    fetch_json,
    get_access_token,
    post_json,
)

logger = logging.getLogger(__name__)

# 企业微信 API 地址
WORKWECHAT_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
WORKWECHAT_MESSAGE_SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"


class WorkWeChatService:
    """企业微信服务类."""

    async def get_access_token(
        self, corpid: str, corpsecret: str
    ) -> tuple[str, int]:
        """获取企业微信 Access Token.

        Args:
            corpid: 企业 ID
            corpsecret: 应用 Secret

        Returns:
            (access_token, expires_in) 元组

        Raises:
            ValueError: 如果获取 token 失败
        """
        try:
            # 企业微信获取 token 使用 corpid 和 corpsecret 参数
            params = {
                "corpid": corpid,
                "corpsecret": corpsecret,
            }
            response_data = await fetch_json(WORKWECHAT_TOKEN_URL, params=params)

            # 检查是否有错误
            if "errcode" in response_data:
                errcode = response_data.get("errcode", 0)
                errmsg = response_data.get("errmsg", "Unknown error")
                if errcode != 0:
                    raise ValueError(
                        f"企业微信 API 错误: errcode={errcode}, errmsg={errmsg}"
                    )

            # 提取 access_token 和 expires_in
            access_token = response_data.get("access_token")
            expires_in = response_data.get("expires_in", 7200)  # 默认 7200 秒

            if not access_token:
                raise ValueError("Access token not found in response")

            logger.debug(f"成功获取企业微信 Access Token, expires_in: {expires_in}")
            return access_token, expires_in

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取企业微信 Access Token 失败: {e}")
            raise ValueError(f"获取企业微信 Access Token 失败: {e}") from e

    async def _send_text_message(
        self,
        access_token: str,
        userid: str,
        agentid: str,
        title: str,
        content: str,
    ) -> dict[str, Any]:
        """发送企业微信文本消息（内部方法）.

        Args:
            access_token: 企业微信 Access Token
            userid: 接收成员的 UserID
            agentid: 应用 AgentID
            title: 消息标题
            content: 消息内容

        Returns:
            企业微信 API 响应数据，包含 msgid 或错误信息

        Raises:
            ValueError: 如果发送失败
        """
        # 企业微信文本消息格式
        # 将 title 和 content 组合成完整的消息内容
        message_text = f"{title}\n\n{content}"

        # 构建请求体
        # agentid 必须是整数
        try:
            agentid_int = int(agentid)
        except (ValueError, TypeError):
            raise ValueError(f"agentid 必须是有效的整数，当前值: {agentid}")

        request_body = {
            "touser": userid,
            "msgtype": "text",
            "agentid": agentid_int,
            "text": {
                "content": message_text,
            },
            "safe": 0,  # 表示是否是保密消息，0 表示否
        }

        try:
            # 调用企业微信消息发送接口
            response_data = await post_json(
                f"{WORKWECHAT_MESSAGE_SEND_URL}?access_token={access_token}",
                json=request_body,
            )

            # 检查企业微信 API 返回的错误
            if "errcode" in response_data:
                errcode = response_data.get("errcode", 0)
                errmsg = response_data.get("errmsg", "Unknown error")
                if errcode != 0:
                    error_msg = f"企业微信 API 错误: errcode={errcode}, errmsg={errmsg}"
                    # 提取 hint 和 from_ip（如果存在）
                    hint = response_data.get("hint", "")
                    from_ip = None
                    if "from ip:" in errmsg.lower():
                        try:
                            from_ip = errmsg.split("from ip:")[-1].split(",")[0].strip()
                        except Exception:
                            pass
                    
                    # 针对常见错误提供更友好的提示
                    if errcode == 60020:
                        ip_info = f" IP: {from_ip}" if from_ip else ""
                        error_msg += (
                            f"\n\n💡 解决方案：此错误表示 IP 地址未在白名单中。"
                            f"请在企业微信管理后台 -> 应用管理 -> [您的应用] -> 企业可信 IP 中添加{ip_info}"
                            f"\n详细配置步骤请参考：企业微信IP白名单配置指南.md"
                        )
                    
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"成功发送企业微信消息, msgid: {response_data.get('msgid')}"
            )
            return response_data

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"发送企业微信消息失败: {e}")
            raise ValueError(f"发送企业微信消息失败: {e}") from e

    async def send_message(
        self,
        appid: str,
        secret: str,
        userid: str,
        title: str,
        content: str,
        base_url: str | None = None,
        agentid: str | None = None,
    ) -> dict[str, Any]:
        """发送消息的统一接口.

        Args:
            appid: 企业 ID（Corpid）
            secret: 应用 Secret（Corpsecret）
            userid: 成员 UserID
            title: 消息标题
            content: 消息内容
            base_url: 跳转链接（可选，企业微信文本消息不支持跳转链接）
            agentid: 应用 AgentID（可选，如果未提供则使用配置的默认值）

        Returns:
            包含 errcode, errmsg, msgid 的字典

        Raises:
            ValueError: 如果发送失败
        """
        # 如果没有提供 agentid，尝试从配置获取
        if not agentid:
            agentid = settings.default_workwechat_agentid

        # 企业微信必须提供 agentid
        if not agentid:
            error_msg = (
                "agentid 是必需的。"
                "请在请求中提供 agentid 参数，或在配置中设置 default_workwechat_agentid"
            )
            logger.error(error_msg)
            # 返回错误响应而不是抛出异常，保持统一的响应格式
            return {
                "errcode": 40000,
                "errmsg": error_msg,
                "msgid": None,
            }
        
        # 验证 agentid 是否为有效整数
        try:
            agentid_int = int(agentid)
        except (ValueError, TypeError) as e:
            error_msg = f"agentid 必须是有效的整数，当前值: {agentid}，类型: {type(agentid).__name__}"
            logger.error(error_msg)
            # 返回错误响应而不是抛出异常
            return {
                "errcode": 40000,
                "errmsg": error_msg,
                "msgid": None,
            }

        # agentid 验证通过，继续执行
        try:
            # 步骤1：获取 Access Token
            corpid_preview = appid[:10] + "..." if len(appid) > 10 else appid
            logger.debug(
                f"开始获取企业微信 Access Token, corpid: {corpid_preview}"
            )
            access_token, _ = await self.get_access_token(appid, secret)

            # 步骤2：发送消息
            userid_preview = userid[:10] + "..." if len(userid) > 10 else userid
            logger.debug(
                f"开始发送企业微信消息, userid: {userid_preview}, agentid: {agentid_int}"
            )
            response_data = await self._send_text_message(
                access_token=access_token,
                userid=userid,
                agentid=str(agentid_int),  # 使用已验证的 agentid_int
                title=title,
                content=content,
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
            # 尝试解析错误码（企业微信 API 返回的）
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
            logger.error(f"发送企业微信消息时发生未知错误: {e}")
            return {
                "errcode": 50000,
                "errmsg": f"发送消息失败: {str(e)}",
                "msgid": None,
            }
