"""测试微信公众平台服务."""

import pytest
import pytest_httpx
from pytest_httpx import HTTPXMock

from wxpush.services.wechat import WeChatService, WECHAT_TOKEN_URL, WECHAT_TEMPLATE_SEND_URL


class TestWeChatServiceGetAccessToken:
    """测试获取 Access Token."""

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, httpx_mock: HTTPXMock):
        """测试成功获取 Access Token."""
        # Mock 微信 API 响应
        mock_response = {
            "access_token": "test_access_token_12345",
            "expires_in": 7200,
        }
        httpx_mock.add_response(
            method="GET",
            url=f"{WECHAT_TOKEN_URL}?grant_type=client_credential&appid=test_appid&secret=test_secret",
            json=mock_response,
        )

        service = WeChatService()
        access_token, expires_in = await service.get_access_token(
            appid="test_appid", secret="test_secret"
        )

        assert access_token == "test_access_token_12345"
        assert expires_in == 7200

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, httpx_mock: HTTPXMock):
        """测试获取 Access Token 失败."""
        # Mock 微信 API 错误响应
        mock_error_response = {
            "errcode": 40013,
            "errmsg": "invalid appid",
        }
        httpx_mock.add_response(
            method="GET",
            url=WECHAT_TOKEN_URL,
            json=mock_error_response,
            status_code=200,  # 微信 API 即使错误也返回 200
        )

        service = WeChatService()
        with pytest.raises(ValueError, match="invalid appid"):
            await service.get_access_token(appid="invalid_appid", secret="test_secret")


class TestWeChatServiceSendTemplateMessage:
    """测试发送模板消息."""

    @pytest.mark.asyncio
    async def test_send_template_message_success(
        self, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ):
        """测试成功发送模板消息."""
        # 设置默认 template_id
        monkeypatch.setenv("DEFAULT_WECHAT_TEMPLATE_ID", "test_template_id")

        # Mock Access Token 请求
        httpx_mock.add_response(
            method="GET",
            url=WECHAT_TOKEN_URL,
            json={"access_token": "test_token", "expires_in": 7200},
        )

        # Mock 模板消息发送响应
        mock_send_response = {
            "errcode": 0,
            "errmsg": "ok",
            "msgid": 123456789,
        }
        httpx_mock.add_response(
            method="POST",
            url=f"{WECHAT_TEMPLATE_SEND_URL}?access_token=test_token",
            json=mock_send_response,
        )

        service = WeChatService()
        result = await service.send_message(
            appid="test_appid",
            secret="test_secret",
            userid="test_openid",
            title="测试标题",
            content="测试内容",
            template_id="test_template_id",
        )

        assert result["errcode"] == 0
        assert result["errmsg"] == "ok"
        assert result["msgid"] == 123456789

    @pytest.mark.asyncio
    async def test_send_template_message_failure(self, httpx_mock: HTTPXMock):
        """测试发送模板消息失败."""
        # Mock Access Token 请求
        httpx_mock.add_response(
            method="GET",
            url=WECHAT_TOKEN_URL,
            json={"access_token": "test_token", "expires_in": 7200},
        )

        # Mock 模板消息发送错误响应
        mock_error_response = {
            "errcode": 40001,
            "errmsg": "invalid credential",
        }
        httpx_mock.add_response(
            method="POST",
            url=WECHAT_TEMPLATE_SEND_URL,
            json=mock_error_response,
        )

        service = WeChatService()
        result = await service.send_message(
            appid="test_appid",
            secret="test_secret",
            userid="test_openid",
            title="测试标题",
            content="测试内容",
            template_id="test_template_id",
        )

        assert result["errcode"] == 40001
        assert "invalid credential" in result["errmsg"]

    @pytest.mark.asyncio
    async def test_send_template_message_missing_template_id(
        self, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ):
        """测试未提供 template_id 时的错误处理."""
        # 不设置默认 template_id
        monkeypatch.delenv("DEFAULT_WECHAT_TEMPLATE_ID", raising=False)

        service = WeChatService()
        result = await service.send_message(
            appid="test_appid",
            secret="test_secret",
            userid="test_openid",
            title="测试标题",
            content="测试内容",
            template_id=None,
        )

        assert result["errcode"] != 0
        assert "template_id" in result["errmsg"].lower()

