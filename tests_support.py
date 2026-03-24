from __future__ import annotations

import inspect

from asgiref.sync import async_to_sync
from django.test import Client


async def _await_value(awaitable):
    return await awaitable


def run_async(callable_obj, *args, **kwargs):
    result = callable_obj(*args, **kwargs) if callable(callable_obj) else callable_obj
    if inspect.isawaitable(result):
        return async_to_sync(_await_value)(result)
    return result


def build_api_client(**kwargs) -> Client:
    return Client(**kwargs)
