from __future__ import annotations

from enum import IntEnum

from common.types import ChoicesMixin


class PublishStatus(ChoicesMixin, IntEnum):
    DRAFT = 1
    PUBLISHED = 2
    ARCHIVED = 3

    @classmethod
    def choices(cls):
        names = {
            cls.DRAFT: "Draft",
            cls.PUBLISHED: "Published",
            cls.ARCHIVED: "Archived",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.DRAFT.value: "draft",
            cls.PUBLISHED.value: "published",
            cls.ARCHIVED.value: "archived",
        }


class IndexMode(ChoicesMixin, IntEnum):
    INDEX = 1
    NOINDEX = 2

    @classmethod
    def choices(cls):
        names = {
            cls.INDEX: "Index",
            cls.NOINDEX: "Noindex",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.INDEX.value: "index",
            cls.NOINDEX.value: "noindex",
        }
