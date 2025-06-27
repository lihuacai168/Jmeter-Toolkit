# JMeter Toolkit v2.0

![CI/CD](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/CI/CD%20Pipeline/badge.svg)
![Code Quality](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Code%20Quality/badge.svg)
![Security](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Security%20Scan/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)
![Coverage](https://img.shields.io/badge/coverage-41%25-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

JMeter Toolkit 是一个专门为 JMeter 测试管理而设计的强大工具集。  
基于 FastAPI 构建，提供现代化的 RESTful API 和强大的后端服务。  
支持异步任务处理、数据持久化、监控指标和分布式部署。

## ✅ 已实现功能

- [x] **JMX文件上传和验证**
- [x] **异步JMeter执行**
- [x] **JTL结果文件管理**
- [x] **HTML报告生成**
- [x] **任务状态管理**
- [x] **文件安全验证**
- [x] **数据库持久化**
- [x] **健康检查和监控**
- [x] **现代化Web界面**
- [x] **Docker容器化部署**
- [x] **分布式任务队列**
- [x] **API文档和测试**

## 🚀 新增特性 (v2.0)

- **异步任务处理**: 使用 Celery + Redis 实现后台任务执行
- **数据持久化**: PostgreSQL 数据库存储任务和文件信息
- **安全增强**: 多层文件验证和恶意内容检测
- **监控集成**: Prometheus 指标和健康检查
- **现代界面**: Bootstrap 5 响应式设计
- **高可用性**: 支持多实例部署和负载均衡


# 使用演示
## 1. 上传，执行，报告一条龙
![jmx-upload-execute-report.gif](docs%2Fjmx-upload-execute-report.gif)

## 2. 上传JMX文件并执行
![upload-execute.png](docs%2Fupload-execute.png)
## 3. 查看报告
![report.png](docs%2Freport.png)
# 快速启动

## 开发环境

### 1. 克隆项目
```bash
git clone <repository-url>
cd jmeter_toolit
```

### 2. 安装依赖
```bash
# 推荐使用 Python 3.11+
pip install -r requirements.txt
```

### 3. 启动开发服务器
```bash
# 主要开发服务器
python main.py

# 或使用简化版开发服务器（用于测试）
python dev_server.py
```

### 4. 访问应用
- **主界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 生产环境

### 1. 使用 Docker Compose（推荐）
```bash
# 启动所有服务（PostgreSQL + Redis + App + Celery）
make deploy

# 或者
docker-compose up -d
```

### 2. 使用 Make 命令
```bash
# 查看所有可用命令
make help

# 开发环境
make setup-dev
make dev

# 测试
make test
make lint

# 部署
make build
make up
```

### 3. 访问服务
- **主应用**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **监控指标**: http://localhost:8000/metrics
- **Celery监控**: http://localhost:5555




# Contributors
<a href="https://github.com/lihuacai168/Jmeter-Toolkit/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=lihuacai168/Jmeter-Toolkit" />
</a>
