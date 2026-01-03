"""测试发送消息路由."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestSendMessageGET:
    """测试 GET 方式发送消息."""

    def test_send_get_missing_api_key(self, test_client: TestClient):
        """测试缺少 API Key 参数."""
        response = test_client.get(
            "/send/",
            params={
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_get_invalid_api_key(self, test_client: TestClient):
        """测试无效的 API Key."""
        response = test_client.get(
            "/send/",
            params={
                "api_key": "invalid_api_key",
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        # FastAPI HTTPException 会将 detail 包装在 detail 字段中
        assert data["detail"]["errcode"] == 40001  # ERRCODE_INVALID_API_KEY

    def test_send_get_missing_required_params(self, test_client: TestClient, test_api_key: str):
        """测试缺少必填参数."""
        response = test_client.get(
            "/send/",
            params={
                "api_key": test_api_key,
                "title": "测试标题",
                # 缺少 content, appid, secret, userid
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_get_invalid_channel(self, test_client: TestClient, test_api_key: str):
        """测试无效的 channel 参数."""
        response = test_client.get(
            "/send/",
            params={
                "api_key": test_api_key,
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
                "channel": "invalid_channel",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "invalid channel" in data["detail"]["errmsg"].lower() or "channel" in data["detail"]["errmsg"].lower()


class TestSendMessagePOST:
    """测试 POST 方式发送消息."""

    def test_send_post_missing_api_key(self, test_client: TestClient):
        """测试缺少 API Key."""
        response = test_client.post(
            "/send/",
            json={
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_post_invalid_api_key(self, test_client: TestClient):
        """测试无效的 API Key."""
        response = test_client.post(
            "/send/",
            json={
                "api_key": "invalid_api_key",
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        # FastAPI HTTPException 会将 detail 包装在 detail 字段中
        assert data["detail"]["errcode"] == 40001  # ERRCODE_INVALID_API_KEY

    def test_send_post_missing_required_fields(self, test_client: TestClient, test_api_key: str):
        """测试缺少必填字段."""
        response = test_client.post(
            "/send/",
            json={
                "api_key": test_api_key,
                "title": "测试标题",
                # 缺少 content, appid, secret, userid
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSendMessageChannel:
    """测试不同 channel 参数."""

    def test_send_wechat_channel(self, test_client: TestClient, test_api_key: str):
        """测试微信公众平台 channel."""
        # 这里不实际调用微信 API，所以会返回错误
        # 但可以验证参数解析和 channel 选择逻辑
        response = test_client.get(
            "/send/",
            params={
                "api_key": test_api_key,
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
                "channel": "wechat",
            },
        )
        # 由于没有 mock 微信 API，可能会返回 400 或 500
        # 但至少应该能到达服务调用阶段
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_send_workwechat_channel(self, test_client: TestClient, test_api_key: str):
        """测试企业微信 channel."""
        response = test_client.get(
            "/send/",
            params={
                "api_key": test_api_key,
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_corpid",
                "secret": "test_secret",
                "userid": "test_userid",
                "channel": "workwechat",
            },
        )
        # 由于没有 mock 企业微信 API，可能会返回 400 或 500
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

