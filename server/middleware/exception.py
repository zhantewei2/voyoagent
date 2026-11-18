"""统一异常处理：业务异常转 resp_result，未预期异常转 500。"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from voyo.utils import Methods, YoHttpException

logger = logging.getLogger(__name__)


class YoExceptionMiddleware(BaseHTTPMiddleware):
    #捕获 service/controller 抛出的 YoHttpException，统一按 resp_result 返回

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except YoHttpException as e:
            logger.warning("业务异常 %s %s: %s", request.method, request.url.path, e.msg)
            return Methods.resp_result(e.msg, code=e.code)
        except Exception:
            logger.exception("未处理异常 %s %s", request.method, request.url.path)
            return Methods.resp_result("服务器内部错误", code=500)
