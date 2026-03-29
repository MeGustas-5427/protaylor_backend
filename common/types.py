from __future__ import annotations

from typing import Any, TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | dict[str, Any] | list[Any]
JSONDict: TypeAlias = dict[str, JSONValue]


class ChoicesMixin:
    @classmethod
    def choices(cls):
        raise NotImplementedError(f"{cls.__name__}.choices() must be implemented by subclasses.")

    @classmethod
    def select(cls):
        return dict(cls.choices())

    @classmethod
    def label_of(cls, value):
        return cls.select().get(int(value), "")

    @classmethod
    def codes(cls):
        raise NotImplementedError(f"{cls.__name__}.codes() must be implemented by subclasses.")

    @classmethod
    def code_of(cls, value):
        return cls.codes().get(int(value), "")
