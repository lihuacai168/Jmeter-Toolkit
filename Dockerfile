FROM python:3.9-buster

# 设置环境变量
ENV JMETER_VERSION 5.5
ENV JMETER_HOME /opt/apache-jmeter-${JMETER_VERSION}
ENV PATH ${JMETER_HOME}/bin:${PATH}

ARG DEBIAN_REPO="deb.debian.org"


ARG DEBIAN_REPO="deb.debian.org"
ARG PIP_INDEX_URL="https://pypi.org/simple"

# replace sources.list, if use docker-compose
RUN echo "deb http://$DEBIAN_REPO/debian/ buster main contrib non-free" > /etc/apt/sources.list && \
    echo "deb-src http://$DEBIAN_REPO/debian/ buster main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://$DEBIAN_REPO/debian-security buster/updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb-src http://$DEBIAN_REPO/debian-security buster/updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://$DEBIAN_REPO/debian/ buster-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb-src http://$DEBIAN_REPO/debian/ buster-updates main contrib non-free" >> /etc/apt/sources.list

# update apt-get and install packages
RUN  apt-get update && \
    apt-get install -y wget unzip openjdk-11-jdk ant

# install JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt && \
    rm apache-jmeter-${JMETER_VERSION}.tgz && \
    chmod +x ${JMETER_HOME}/bin/jmeter


# install python packages
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt -i ${PIP_INDEX_URL}

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

