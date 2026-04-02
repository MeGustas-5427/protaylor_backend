import asyncio
import typing
from asgiref.sync import sync_to_async

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

# Django 4.2+ supports Paginator.apage(); Django 6.0 is the project baseline.


class AsyncPaginatorMixin:
    """提供异步分页接口"""

    MAX_NUM_PER_PAGE = 10
    IGNORE_EMPTY = True

    async def get_paginator(self, objects, count=None, page=None, ignore=None):
        """
        异步分页器, page不合法时返回第一页, page超出最大页数时返回最后一页
        :param objects: QuerySet对象
        :param page: 指定第几页
        :param count: 指定一页最大有多少数据, 默认为 self.MAX_NUM_PER_PAGE
        :param ignore: 是否忽略页码错误，True则在错误时返回最后一页信息，否则抛出一个Http404
        :return: Page对象: https://docs.djangoproject.com/zh-hans/2.2/topics/pagination/
        """
        ignore = self.IGNORE_EMPTY if ignore is None else ignore

        # Django 4.2+ 原生支持 Paginator.apage()，无需 sync_to_async 包装
        paginator = Paginator(objects, count or self.MAX_NUM_PER_PAGE)
        try:
            return await paginator.apage(page)
        except PageNotAnInteger:
            return await paginator.apage(1)
        except EmptyPage:
            if ignore:
                num_pages = await paginator.anum_pages()
                try:
                    return await paginator.apage(num_pages if num_pages > 0 else 1)
                except EmptyPage:
                    raise Http404()
            raise Http404()


class AsyncFilterApiView(View, AsyncPaginatorMixin):
    """
    异步版本的FilterApiView，完全复刻原版所有功能
    
    使用样例:
    
    class DemoAsyncApiView(AsyncFilterApiView):
    
        async def serialization(self, object_list):
            return [await sync_to_async(obj.to_dict)() for obj in object_list]
        
        async def filter_company(self, filter_value, queryset):
            '''过滤:公司'''
            try:
                company = await sync_to_async(Company.objects.get)(
                    name=filter_value, creator=self.user
                )
            except Company.DoesNotExist:
                raise ObjectDoesNotExist('该公司不存在')
            return queryset.filter(category=company)
        
        async def filter_source(self, filter_value, queryset):
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

    async def dispatch(self, request: Request, *args, **kwargs):
        """异步dispatch方法"""
        self.setup(request, *args, **kwargs)
        
        # 处理页码参数，确保为正数
        try:
            page = int(request.GET.get("page", 1))
            self.page = max(1, page)
        except (ValueError, TypeError):
            self.page = 1
            
        # 处理页大小参数，确保为正数且在合理范围内
        try:
            page_size = int(request.GET.get("page_size", 30))
            self.page_size = max(1, min(page_size, 100))  # 限制在1-100之间
        except (ValueError, TypeError):
            self.page_size = 30
            
        order_by: typing.Optional[str] = request.GET.get("order_by")
        self.order_by: list = order_by.split(",") if order_by else self.order_by
        
        # 获取对应的HTTP方法处理器
        handler = getattr(self, request.method.lower(), None)
        if handler is None:
            return restful.method_not_allowed()
        
        # 调用异步处理器
        return await handler(request, *args, **kwargs)

    async def get(self, request: Request, *args, **kwargs):
        """异步GET方法"""
        return await self.list(request)

    async def list(self, request: Request):
        """异步列表方法"""
        queryset = await self.get_init_queryset()
        custom_ordering_applied = False  # 标记是否已应用自定义排序

        if self.QueryForm is not None:
            # Form验证是同步的，需要包装
            @sync_to_async
            def validate_form():
                form = self.QueryForm(request.GET)
                return form, form.is_valid()
            
            form, is_valid = await validate_form()
            
            if not is_valid:
                return restful.bad_request(message=form.errors)

            # 处理每个过滤条件
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
                    
                    # 调用异步过滤方法
                    filter_method = getattr(self, f"filter_{filter_name}")
                    if asyncio.iscoroutinefunction(filter_method):
                        queryset = await filter_method(filter_value, queryset)
                    else:
                        # 如果过滤方法不是异步的，将其包装为异步
                        queryset = await sync_to_async(filter_method)(filter_value, queryset)
                        
                except (ObjectDoesNotExist, AssertionError) as e:
                    return restful.bad_request(message=str(e))

        # 只有在没有应用自定义排序时才使用默认排序
        # order_by() 是惰性操作，不触碰数据库，无需 sync_to_async
        if not custom_ordering_applied:
            queryset = queryset.all().order_by(*self.order_by)

        # 获取分页数据
        this_page_objs = await self.get_paginator(
            queryset, count=self.page_size, page=self.page
        )

        # 使用 paginator.count 复用已有计数，避免发起第二条 COUNT SQL
        total = this_page_objs.paginator.count
        
        # 构建分页信息
        this_paginator = pagination(
            self.request, this_page_objs, self.page, self.page_size, total
        )
        
        # 序列化数据
        this_page_result = await self.serialization(this_page_objs.object_list)
        this_paginator.update({"results": this_page_result})
        
        return restful.ok(**this_paginator)

    async def serialization(self, object_list) -> list:
        """异步序列化该列表页数据"""
        raise NotImplementedError()

    async def get_init_queryset(self):
        """异步初始化查询"""
        return self.Model.objects.all()


