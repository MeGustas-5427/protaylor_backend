from typing import Union

from django.forms import Form, ModelForm
from django.http import JsonResponse, HttpResponse

from constants.code import Code
from utils.myjwt import EXP_TIME


def jsonify(code: int, body=None, *, status: int, **kwargs) -> JsonResponse:
    """
    :param body: 如果不是None, 则只将此参数作为回复内容。
    :param status: HTTP状态码, 详见 https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status
    :param kwargs: 将被转为字典作为返回内容
    :return:
    """
    kwargs["code"] = code
    if body is None:
        res = JsonResponse(
            kwargs, status=status, json_dumps_params={"ensure_ascii": False}
        )
    else:
        res = JsonResponse(
            body, status=status, safe=False, json_dumps_params={"ensure_ascii": False}
        )

    if kwargs.get("token"):
        res.set_cookie("token", kwargs.get("token"), max_age=EXP_TIME)
    return res


def ok(body=None, **kwargs) -> JsonResponse:
    """
    everything be ok!
    """
    return jsonify(Code.OK, body, status=200, **kwargs)


def created(body=None, **kwargs) -> JsonResponse:
    """
    创建资源成功
    """
    return jsonify(code=Code.创建成功, body=body, status=201, **kwargs)


def accepted(body=None, **kwargs) -> JsonResponse:
    """
    接受请求, 已在后台处理
    """
    return jsonify(Code.OK, body, status=202, **kwargs)


def reset_content(body=None, **kwargs) -> JsonResponse:
    """
    重置内容, 服务器成功执行了请求
    """
    return jsonify(Code.OK, body, status=205, **kwargs)


def no_content() -> HttpResponse:
    """
    处理成功, 但没有响应实体
    """
    return HttpResponse(status=204)


def bad_request(code=Code.CLIENT_ERROR, body=None, **kwargs) -> JsonResponse:
    """
    请求的姿势不对, 重来
    """
    return jsonify(code, body, status=400, **kwargs)


def unauthorized(code=Code.CLIENT_UNAUTHORIZED, body=None, **kwargs) -> JsonResponse:
    """
    缺少有效的身份信息
    """
    return jsonify(code, body, status=401, **kwargs)


def forbidden(code, body=None, **kwargs) -> JsonResponse:
    """
    当前携带的身份信息没有访问资格
    """
    return jsonify(code, body, status=403, **kwargs)


def notfound(body=None, **kwargs) -> JsonResponse:
    """
    找不到资源
    """
    return jsonify(Code.不存在或无权查询, body, status=404, **kwargs)


def method_not_allowed(body=None, **kwargs) -> JsonResponse:
    """
    不允许使用的方法
    """
    return jsonify(Code.CLIENT_ERROR, body, status=405, **kwargs)


def server_error(body=None, **kwargs) -> JsonResponse:
    """
    服务器处理出错
    """
    return jsonify(Code.CLIENT_ERROR, body, status=500, **kwargs)


def get_a_error_message(form: Union[Form, ModelForm]) -> JsonResponse:
    """获取form表单第一个错误"""
    for error_field, error_msg_list in form.errors.items():
        # get first as as error message
        return bad_request(message=error_msg_list[0])
