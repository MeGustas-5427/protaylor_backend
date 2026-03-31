from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware


class ConditionalSessionMiddleware(SessionMiddleware):
    """条件性Session中间件 - 仅为Admin路径启用"""
    
    def __call__(self, request):
        # 只对admin路径处理session
        if request.path.startswith('/admin/'):
            return super().__call__(request)
        
        # 非admin路径直接跳过
        return self.get_response(request)


class ConditionalAuthMiddleware(AuthenticationMiddleware):
    """条件性认证中间件 - 仅为Admin路径启用"""
    
    def __call__(self, request):
        # 只对admin路径使用Django认证
        if request.path.startswith('/admin/'):
            return super().__call__(request)
        
        # 非admin路径直接跳过
        return self.get_response(request)


class ConditionalMessageMiddleware(MessageMiddleware):
    """条件性消息中间件 - 仅为Admin路径启用"""
    
    def __call__(self, request):
        # 只对admin路径处理消息
        if request.path.startswith('/admin/'):
            return super().__call__(request)
        
        # 非admin路径直接跳过
        return self.get_response(request)

