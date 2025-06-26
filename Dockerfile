FROM python:3.11-slim-bullseye

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


# Install system dependencies for python-magic and PostgreSQL
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -i ${PIP_INDEX_URL}

WORKDIR /app

COPY . .

EXPOSE 8000

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

