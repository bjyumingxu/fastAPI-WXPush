"""Pytest 配置和共享 fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from wxpush.core.config import settings
from wxpush.main import app
from wxpush.utils.http_client import init_http_client


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """创建 FastAPI 测试客户端."""
    # 初始化 HTTP 客户端（测试需要）
    init_http_client()
    yield TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_test_api_keys(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """为测试设置 API Keys.

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    # 设置测试用的 API Key
    test_api_keys = ["test_api_key_12345", "test_api_key_67890"]
    
    # 直接 patch settings 的 api_keys 属性
    # api_keys_list property 会自动使用 api_keys 的值
    original_api_keys = settings.api_keys
    monkeypatch.setattr(settings, "api_keys", test_api_keys)
    
    # 确保 security 和 dependencies 模块也使用相同的 settings
    # 它们已经在导入时引用了 settings，所以不需要额外 patch
    
    yield
    
    # 清理：恢复原始设置
    monkeypatch.setattr(settings, "api_keys", original_api_keys)


@pytest.fixture(scope="function")
def test_api_key() -> str:
    """返回测试用的 API Key."""
    return "test_api_key_12345"

