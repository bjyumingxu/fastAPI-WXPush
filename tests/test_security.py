"""测试安全模块."""

import time

import pytest

from wxpush.core.security import (
    generate_signature,
    validate_api_key_with_signature,
    verify_api_key,
    verify_signature,
    verify_timestamp,
)


class TestVerifyAPIKey:
    """测试 API Key 验证."""

    def test_verify_valid_api_key(self, test_api_key: str):
        """测试验证有效的 API Key."""
        assert verify_api_key(test_api_key) is True

    def test_verify_invalid_api_key(self):
        """测试验证无效的 API Key."""
        assert verify_api_key("invalid_api_key") is False

    def test_verify_empty_api_key(self):
        """测试验证空的 API Key."""
        assert verify_api_key("") is False


class TestVerifyTimestamp:
    """测试时间戳验证."""

    def test_verify_valid_timestamp(self):
        """测试验证有效的时间戳."""
        current_timestamp = int(time.time())
        assert verify_timestamp(current_timestamp) is True

    def test_verify_expired_timestamp(self):
        """测试验证过期的时间戳."""
        expired_timestamp = int(time.time()) - 400  # 400 秒前（超过 5 分钟窗口）
        assert verify_timestamp(expired_timestamp) is False

    def test_verify_future_timestamp(self):
        """测试验证未来的时间戳."""
        future_timestamp = int(time.time()) + 400  # 400 秒后（超过 5 分钟窗口）
        assert verify_timestamp(future_timestamp) is False


class TestSignature:
    """测试签名生成和验证."""

    def test_generate_signature(self, monkeypatch: pytest.MonkeyPatch):
        """测试生成签名."""
        monkeypatch.setenv("API_KEY_SECRET", "test_secret")
        
        api_key = "test_api_key"
        timestamp = int(time.time())
        payload = "test_payload"
        
        signature = generate_signature(api_key, timestamp, payload, secret="test_secret")
        
        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 十六进制长度

    def test_verify_valid_signature(self, monkeypatch: pytest.MonkeyPatch):
        """测试验证有效签名."""
        monkeypatch.setenv("API_KEY_SECRET", "test_secret")
        
        api_key = "test_api_key"
        timestamp = int(time.time())
        payload = "test_payload"
        secret = "test_secret"
        
        signature = generate_signature(api_key, timestamp, payload, secret=secret)
        assert verify_signature(api_key, timestamp, payload, signature, secret=secret) is True

    def test_verify_invalid_signature(self, monkeypatch: pytest.MonkeyPatch):
        """测试验证无效签名."""
        monkeypatch.setenv("API_KEY_SECRET", "test_secret")
        
        api_key = "test_api_key"
        timestamp = int(time.time())
        payload = "test_payload"
        invalid_signature = "invalid_signature"
        secret = "test_secret"
        
        assert verify_signature(api_key, timestamp, payload, invalid_signature, secret=secret) is False


class TestValidateAPIKeyWithSignature:
    """测试 API Key 和签名的统一验证."""

    def test_validate_with_valid_api_key_only(self, test_api_key: str):
        """测试仅使用有效的 API Key 验证（不使用签名）."""
        is_valid, message = validate_api_key_with_signature(
            api_key=test_api_key,
            timestamp=None,
            payload="",
            signature=None,
        )
        assert is_valid is True
        assert message == "验证成功"

    def test_validate_with_invalid_api_key(self):
        """测试使用无效的 API Key."""
        is_valid, message = validate_api_key_with_signature(
            api_key="invalid_api_key",
            timestamp=None,
            payload="",
            signature=None,
        )
        assert is_valid is False
        assert "无效" in message

    def test_validate_with_signature_but_no_timestamp(self, test_api_key: str):
        """测试使用签名但未提供时间戳."""
        is_valid, message = validate_api_key_with_signature(
            api_key=test_api_key,
            timestamp=None,
            payload="test_payload",
            signature="test_signature",
        )
        assert is_valid is False
        assert "时间戳" in message



