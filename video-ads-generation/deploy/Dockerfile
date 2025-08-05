# 1. 基于官方精简版 Python 镜像
FROM python:3.10-slim

# 2. 在容器里创建工作目录 /app
WORKDIR /app

# 3. 先拷贝依赖清单，安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 再把项目所有代码复制进来
COPY . .

# 5. 暴露容器内部的 5001 端口
EXPOSE 5001

# 6. 容器启动时，运行下面命令：用 gunicorn 启动 Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "app:app"]
