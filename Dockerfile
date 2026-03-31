# ==========================================
# 第一阶段：构建阶段
# ==========================================
FROM python:3.14-slim as builder

# 设置pip使用国内镜像源
#RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
#    pip config set global.extra-index-url https://mirrors.aliyun.com/pypi/simple/

# 配置apt使用国内源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装编译依赖（基于你的requirements.txt分析）
RUN apt-get update && apt-get install -y \
    # Python开发头文件(cryptography, cffi需要) \
    python3-dev \
    # C编译器(编译C扩展需要) \
    gcc \
    # PostgreSQL开发库(如果将来要用psycopg2源码版) \
    libpq-dev \
    # 加密库依赖(cryptography需要) \
    libssl-dev \
    libffi-dev \
    # Pillow图像处理依赖 \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    zlib1g-dev \
    # 清理apt缓存 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# 第二阶段：运行阶段
# ==========================================
FROM python:3.14-slim as runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 配置apt使用国内源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 只安装运行时库（不需要开发头文件）
RUN apt-get update && apt-get install -y \
    # PostgreSQL客户端库(psycopg2-binary需要) \
    libpq5 \
    # SSL库(cryptography运行时需要) \
    libssl3 \
    libffi8 \
    # Pillow运行时库 \
    libjpeg62-turbo \
    libpng16-16 \
    libwebp7 \
    libfreetype6 \
    zlib1g \
    # cron定时任务支持 \
    cron \
    # 清理apt缓存 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r django && useradd -r -g django django

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# ✅ 创建必要的目录和文件
RUN mkdir -p /app/logs /app/media /app/staticfiles && \
    touch /app/logs/django.log && \
    chmod -R 777 /app/logs

# 设置权限
RUN chown -R django:django /app

# 切换到非root用户
#USER django

# 收集静态文件
RUN python3 manage.py collectstatic --noinput || true

# 暴露端口
EXPOSE 8000

# 启动命令
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/uvicorn/
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "menu_fresh_api.asgi:application"]
