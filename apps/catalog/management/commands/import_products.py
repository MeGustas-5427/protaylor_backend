"""
Django 管理命令：从 protaylor_products.xlsx 导入产品数据。

使用方式（在 backend/ 目录下）：
    python manage.py import_products --excel "F:/菱威仓管/protaylor_products.xlsx"

前提：
    - 已运行 scripts/generate_summaries.py，Excel 第 344 列已有 AI Summary
    - 数据库迁移已执行（python manage.py migrate）

行为：
    - 幂等：重复运行时，已存在的 Category / Product（按 slug 查找）不会重复创建
    - 分类：L1 == L2 时建单层 Category；L1 != L2 时建 L1（父）→ L2（子）层级
    - 产品：挂在 L2 Category（或单层 Category）下
    - raw_attributes：B区全部非空字段，同语义重复字段保留值最长的
    - 不导入：图片 URL、C区包装字段、source_url、ProductSpecGroup/Row
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

# ── 常量 ──────────────────────────────────────────────────────────────────────
SHEET_NAME = "All Products"

# Excel 列序号（openpyxl 1-indexed / pandas iloc 0-indexed 各差 1）
# 以下统一用 0-based（pandas iloc 列索引）
IDX_L1 = 0           # 一级分类
IDX_L2 = 1           # 二级分类
IDX_NAME = 2         # 产品名称
IDX_MODEL_NO = 4     # 产品型号
IDX_B_START = 5      # B区属性起始列（含）
IDX_B_END = 336      # B区属性结束列（含），共 333 列
IDX_DESC = 342       # E区产品描述
IDX_SUMMARY = 343    # AI Summary（generate_summaries.py 写入）
IDX_LEAD_TEXT = 344  # 页面首段导语
IDX_PRIMARY_QUERY = 345       # 主查询词(核心目标查询)
IDX_SECONDARY_QUERIES = 346   # 次级查询词(每行一个次级查询词)
IDX_BUYER_FIT = 347           # 适合谁
IDX_APPLICATION_SUMMARY = 348 # 应用概述

# is_core_category = True 的 L1 分类名
CORE_CATEGORIES: set[str] = {
    "2L Slush Machine",
    "5 In 1 Slush Freezer",
    "Ice Cream Cone Machines",
    "Ice Cream Machines",
}

# Excel 数据行（pandas 0-indexed）
# row 0 = 二级表头（字段名行），row 1+ = 实际产品
ROW_SUBHEADER = 0
ROW_DATA_START = 1


# ── Slug 工具 ─────────────────────────────────────────────────────────────────
def slugify(text: str, max_len: int = 160) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text[:max_len]


# ── raw_attributes 去重 ───────────────────────────────────────────────────────
def norm_key(field_name: str) -> str:
    """
    标准化字段名用于去重：
      1. 移除括号内容：(V)、（V）、(L*W*H) 等
      2. 仅保留英文字母，转小写
    例：'Voltage (V)' → 'voltage'，'VOLTAGE' → 'voltage'
    """
    s = re.sub(r"[\(\（\[【][^\)\）\]】]*[\)\）\]】]", "", field_name)
    s = re.sub(r"[^a-zA-Z]", "", s)
    return s.lower()


def build_raw_attributes(
    subheader_row: "pd.Series",
    product_row: "pd.Series",
) -> dict[str, Any]:
    """
    从 B区（IDX_B_START..IDX_B_END）提取非空字段。
    同语义重复字段（norm_key 相同）保留 str(value) 最长的那条，
    使用该条的原始字段名作为 key。
    """
    # 临时结构：norm_key → (original_field_name, str_value)
    candidates: dict[str, tuple[str, Any]] = {}

    for col_idx in range(IDX_B_START, IDX_B_END + 1):
        raw_header = subheader_row.iloc[col_idx]
        value = product_row.iloc[col_idx]

        # 跳过空值
        if _is_empty(value):
            continue
        if _is_empty(raw_header):
            continue

        # 从 "Field Name\n(N条产品)" 格式中取字段名
        field_name = str(raw_header).split("\n")[0].strip()
        if not field_name:
            continue

        nk = norm_key(field_name)
        str_val = str(value)

        if nk not in candidates or len(str_val) > len(str(candidates[nk][1])):
            candidates[nk] = (field_name, value)

    return {fn: val for fn, val in candidates.values()}


def _is_empty(val: Any) -> bool:
    if val is None:
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except Exception:
        pass
    return str(val).strip() == ""


# ── 主命令 ────────────────────────────────────────────────────────────────────
class Command(BaseCommand):
    help = "Import products from protaylor_products.xlsx into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--excel",
            required=True,
            help="Path to protaylor_products.xlsx (must have AI Summary column)",
        )
        parser.add_argument(
            "--category-excel",
            default=None,
            help=(
                "Path to protaylor_category.xlsx. "
                "Defaults to protaylor_category.xlsx in the same directory as --excel."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )

    def handle(self, *args, **options):
        try:
            import pandas as pd
        except ImportError:
            raise CommandError("pandas is required: pip install pandas openpyxl")

        from apps.catalog.models import Product, ProductCategory
        from common.enums import IndexMode, PublishStatus

        excel_path = Path(options["excel"])
        if not excel_path.exists():
            raise CommandError(f"File not found: {excel_path}")

        # 分类 Excel：优先用 --category-excel，否则自动检测同目录文件
        cat_excel_arg = options.get("category_excel")
        if cat_excel_arg:
            cat_excel_path = Path(cat_excel_arg)
        else:
            cat_excel_path = excel_path.parent / "protaylor_category.xlsx"

        category_data: dict[str, dict] = {}
        if cat_excel_path.exists():
            self.stdout.write(f"Loading category data: {cat_excel_path}")
            category_data = _load_category_data(cat_excel_path, pd)
            self.stdout.write(f"  Loaded {len(category_data)} category entries.")
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Category Excel not found ({cat_excel_path}); "
                    "category fields will use defaults."
                )
            )

        dry_run: bool = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes."))

        # ── 读取 Excel ────────────────────────────────────────────────────────
        self.stdout.write(f"Reading: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=SHEET_NAME, header=0, dtype=str)

        subheader = df.iloc[ROW_SUBHEADER]       # 字段名行
        data = df.iloc[ROW_DATA_START:].reset_index(drop=True)  # 实际产品行

        total = len(data)
        self.stdout.write(f"Product rows: {total}")

        # ── 第一步：收集并创建/获取所有 Category ─────────────────────────────
        self.stdout.write("Step 1/2: Processing categories …")
        category_map: dict[str, ProductCategory] = {}  # category_name → instance

        # 收集所有唯一的 (L1, L2) 对
        pairs: list[tuple[str, str]] = []
        for _, row in data.iterrows():
            l1 = _clean_str(row.iloc[IDX_L1])
            l2 = _clean_str(row.iloc[IDX_L2])
            if l1:
                pairs.append((l1, l2 if l2 else l1))

        unique_pairs = list(dict.fromkeys(pairs))  # 保持顺序去重

        # 先建所有 L1（无父级）
        l1_names = list(dict.fromkeys(l1 for l1, _ in unique_pairs))
        for l1_name in l1_names:
            cat = _get_or_create_category(
                name=l1_name,
                parent=None,
                is_core=l1_name in CORE_CATEGORIES,
                extra_fields=category_data.get(l1_name, {}),
                dry_run=dry_run,
            )
            category_map[l1_name] = cat

        # 再建所有 L2（有父级，且 L1 != L2）
        for l1_name, l2_name in unique_pairs:
            if l2_name == l1_name:
                continue  # 单层，已建
            if l2_name not in category_map:
                cat = _get_or_create_category(
                    name=l2_name,
                    parent=category_map[l1_name],
                    is_core=False,
                    extra_fields=category_data.get(l2_name, {}),
                    dry_run=dry_run,
                )
                category_map[l2_name] = cat

        self.stdout.write(
            self.style.SUCCESS(f"  Categories ready: {len(category_map)}")
        )

        # ── 第二步：创建/更新 Product ─────────────────────────────────────────
        self.stdout.write("Step 2/2: Importing products …")
        created = updated = skipped = 0

        for idx, row in data.iterrows():
            l1 = _clean_str(row.iloc[IDX_L1])
            l2 = _clean_str(row.iloc[IDX_L2])
            name = _clean_str(row.iloc[IDX_NAME])
            model_no = _clean_str(row.iloc[IDX_MODEL_NO])

            if not name:
                skipped += 1
                continue

            # 产品挂在 L2 Category（或单层时挂在 L1）
            cat_name = l2 if (l2 and l2 != l1) else l1
            category = category_map.get(cat_name)
            if category is None:
                self.stderr.write(f"  [WARN] row {idx + ROW_DATA_START + 2}: category '{cat_name}' not found, skipping.")
                skipped += 1
                continue

            raw_description = _clean_str(row.iloc[IDX_DESC])
            summary = _clean_str(row.iloc[IDX_SUMMARY]) if IDX_SUMMARY < len(row) else ""
            raw_attributes = build_raw_attributes(subheader, row)

            # SEO 字段
            product_slug = slugify(name)
            url_path = f"/products/{category.slug}/{product_slug}"
            meta_desc = raw_description[:160] if raw_description else name[:160]
            lead_text = _clean_str(row.iloc[IDX_LEAD_TEXT])
            primary_query = _clean_str(row.iloc[IDX_PRIMARY_QUERY])
            secondary_queries = _clean_str(row.iloc[IDX_SECONDARY_QUERIES])
            buyer_fit = _clean_str(row.iloc[IDX_BUYER_FIT])
            application_summary = _clean_str(row.iloc[IDX_APPLICATION_SUMMARY])

            defaults = dict(
                name=name,
                model_code=model_no,
                summary=summary,
                raw_description=raw_description,
                raw_attributes=raw_attributes,
                # SEO
                h1=name,
                seo_title=name,
                meta_description=meta_desc,
                url_path=url_path,
                index_mode=IndexMode.INDEX,
                lead_text = lead_text,
                primary_query = primary_query,
                secondary_queries = secondary_queries,
                buyer_fit = buyer_fit,
                application_summary = application_summary,
                # 发布
                status=PublishStatus.PUBLISHED,
                published_at=timezone.now(),
                # 其余
                is_canonical=True,
            )

            if dry_run:
                created += 1
                if (idx + 1) % 50 == 0:
                    self.stdout.write(f"  [dry-run] processed {idx + 1}/{total}")
                continue

            with transaction.atomic():
                obj, was_created = Product.objects.get_or_create(
                    category=category,
                    slug=product_slug,
                    defaults=defaults,
                )
                if not was_created:
                    # 已存在则更新
                    for field, val in defaults.items():
                        setattr(obj, field, val)
                    obj.save()
                    updated += 1
                else:
                    created += 1

            if (created + updated) % 50 == 0:
                self.stdout.write(
                    f"  created={created} updated={updated} skipped={skipped} / {total}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. created={created} updated={updated} skipped={skipped} / total={total}"
            )
        )


# ── 辅助函数 ──────────────────────────────────────────────────────────────────
def _clean_str(val: Any) -> str:
    if _is_empty(val):
        return ""
    return str(val).strip()


def _load_category_data(path: "Path", pd: "Any") -> "dict[str, dict]":
    """
    从 protaylor_category.xlsx 加载分类字段数据。
    返回 {category_name: {field: value}} 字典。

    映射规则：
    - Subcategory == '── All ──'  → key 为 Category（L1 父分类）
    - 其他                         → key 为 Subcategory（L2 子分类或单层分类）
    """
    df = pd.read_excel(str(path), header=0, dtype=str)
    result: dict[str, dict] = {}
    for _, row in df.iterrows():
        cat = _clean_str(row.get("Category", ""))
        sub = _clean_str(row.get("Subcategory", ""))
        if not cat:
            continue
        key = cat if sub in ("── All ──", "-- All --", "") else sub
        result[key] = {
            "meta_description": _clean_str(row.get("meta_description", "")),
            "lead_text":        _clean_str(row.get("lead_text", "")),
            "primary_query":    _clean_str(row.get("primary_query", "")),
            "secondary_queries":_clean_str(row.get("secondary_queries", "")),
            "summary":          _clean_str(row.get("summary", "")),
            "buyer_fit":        _clean_str(row.get("buyer_fit", "")),
            "selection_guide":  _clean_str(row.get("selection_guide", "")),
        }
    return result


def _get_or_create_category(
    name: str,
    parent: "ProductCategory | None",
    is_core: bool,
    extra_fields: dict,
    dry_run: bool,
) -> "ProductCategory | None":
    from apps.catalog.models import ProductCategory
    from common.enums import IndexMode, PublishStatus

    cat_slug = slugify(name)
    url_path = f"/products/{cat_slug}"

    defaults = dict(
        name=name,
        parent=parent,
        is_core_category=is_core,
        h1=name,
        seo_title=name,
        url_path=url_path,
        index_mode=IndexMode.INDEX,
        status=PublishStatus.PUBLISHED,
        published_at=timezone.now(),
        # Fields from category Excel (fall back to empty string if not provided)
        meta_description=extra_fields.get("meta_description", ""),
        lead_text=extra_fields.get("lead_text", ""),
        primary_query=extra_fields.get("primary_query", ""),
        secondary_queries=extra_fields.get("secondary_queries", ""),
        summary=extra_fields.get("summary", ""),
        buyer_fit=extra_fields.get("buyer_fit", ""),
        selection_guide=extra_fields.get("selection_guide", ""),
    )

    obj, _ = ProductCategory.objects.get_or_create(slug=cat_slug, defaults=defaults)
    if not _:
        # Already exists — update the enriched fields so re-runs stay fresh
        for field in (
            "meta_description", "lead_text", "primary_query", "secondary_queries",
            "summary", "buyer_fit", "selection_guide",
        ):
            if extra_fields.get(field):
                setattr(obj, field, extra_fields[field])
        if not dry_run:
            obj.save()
    return obj
