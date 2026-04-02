import re
import typing
import datetime
import random
import string
import uuid
import orjson
from bs4 import BeautifulSoup

from django.utils import timezone
from django.db.models import QuerySet
from django.core.paginator import Page
from django.db import models

from utils import restful
from constants.code import Code



async def alist(queryset: QuerySet) -> typing.List:
    """将QuerySet异步转换为列表，避免PostgreSQL游标冲突问题"""
    from asgiref.sync import sync_to_async
    return await sync_to_async(list)(queryset)


def remove_html_tags(text):
    return BeautifulSoup(text, "html.parser").get_text()


def get_uuid4():
    return str(uuid.uuid4()).replace("-", "")


def generate_invite_code():
    """生成8位邀请码，基于UUID4的前8位"""
    return str(uuid.uuid4()).replace("-", "")[:8].upper()


def get_order_no() -> str:
    """根据当前系统时间来生成订单号。时间精确到微秒"""
    return timezone.localtime().strftime("%Y%m%d%H%M%S%f")


def random_str(num: int) -> str:
    """生成随机字符串"""
    return "".join(random.sample(string.ascii_letters + string.digits, num))


def filter_dict(
    data: dict, namelist: typing.Iterable[str], notfound_error: bool = False
) -> dict:
    """
    从字典中摘取需要的部分

    如果 notfound_error 为真, 则在 namelist 中存在 data 中没有的 key 时, 会抛出一个 KeyError 异常
    """
    newdict = {}

    for name in namelist:
        try:
            newdict[name] = data[name]
        except KeyError as e:
            if notfound_error:
                raise e
    return newdict


def pagination(
    request, queryset: Page, page: int, count: int, orders_count: int, params=""
):
    """API接口分页参数"""
    _pagination = {
        "count": orders_count,
        "current_page": page,
        "page_size": count
    }
    url = request.build_absolute_uri().split("?")[0]
    if queryset.has_next():
        _pagination["next"] = f"{url}?p={page+1}&page_size={count}&{params}"
    else:
        _pagination["next"] = queryset.has_next()

    if queryset.has_previous():
        _pagination["previous"] = f"{url}?p={page-1}&page_size={count}&{params}"
    else:
        _pagination["previous"] = queryset.has_previous()

    return _pagination


def convert_timezone(dt: datetime.datetime) -> datetime.datetime:
    """
    将任何 datetime 转为当前 TIME_ZONE 的 aware 时间
    """
    # 添加None值检查，防止'NoneType' object has no attribute 'utcoffset'错误
    if dt is None:
        return timezone.now()  # 返回当前时间作为默认值
    
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=timezone.utc)  # 先假设入参是 UTC
    return timezone.localtime(dt)  # 转到 settings.TIME_ZONE


def parse_json_request(request):
    """解析JSON请求数据"""
    try:
        return orjson.loads(request.body), None
    except orjson.JSONDecodeError:
        return None, restful.bad_request(code=Code.json格式不正确, message=Code.message(Code.json格式不正确))
    except Exception as e:
        # 处理RawPostDataException或其他请求体访问异常
        from django.http.request import RawPostDataException
        if isinstance(e, RawPostDataException):
            return None, restful.bad_request(code=Code.json格式不正确, message="无法读取请求数据，请使用JSON格式")
        return None, restful.bad_request(code=Code.json格式不正确, message=Code.message(Code.json格式不正确))


def clean_template_string(field_value):
    """
    清理模板字符串中的变量标记

    将模板变量标记转换为安全格式:
    - {{ 替换为 $
    - }} 替换为空格
    - { 替换为 $  
    - } 替换为空格
    最后去除首尾空白

    Args:
        field_value: 需要清理的字符串值

    Returns:
        清理后的字符串，如果输入为空则返回原值
    """
    if field_value:
        # 先处理双大括号，再处理单大括号
        cleaned = str(field_value).replace("{{", "$").replace("}}", " ")
        cleaned = cleaned.replace("{", "$").replace("}", " ")
        return cleaned.strip()
    return field_value


def remove_div_and_content(text: str) -> str:
    """
    移除字符串中 <div ...> ... </div> 及其中的所有内容
    """
    # re.S 让 '.' 可以匹配换行符
    return re.sub(r'<div id="ai.*?>.*?</div>', "", text, flags=re.S)


def validate_uuid_format(uuid_str, param_name="UUID", error_message=None):
    """
    验证UUID格式
    
    Args:
        uuid_str: 需要验证的UUID字符串
        param_name: 参数名称，用于日志记录
        error_message: 自定义错误消息，默认为"资源不存在"
        
    Returns:
        tuple: (is_valid, error_response)
        - is_valid: bool, UUID格式是否有效
        - error_response: dict or None, 格式无效时的错误响应
    """
    if error_message is None:
        error_message = "资源不存在"
    
    try:
        uuid.UUID(uuid_str)
        return True, None
    except (ValueError, TypeError):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"{param_name}格式无效: {uuid_str}")
        return False, restful.notfound(message=error_message)


class StringUUIDField(models.UUIDField):
    """返回字符串格式的 UUID 字段"""

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str):
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(super().to_python(value))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

def orjson_dumps_str(obj, **kwargs) -> str:
    return orjson.dumps(obj, **kwargs).decode('utf-8')