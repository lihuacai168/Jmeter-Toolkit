
# 使用官方Python 3.9镜像作为基础镜像
FROM python:3.9-buster

# 设置环境变量
ENV JMETER_VERSION 5.5
ENV JMETER_HOME /opt/apache-jmeter-${JMETER_VERSION}
ENV PATH ${JMETER_HOME}/bin:${PATH}

# 更换apt源为阿里云镜像源，更新系统和安装一些基本软件包
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y wget unzip openjdk-11-jdk ant

# 安装JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt && \
    rm apache-jmeter-${JMETER_VERSION}.tgz && \
    chmod +x ${JMETER_HOME}/bin/jmeter

ARG PIP_INDEX_URL="https://pypi.org/simple"

# 安装项目依赖
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt -i ${PIP_INDEX_URL}

# 设置工作目录
WORKDIR /app

# 将项目文件拷贝到工作目录
COPY . .

# 暴露8000端口
EXPOSE 8000

# 启动FastAPI应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

