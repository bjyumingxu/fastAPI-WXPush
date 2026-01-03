"""日志配置模块."""

import logging
import sys
from typing import Any

from wxpush.core.config import settings


class SensitiveFilter(logging.Filter):
    """过滤敏感信息的日志过滤器."""

    SENSITIVE_KEYS = {
        "secret",
        "api_key",
        "apikey",
        "password",
        "token",
        "access_token",
        "authorization",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录中的敏感信息."""
        # 过滤消息中的敏感信息
        if hasattr(record, "msg") and isinstance(record.msg, dict):
            record.msg = self._sanitize_dict(record.msg.copy())
        elif hasattr(record, "args") and isinstance(record.args, tuple):
            # 处理格式化参数
            new_args = []
            for arg in record.args:
                if isinstance(arg, dict):
                    new_args.append(self._sanitize_dict(arg.copy()))
                elif isinstance(arg, str):
                    new_args.append(self._sanitize_str(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        return True

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """清理字典中的敏感信息."""
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str) and any(
                sensitive in value.lower() for sensitive in ["secret", "api_key", "token"]
            ):
                # 简单检查，避免显示敏感值
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_str(self, text: str) -> str:
        """清理字符串中的敏感信息."""
        # 简单的字符串清理，可以更复杂
        if len(text) > 100:  # 避免处理过长的字符串
            return text
        lower_text = text.lower()
        if any(sensitive in lower_text for sensitive in self.SENSITIVE_KEYS):
            return "***REDACTED***"
        return text


def setup_logging() -> None:
    """配置日志系统."""
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # 移除现有的处理器
    root_logger.handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))

    # 创建格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # 添加敏感信息过滤器
    sensitive_filter = SensitiveFilter()
    console_handler.addFilter(sensitive_filter)

    # 添加处理器
    root_logger.addHandler(console_handler)

    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)



