"""集成测试 - 端到端测试."""

import pytest
import pytest_httpx
from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from wxpush.services.wechat import WECHAT_TOKEN_URL, WECHAT_TEMPLATE_SEND_URL
from wxpush.services.workwechat import WORKWECHAT_TOKEN_URL, WORKWECHAT_MESSAGE_SEND_URL


class TestHealthCheck:
    """测试健康检查接口."""

    def test_health_check(self, test_client: TestClient):
        """测试健康检查接口."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"


class TestMessageDetail:
    """测试消息详情页."""

    def test_message_detail_page(self, test_client: TestClient):
        """测试消息详情页面."""
        response = test_client.get(
            "/detail",
            params={
                "title": "测试标题",
                "content": "测试内容",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "测试标题" in response.text
        assert "测试内容" in response.text

    def test_message_detail_with_time(self, test_client: TestClient):
        """测试带时间戳的消息详情页."""
        response = test_client.get(
            "/detail",
            params={
                "title": "测试标题",
                "content": "测试内容",
                "time": "2024-01-01 12:00:00",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "2024-01-01 12:00:00" in response.text


class TestSendMessageIntegration:
    """测试发送消息的完整流程."""

    def test_send_wechat_message_integration(
        self,
        test_client: TestClient,
        httpx_mock: HTTPXMock,
        test_api_key: str,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """测试微信公众平台消息发送的完整流程."""
        # 设置默认 template_id
        monkeypatch.setenv("DEFAULT_WECHAT_TEMPLATE_ID", "test_template_id")

        # Mock 微信 API
        # Mock 微信 API（使用更灵活的 URL 匹配）
        httpx_mock.add_response(
            method="GET",
            url=WECHAT_TOKEN_URL,
            json={"access_token": "test_token", "expires_in": 7200},
        )
        httpx_mock.add_response(
            method="POST",
            url=WECHAT_TEMPLATE_SEND_URL,
            json={"errcode": 0, "errmsg": "ok", "msgid": 123456789},
        )

        # 发送 GET 请求
        response = test_client.get(
            "/send/",
            params={
                "api_key": test_api_key,
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_openid",
                "channel": "wechat",
                "template_id": "test_template_id",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["errcode"] == 0
        assert data["errmsg"] == "ok"
        assert data["msgid"] == 123456789

    def test_send_workwechat_message_integration(
        self,
        test_client: TestClient,
        httpx_mock: HTTPXMock,
        test_api_key: str,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """测试企业微信消息发送的完整流程."""
        # 设置默认 agentid
        monkeypatch.setenv("DEFAULT_WORKWECHAT_AGENTID", "1000001")

        # Mock 企业微信 API
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
        httpx_mock.add_response(
            method="POST",
            url=WORKWECHAT_MESSAGE_SEND_URL,
            json={"errcode": 0, "errmsg": "ok", "msgid": "test_msgid"},
        )

        # 发送 POST 请求
        response = test_client.post(
            "/send/",
            json={
                "api_key": test_api_key,
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_corpid",
                "secret": "test_secret",
                "userid": "test_userid",
                "channel": "workwechat",
                "agentid": "1000001",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["errcode"] == 0
        assert data["errmsg"] == "ok"
        assert data["msgid"] == "test_msgid"

