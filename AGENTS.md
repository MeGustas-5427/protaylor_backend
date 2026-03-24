# PRO-TAYLOR Backend Project Rules

## 项目定位

- 这是 `PRO-TAYLOR` 官网的正式后端，不是原型服务，不是纯 CMS 壳子。
- 当前目标优先支持：
  - 首页配置
  - 产品分类页 / 产品详情页
  - 资源页 / 解决方案页 / 公司页
  - 全站导航、页脚、联系方式
  - 询盘提交与来源上下文
- 业务方向是 `B2B 询盘 + SEO + GEO`，不是零售购物车体系。

## 当前技术栈

- `Django 6`
- `django-ninja`
- 本地默认可用 `SQLite`
- 生产目标数据库是 `PostgreSQL`

## 当前目录结构

- `protaylor_api/`
  - 当前唯一主 project package
  - 包含 `settings.py`、`urls.py`、`api.py`、`asgi.py`、`wsgi.py`
- `apps/`
  - 业务 app 所在目录
  - 当前主要 app：`core`、`catalog`、`content`、`inquiries`
- `common/`
  - 公共类型、枚举、模型基类、配置、展示层辅助
- `tests_support.py`
  - 测试辅助

## 模型写法总原则

- 模型写法风格对齐 `F:\menu-fresh\backend`。
- 枚举字段优先使用：
  - `IntEnum`
  - `ChoicesMixin`
  - `PositiveSmallIntegerField`
- 关系字段要显式写出：
  - `verbose_name`
  - `related_name`
  - `on_delete`
  - `help_text`
- 公共时间字段、排序字段、发布字段、SEO 字段优先复用 `common/models.py` 里的基类和 mixin。

## 枚举字段规则

- 不要回退到 `TextChoices + CharField` 作为默认方案。
- 新增枚举字段时，优先沿用：
  - `choices()`
  - `codes()`
  - `code_of()`
- API 输出如果需要稳定的字符串语义，优先通过 `*_code` 属性提供，而不是把数据库字段重新改回字符串。

## 关联字段规则

- 强关系保留数据库外键约束。
- `可空 + 允许目标删除后保留历史记录` 的弱关联使用：
  - `on_delete=models.SET_NULL`
  - `null=True`
  - `blank=True`
  - `db_constraint=False`
- 不要把 `db_constraint=False` 滥用到强关系上。
- 如果关系本身承担业务主链路，不要为了迁就历史数据轻易去掉数据库约束。

## 当前已经明确的弱关联语义

- `InquirySourceContext.product`
- `InquirySourceContext.variant`
- `ProductRelation.related_product`
- `ProductRelation.related_resource`
- `HomeFeaturedCard.asset`
- `HomeProofItem.asset`
- `PageSEO.og_image`

## 迁移规则

- 修改已存在的枚举字段时，优先考虑历史数据兼容，不要只依赖 Django 自动生成迁移。
- 遇到 `字符串枚举 -> 整型枚举` 的调整时，必须补 `RunPython` 做数据转换。
- 已有字段改名时，优先考虑 `RenameField`，不要直接 `RemoveField + AddField` 导致数据丢失。
- 不要为了省事删除已执行迁移并重建历史。
- 新增模型字段后，先检查迁移语义是否正确，再执行 `migrate`。

## 当前 app 边界

- `core`
  - 组织信息、媒体资源、联系方式、导航、页脚、SEO 扩展、页面关系
- `catalog`
  - 产品分类、产品、变体、规格、卖点、应用场景、媒体、下载、产品关系
- `content`
  - 首页配置、首页模块数据、解决方案、资源文章、公司页面、FAQ
- `inquiries`
  - 询盘主体、来源上下文、revalidate 相关写入契约

## API 约定

- API 统一从 `protaylor_api/api.py` 聚合注册。
- 每个 app 默认按以下结构组织：
  - `models.py`
  - `admin.py`
  - `api.py`
  - `schemas.py`
  - `services.py`
  - `tests.py`
- 读接口优先放在 app 自己的 `services.py` 做查询拼装，再由 `api.py` 暴露。
- 不要把复杂查询和展示拼装逻辑直接堆进 `api.py`。
- 不要让前端直接依赖 Django ORM 字段细节；优先通过 schema 明确输出契约。

## Admin 约定

- Django admin 是正式录入入口，不是临时摆设。
- admin 默认优先补齐：
  - `search_fields`
  - `list_filter`
  - `list_display`
  - `autocomplete_fields`
  - `list_select_related`
- inline 里若记录可能需要单独编辑，优先加 `show_change_link = True`。
- 能预填 slug 的页面模型，优先设置 `prepopulated_fields`。
- 后续新增页面型模型时，优先考虑录入效率，不要只注册最裸的 `ModelAdmin`。

## SEO / GEO 相关后端原则

- 数据库存业务字段，不库存原始 `JSON-LD`。
- 页面类型需要的结构化数据由前端按模板生成：
  - `Organization`
  - `Product`
  - `BreadcrumbList`
  - `FAQPage`
  - `Article / BlogPosting`
- 后端字段设计要能支撑这些 schema，而不是让前端从富文本里硬拆。
- `quick facts` 这类前端模块应来自结构化字段或结构化关系，不要长期靠手写 JSX 常量。

## 测试与验证

- 涉及模型、迁移、admin、API 契约的改动后，至少运行：
  - `.\.venv\Scripts\python.exe manage.py check`
  - `.\.venv\Scripts\python.exe manage.py test apps.core apps.content apps.catalog apps.inquiries`
- 涉及迁移的改动后，额外运行：
  - `.\.venv\Scripts\python.exe manage.py migrate`

## 当前明确不要做的事

- 不要恢复 `protaylor_backend` 兼容层。
- 不要把旧站模板字段直接搬成新模型主字段。
- 不要把后台做成自由拖拽 page builder。
- 不要让产品页和首页长期依赖“写死在代码里”的正式业务内容。
- 不要为了图省事把所有外键都改成 `db_constraint=False`。
