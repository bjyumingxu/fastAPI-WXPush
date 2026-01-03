"""测试企业微信服务."""

import pytest
import pytest_httpx
from pytest_httpx import HTTPXMock

from wxpush.services.workwechat import (
    WORKWECHAT_TOKEN_URL,
    WORKWECHAT_MESSAGE_SEND_URL,
    WorkWeChatService,
)


class TestWorkWeChatServiceGetAccessToken:
    """测试获取 Access Token."""

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, httpx_mock: HTTPXMock):
        """测试成功获取 Access Token."""
        # Mock 企业微信 API 响应
        mock_response = {
            "errcode": 0,
            "errmsg": "ok",
            "access_token": "test_access_token_12345",
            "expires_in": 7200,
        }
        httpx_mock.add_response(
            method="GET",
            url=f"{WORKWECHAT_TOKEN_URL}?corpid=test_corpid&corpsecret=test_secret",
            json=mock_response,
        )

        service = WorkWeChatService()
        access_token, expires_in = await service.get_access_token(
            corpid="test_corpid", corpsecret="test_secret"
        )

        assert access_token == "test_access_token_12345"
        assert expires_in == 7200

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, httpx_mock: HTTPXMock):
        """测试获取 Access Token 失败."""
        # Mock 企业微信 API 错误响应
        mock_error_response = {
            "errcode": 40013,
            "errmsg": "invalid corpid",
        }
        httpx_mock.add_response(
            method="GET",
            url=WORKWECHAT_TOKEN_URL,
            json=mock_error_response,
        )

        service = WorkWeChatService()
        with pytest.raises(ValueError, match="invalid corpid"):
            await service.get_access_token(
                corpid="invalid_corpid", corpsecret="test_secret"
            )


class TestWorkWeChatServiceSendMessage:
    """测试发送消息."""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ):
        """测试成功发送消息."""
        # 设置默认 agentid
        monkeypatch.setenv("DEFAULT_WORKWECHAT_AGENTID", "1000001")

        # Mock Access Token 请求
        httpx_mock.add_response(
            method="GET",
            url=WORKWECHAT_TOKEN_URL,
            json={
                "errcode": 0,
                "errmsg": "ok",
                "access_token": "test_token",
                "expires_in": 7200,
            },
        )

        # Mock 消息发送响应
        mock_send_response = {
            "errcode": 0,
            "errmsg": "ok",
            "msgid": "test_msgid_12345",
        }
        httpx_mock.add_response(
            method="POST",
            url=f"{WORKWECHAT_MESSAGE_SEND_URL}?access_token=test_token",
            json=mock_send_response,
        )

        service = WorkWeChatService()
        result = await service.send_message(
            appid="test_corpid",
            secret="test_secret",
            userid="test_userid",
            title="测试标题",
            content="测试内容",
            agentid="1000001",
        )

        assert result["errcode"] == 0
        assert result["errmsg"] == "ok"
        assert result["msgid"] == "test_msgid_12345"

    @pytest.mark.asyncio
    async def test_send_message_failure(self, httpx_mock: HTTPXMock):
        """测试发送消息失败."""
        # Mock Access Token 请求
        httpx_mock.add_response(
            method="GET",
            url=WORKWECHAT_TOKEN_URL,
            json={
                "errcode": 0,
                "errmsg": "ok",
                "access_token": "test_token",
                "expires_in": 7200,
            },
        )

        # Mock 消息发送错误响应
        mock_error_response = {
            "errcode": 40001,
            "errmsg": "invalid userid",
        }
        httpx_mock.add_response(
            method="POST",
            url=WORKWECHAT_MESSAGE_SEND_URL,
            json=mock_error_response,
        )

        service = WorkWeChatService()
        result = await service.send_message(
            appid="test_corpid",
            secret="test_secret",
            userid="invalid_userid",
            title="测试标题",
            content="测试内容",
            agentid="1000001",
        )

        assert result["errcode"] == 40001
        assert "invalid userid" in result["errmsg"]

    @pytest.mark.asyncio
    async def test_send_message_missing_agentid(
        self, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ):
        """测试未提供 agentid 时的错误处理."""
        # 不设置默认 agentid
        monkeypatch.delenv("DEFAULT_WORKWECHAT_AGENTID", raising=False)

        service = WorkWeChatService()
        result = await service.send_message(
            appid="test_corpid",
            secret="test_secret",
            userid="test_userid",
            title="测试标题",
            content="测试内容",
            agentid=None,
        )

        assert result["errcode"] != 0
        assert "agentid" in result["errmsg"].lower()

    @pytest.mark.asyncio
    async def test_send_message_invalid_agentid(self, httpx_mock: HTTPXMock):
        """测试无效的 agentid（非整数）."""
        service = WorkWeChatService()
        result = await service.send_message(
            appid="test_corpid",
            secret="test_secret",
            userid="test_userid",
            title="测试标题",
            content="测试内容",
            agentid="not_a_number",
        )

        assert result["errcode"] != 0
        assert "整数" in result["errmsg"] or "agentid" in result["errmsg"].lower()

