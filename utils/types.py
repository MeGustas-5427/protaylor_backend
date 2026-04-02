from typing import Any, Dict, Union, Callable, TYPE_CHECKING

from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.contrib.auth.models import AnonymousUser

if TYPE_CHECKING:
    # 只在类型检查时导入，避免循环导入
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    # 运行时使用字符串引用
    from django.contrib.auth.models import AbstractUser
    User = AbstractUser

__all__ = ["Request"]


class Request(WSGIRequest):
    user: Union['User', AnonymousUser]
    DATA: Dict[str, Any]


HTTPHandler = Callable[..., HttpResponse]
