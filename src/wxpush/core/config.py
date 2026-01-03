"""应用配置模块 - 使用 Pydantic Settings 管理配置."""

import json
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置."""

    # 服务配置
    port: int = Field(default=5566, description="服务端口")
    log_level: str = Field(default="INFO", description="日志级别")
    default_tz: str = Field(default="Asia/Shanghai", description="默认时区")

    # API Key 配置
    # 注意：使用 None 作为默认值，这样 field_validator 会被调用
    api_keys: List[str] | None = Field(
        default=None, description="有效的项目识别码列表（从环境变量或配置文件加载）"
    )
    api_key_secret: str | None = Field(default=None, description="API Key 签名密钥")

    # 微信模板配置
    default_wechat_template_id: str | None = Field(
        default=None, description="默认的微信模板消息 ID（可选）"
    )
    # 企业微信配置
    default_workwechat_agentid: str | None = Field(
        default=None, description="默认的企业微信应用 AgentID（可选）"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | List[str] | None) -> List[str]:
        """解析 API Keys.

        支持从环境变量（逗号分隔字符串）或配置文件加载.
        优先级：环境变量 > 配置文件
        """
        # 如果环境变量提供了值（字符串），优先使用环境变量
        if isinstance(v, str):
            if v.strip():
                # 分割并清理
                return [key.strip() for key in v.split(",") if key.strip()]
            # 空字符串，尝试从配置文件加载
            return cls._load_api_keys_from_file()

        # 如果是列表，直接返回
        if isinstance(v, list):
            return v

        # 如果是 None 或未提供，尝试从配置文件加载
        if v is None:
            return cls._load_api_keys_from_file()

        return []

    @staticmethod
    def _load_api_keys_from_file() -> List[str]:
        """从配置文件加载 API Keys.

        Returns:
            API Keys 列表
        """
        api_keys_file = Path("api_keys.json")
        if api_keys_file.exists():
            try:
                with open(api_keys_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    keys = data.get("valid_keys", [])
                    if keys:
                        import logging
                        logging.info(f"从配置文件加载了 {len(keys)} 个 API Keys")
                    return keys
            except (json.JSONDecodeError, KeyError, OSError) as e:
                # 配置文件格式错误时，返回空列表并记录警告
                import logging

                logging.warning(f"从配置文件加载 API Keys 失败: {e}")
                return []
        return []

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return v_upper

    @property
    def api_keys_list(self) -> List[str]:
        """获取 API Keys 列表（处理 None 情况）."""
        if self.api_keys is None:
            return self._load_api_keys_from_file()
        return self.api_keys


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）."""
    return settings

