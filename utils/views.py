import typing

from django.forms import Form
from django import forms
from django.db import models
from django.db.models import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.views import View

from utils.functions import pagination

from .types import Request
from . import restful

class PaginatorMixin:
    """提供分页接口"""

    MAX_NUM_PER_PAGE = 10
    IGNORE_EMPTY = True

    def get_paginator(self, objects, count=None, page=None, ignore=None):
        """
        分页器, page不合法时返回第一页, page超出最大页数时返回最后一页
        :param objects:
        :param page: 指定第几页
        :param count: 指定一页最大有多少数据, 默认为 self.MAX_NUM_PER_PAG
        :param ignore: 是否忽略页码错误，True则在错误时返回最后一页信息，否则抛出一个Http404
        :return: Page对象: https://docs.djangoproject.com/zh-hans/2.2/topics/pagination/
        """
        ignore = self.IGNORE_EMPTY if ignore is None else ignore
        paginator = Paginator(objects, count or self.MAX_NUM_PER_PAGE)
        try:
            page = paginator.page(page)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            if ignore:
                num_pages = paginator.num_pages
                try:
                    page = paginator.page(num_pages if num_pages > 0 else 1)
                except EmptyPage:
                    raise Http404()
            else:
                raise Http404()
        return page


class FilterApiView(View, PaginatorMixin):
    """
    以下为一个简单的使用样例s

    class DemoApiView(FilterApiView):

        def serialization(self, object_list):
            return [obj.to_dict() for obj in object_list]

        def filter_company(self, filter_value, queryset):
            '''过滤:公司'''
            try:
                company: Company = Company.objects.get(name=filter_value, creator=self.user)
            except Company.DoesNotExist:
                raise ObjectDoesNotExist('该公司不存在')
            return queryset.filter(category=company)

        def filter_source(self, filter_value, queryset):
            '''过滤:来源'''
            return queryset.filter(source=filter_value)
    """

    # 此 Api 操作的模型
    Model: typing.Type[models.Model] = None
    # 用于 list 方法中处理数据的Form表单
    QueryForm: typing.Type[Form] = None
    # 用于 list 方法中的数据排序
    order_by: typing.Sequence[str] = ("-id",)

    def __init__(self, **kwargs: typing.Any):
        super().__init__(**kwargs)
        self.page_size = None
        self.page = None

    def dispatch(self, request: Request, *args, **kwargs):
        self.request = request
        try:
            page = int(request.GET.get("page", 1))
            self.page = max(1, page)
        except (ValueError, TypeError):
            self.page = 1
        try:
            page_size = int(request.GET.get("page_size", 30))
            self.page_size = max(1, min(page_size, 100))
        except (ValueError, TypeError):
            self.page_size = 30
        order_by: typing.Optional[str] = request.GET.get("order_by")
        self.order_by: list = order_by.split(",") if order_by else self.order_by
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: Request, *args, **kwargs):
        return self.list(request)

    def list(self, request: Request):
        """"""
        queryset = self.get_init_queryset()
        custom_ordering_applied = False  # 标记是否已应用自定义排序

        if self.QueryForm is not None:
            form = self.QueryForm(request.GET)
            if form.is_valid() is False:
                return restful.bad_request(message=form.errors)

            for filter_name, filter_value in form.cleaned_data.items():
                # 对于BooleanField，只有在请求中明确指定时才应用过滤
                field = form.fields.get(filter_name)
                if isinstance(field, forms.BooleanField):
                    # 如果是BooleanField且请求中没有明确指定该字段，跳过过滤
                    if filter_name not in request.GET:
                        continue
                
                if filter_value in [None, ""]:  # 考虑到models.BooleanField字段, 不对boolean类型判断
                    continue
                if not hasattr(self, f"filter_{filter_name}"):
                    continue
                try:
                    # 对于sort_by类型的过滤器，标记已应用自定义排序
                    if filter_name == 'sort_by':
                        custom_ordering_applied = True
                    queryset = getattr(self, f"filter_{filter_name}")(
                        filter_value, queryset
                    )
                except (ObjectDoesNotExist, AssertionError) as e:
                    return restful.bad_request(message=str(e))

        # 只有在没有应用自定义排序时才使用默认排序
        if not custom_ordering_applied:
            queryset = queryset.all().order_by(*self.order_by)
        
        this_page_objs = self.get_paginator(
            queryset, count=self.page_size, page=self.page
        )
        # 使用 paginator.count 复用已有计数，避免发起第二条 COUNT SQL
        total = this_page_objs.paginator.count
        this_paginator = pagination(
            self.request, this_page_objs, self.page, self.page_size, total
        )
        this_page_result = self.serialization(this_page_objs.object_list)
        this_paginator.update({"results": this_page_result})
        return restful.ok(**this_paginator)

    def serialization(self, object_list) -> list:
        """序列化该列表页数据"""
        raise NotImplementedError()

    def get_init_queryset(self):
        """初始化查询"""
        return self.Model.objects.all()
