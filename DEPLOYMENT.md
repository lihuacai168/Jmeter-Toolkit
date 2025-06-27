# JMeter Toolkit 部署指南

## 📁 项目结构简化

项目已清理文件结构，现在只有两个主要应用文件：

### 🎯 **主要文件**：

- **`main.py`** - 统一应用入口（生产/开发环境自适应）
- **`dev_server.py`** - 简化开发服务器（仅用于测试）

### 🗂️ **启动脚本**：

- **`start_dev.sh`** - 开发环境启动脚本
- **`start_simple.sh`** - 简化测试服务器启动脚本

## 🚀 启动方式

### 1. 开发环境（推荐）

使用统一的 main.py，自动检测环境：

```bash
# 方式一：使用启动脚本
./start_dev.sh

# 方式二：直接运行
ENVIRONMENT=development python main.py

# 方式三：使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 简化测试环境

使用 dev_server.py（仅用于测试）：

```bash
# 方式一：使用启动脚本
./start_simple.sh

# 方式二：直接运行
python dev_server.py
```

### 3. 生产环境

```bash
# 设置生产环境变量
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@localhost/jmeter_toolkit

# 启动应用
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔧 环境配置

### 开发环境变量：
```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite:///./jmeter_toolkit_dev.db
LOG_LEVEL=INFO
```

### 生产环境变量：
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/jmeter_toolkit
LOG_LEVEL=WARNING
```

## 📊 功能对比

| 功能 | main.py (开发模式) | dev_server.py | main.py (生产模式) |
|------|-------------------|---------------|-------------------|
| 数据库 | SQLite | 内存存储 | PostgreSQL |
| JMeter执行 | 模拟执行 | 模拟执行 | 真实执行 |
| 中间件 | 简化 | 基础 | 完整 |
| 监控 | 基础 | 无 | 完整 |
| 安全验证 | 简化 | 基础 | 完整 |
| 适用场景 | 日常开发 | 快速测试 | 生产部署 |

## 🧪 测试运行

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行增强API测试
python -m pytest tests/test_api_enhanced.py -v

# 运行测试覆盖率
python -m pytest tests/ --cov=. --cov-report=html
```

## 📝 说明

1. **main.py** 现在是唯一的应用入口，通过环境变量自动适配不同环境
2. **dev_server.py** 专门用于测试，保持最小化依赖
3. 删除了冗余的 `main_dev.py` 和 `run_dev.py`
4. 使用启动脚本简化常用操作
5. 测试配置已更新为使用 `dev_server.py`