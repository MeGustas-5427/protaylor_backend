"""
自定义CSRF中间件 - 为API接口优化CSRF校验
"""
import logging
import re
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ApiCsrfExemptMiddleware(MiddlewareMixin):
    """
    API接口CSRF豁免中间件
    - API接口默认跳过CSRF检查
    - Admin或其他web页面保留CSRF防护
    """

    def __init__(self, get_response=None):
        # 调用父类初始化
        super().__init__(get_response)

        # 编译豁免URL正则表达式
        self.exempt_urls = []
        if hasattr(settings, 'CSRF_EXEMPT_URLS'):
            self.exempt_urls = [re.compile(url) for url in settings.CSRF_EXEMPT_URLS]

    def process_request(self, request):
        """检查请求是否应该豁免CSRF"""
        path = request.path_info.lstrip('/')

        # 匹配豁免URL
        for url_pattern in self.exempt_urls:
            if url_pattern.match(path):
                # 标记为豁免CSRF
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
        else:
            logger.info("CSRF保护启用: %s", path)

        return None


class SmartCsrfViewMiddleware(CsrfViewMiddleware):
    """
    智能CSRF中间件 - 结合原生Django CSRF中间件
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # 如果请求已被标记为豁免，跳过CSRF检查
        if getattr(request, '_dont_enforce_csrf_checks', False):
            return None
        # 否则执行正常的CSRF检查
        # 其他请求仍交给默认的CSRF校验
        return super().process_view(request, callback, callback_args, callback_kwargs)
