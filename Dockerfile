# 使用官方的 Python 3.9 slim 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /scade

# 将当前目录的内容复制到容器中
COPY . /scade

RUN apt-get update
# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 设置启动命令
CMD ["tail", "-f", "/dev/null"]