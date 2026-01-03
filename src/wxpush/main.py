"""FastAPI 应用入口."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from wxpush.core.config import settings
from wxpush.core.logging_config import setup_logging
from wxpush.routers import send
from wxpush.utils.http_client import close_http_client, init_http_client

logger = logging.getLogger(__name__)

# 初始化 Jinja2 模板引擎
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# 配置日志
setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title="微信消息推送服务",
    description="提供简洁的 HTTP API 接口，支持微信公众平台和企业微信消息推送",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，记录请求和响应信息."""

    async def dispatch(
        self, request: StarletteRequest, call_next: Callable
    ) -> Response:
        """处理请求并记录日志.

        Args:
            request: Starlette 请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP 响应
        """
        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端 IP
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求信息
        logger.info(
            "收到请求",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "query_params": str(request.query_params) if request.query_params else None,
            },
        )

        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            logger.info(
                "请求处理完成",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                },
            )

            return response
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录异常信息
            logger.error(
                "请求处理失败",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": f"{process_time:.3f}s",
                },
                exc_info=True,
            )
            raise


# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: StarletteRequest, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证错误.

    Args:
        request: Starlette 请求对象
        exc: 验证异常

    Returns:
        JSON 错误响应
    """
    logger.warning(
        "请求参数验证失败",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "errcode": 42200,
            "errmsg": "请求参数验证失败",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: StarletteRequest, exc: Exception
) -> JSONResponse:
    """处理全局异常.

    Args:
        request: Starlette 请求对象
        exc: 异常对象

    Returns:
        JSON 错误响应
    """
    logger.error(
        "未处理的异常",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "errcode": 50000,
            "errmsg": "服务器内部错误",
        },
    )


# 注册路由
app.include_router(send.router)


@app.on_event("startup")
async def startup_event() -> None:
    """应用启动时的初始化."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("微信消息推送服务启动")
    logger.info(f"服务端口: {settings.port}")
    logger.info(f"日志级别: {settings.log_level}")

    # 初始化 HTTP 客户端
    init_http_client()
    logger.info("HTTP 客户端已初始化")

    api_keys = settings.api_keys_list
    if api_keys:
        logger.info(f"已加载 {len(api_keys)} 个有效的 API Keys")
    else:
        logger.warning("未配置有效的 API Keys，所有请求将被拒绝")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """应用关闭时的清理."""
    import logging

    logger = logging.getLogger(__name__)

    # 关闭 HTTP 客户端
    await close_http_client()
    logger.info("HTTP 客户端已关闭")

    logger.info("微信消息推送服务关闭")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查接口.

    Returns:
        服务状态信息
    """
    return {"status": "ok"}


@app.get("/detail", response_class=HTMLResponse)
async def message_detail(
    request: Request,
    title: str = Query(..., description="消息标题"),
    content: str = Query(..., description="消息内容"),
    time: str | None = Query(None, description="时间戳（可选）"),
) -> HTMLResponse:
    """消息详情页面.

    Args:
        request: FastAPI 请求对象
        title: 消息标题
        content: 消息内容
        time: 时间戳（可选，格式：YYYY-MM-DD HH:MM:SS）

    Returns:
        HTML 响应
    """
    # 格式化时间
    if time:
        display_time = time
    else:
        # 使用当前时间
        current_time = datetime.now()
        display_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # 渲染模板
    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "title": title,
            "content": content,
            "time": display_time,
            "current_time": display_time,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wxpush.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )

