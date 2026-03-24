# PRO-TAYLOR Backend

`F:\菱威仓管\protaylor_web\backend` 现在是一个可运行的 `Django + django-ninja` 后端骨架，面向 `English-main site`，优先支持：

- 首页配置
- 产品分类页 / 产品详情页
- 全站导航、页脚、联系方式
- FAQ / 页面关系 / SEO 扩展字段
- 询盘提交与来源上下文
- 后续对接 `Next.js App Router` 的只读 API 与 ISR revalidate webhook

## 当前技术栈

- `Django 6`
- `django-ninja`
- `psycopg`
- 默认本地开发可用 `SQLite`
- 生产目标数据库：`PostgreSQL`

## 已实现的 app

- `core`
  - `organization_profile`
  - `media_asset`
  - `contact_channel`
  - `navigation_item`
  - `footer_link_group`
  - `footer_link`
  - `page_seo`
  - `page_relation`
- `catalog`
  - `product_category`
  - `product`
  - `product_variant`
  - `product_spec_group`
  - `product_spec_row`
  - `product_feature`
  - `product_use_case`
  - `product_media`
  - `product_download`
  - `product_relation`
- `content`
  - `home_config`
  - `home_buyer_path`
  - `home_value_point`
  - `home_featured_card`
  - `home_proof_item`
  - `solution_page`
  - `resource_article`
  - `company_page`
  - `faq_item`
- `inquiries`
  - `inquiry`
  - `inquiry_source_context`

## 目录说明

- `protaylor_api/`
  - 当前唯一主 project package
  - 聚合 `settings.py`、`urls.py`、`api.py`、`asgi.py`、`wsgi.py`
- `apps/`
  - 业务 app 所在目录
  - 每个 app 按 `models.py / admin.py / api.py / schemas.py / services.py / tests.py` 组织
- `common/`
  - 公共配置、枚举与模型基类、API 展示层辅助
  - 当前包含 `config.py`、`enums.py`、`types.py`、`models.py`、`api_schemas.py`、`presenters.py`
- `apps/core/management/commands/seed_sample_site.py`
  - 本地联调用样例数据
- `tests_support.py`
  - Django API smoke tests 复用的测试辅助

## API 范围

当前已暴露的稳定接口：

- `GET /api/v1/site/home`
- `GET /api/v1/site/organization`
- `GET /api/v1/site/navigation`
- `GET /api/v1/site/footer`
- `GET /api/v1/site/contact-channels`
- `GET /api/v1/site/chrome`
- `GET /api/v1/catalog/categories/{slug}`
- `GET /api/v1/catalog/products/{category_slug}/{product_slug}`
- `POST /api/v1/inquiries/`
- `POST /api/v1/inquiries/revalidate-hook`
- `GET /healthz/`

说明：

- 后端只存业务字段，不存原始 `JSON-LD`
- `quick facts` 来自 `product_spec_row.is_highlight=True`
- 产品相关推荐已强制拆分为：
  - `related_product`
  - `related_resource`

## 本地运行

### 1. 安装依赖

你已经安装过依赖；如果后续重建环境，执行：

```powershell
uv sync
```

或：

```powershell
pip install -r requirements.txt
```

### 2. 准备环境变量

复制 `.env.example` 为 `.env`，按需填写。

### 3. 执行迁移

```powershell
python manage.py migrate
```

### 4. 灌入样例数据

```powershell
python manage.py seed_sample_site
```

### 5. 启动开发服务器

```powershell
python manage.py runserver
```

## 已验证命令

以下命令已在当前工作区执行通过：

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test apps.core apps.content apps.catalog apps.inquiries
```

补充说明：

- 当前迁移链已经兼容旧版字符串枚举数据到新版整型枚举字段的升级。
- 枚举字段、关联字段、公共模型基类的写法已对齐 `F:\menu-fresh\backend` 的风格。
- 关联字段的约束策略也按参考项目收口：强关系保留数据库外键约束，`可空 + 允许目标删除后保留历史记录` 的弱关联使用 `db_constraint=False`。
- Django admin 的当前约定也已统一：优先补 `search_fields`，跨表选择优先用 `autocomplete_fields`，列表页优先用 `list_select_related` 降低查询抖动。

并已验证这些接口可以返回 `200`：

- `/api/v1/site/home`
- `/api/v1/site/organization`
- `/api/v1/site/navigation`
- `/api/v1/site/footer`
- `/api/v1/site/contact-channels`
- `/api/v1/site/chrome`
- `/api/v1/catalog/categories/soft-ice-cream-machine`
- `/api/v1/catalog/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine`
- `POST /api/v1/inquiries/`
- `GET /api/healthz`

## 环境变量

### Django

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_TIME_ZONE`

### 数据库

优先支持：

- `DATABASE_URL`

例如：

```env
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/protaylor
```

如果不用 `DATABASE_URL`，也支持：

- `DB_ENGINE=postgres`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_CONN_MAX_AGE`

### Revalidate

- `REVALIDATE_SHARED_SECRET`

## 与前端契约的当前约定

- 首页 API 返回：
  - `buyer_paths`
  - `core_categories`
  - `value_points`
  - `featured_cards`
  - `proof_items`
  - `faq_items`
- 产品详情 API 返回：
  - `variants`
  - `quick_facts`
  - `spec_groups`
  - `features`
  - `use_cases`
  - `media_items`
  - `downloads`
  - `related_products`
  - `related_resources`
  - `faq_items`
- 询盘 API 接收来源上下文：
  - `source_page_type`
  - `source_page_path`
  - `source_page_title`
  - `category_slug`
  - `product_slug`
  - `variant_code`
  - `utm_source`
  - `utm_medium`
  - `utm_campaign`
  - `referer`

## 仍需你手动接入的内容

- 生产环境 PostgreSQL 实例
- 生产 `.env`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `REVALIDATE_SHARED_SECRET`
- 真正的媒体资源存储方案
  - 当前 `media_asset.file_url` 用的是 URL 字符串
  - 还没有接 S3 / OSS / 本地上传策略
- 管理员账号
  - 需要手动执行：

```powershell
python manage.py createsuperuser
```

## 后续建议

- 下一步可以补：
  - 分类页更多筛选字段
  - 资源页 / 解决方案页详情 API
  - 后台录入约束与字段帮助文本
  - 更正式的 API versioning / auth 策略
  - 对接前端 ISR 的真实 revalidate 调用
