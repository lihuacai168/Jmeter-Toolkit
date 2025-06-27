# 测试指南

## 测试环境设置

项目使用 pytest 作为测试框架，支持 SQLite 数据库进行测试隔离。

### 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行测试覆盖率分析
python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# 运行特定测试文件
python -m pytest tests/test_api.py -v
python -m pytest tests/test_security.py -v
```

## 测试结构

### API 测试 (`tests/test_api.py`)

测试 FastAPI 应用的核心端点：

- ✅ 健康检查端点
- ✅ 指标端点
- ✅ 文件列表端点（JMX/JTL）
- ✅ 任务列表端点
- ✅ 错误处理和边界条件

### 安全测试 (`tests/test_security.py`)

测试安全相关功能：

- ✅ 文件验证（扩展名、大小、MIME类型）
- ✅ 恶意内容扫描
- ✅ 命令参数净化
- ✅ 路径验证
- ✅ 安全文件名生成

### 测试配置 (`tests/conftest.py`)

- 使用 SQLite 内存数据库进行测试隔离
- 自动创建和清理测试目录
- 提供 FastAPI 测试客户端

## 测试覆盖率

当前测试覆盖率：**30%**

主要覆盖的模块：
- ✅ 配置管理 (96%)
- ✅ 数据库模型 (95%)
- ✅ 测试文件 (100%)
- ✅ 安全工具 (51%)
- ✅ 简化开发服务器 (59%)

待改进的覆盖率：
- 🔄 Core JMeter 管理器 (0%)
- 🔄 中间件和错误处理 (0%)
- 🔄 Celery 任务 (0%)
- 🔄 监控工具 (34%)

## 测试最佳实践

### 1. 测试隔离
每个测试使用独立的数据库事务，确保测试间不相互影响。

### 2. 模拟和存根
对外部依赖（如 JMeter 执行）使用模拟，确保测试可靠性。

### 3. 边界条件测试
测试各种边界条件和错误情况，如无效输入、文件不存在等。

### 4. 安全测试
重点测试文件上传、命令执行等安全敏感功能。

## 持续集成

测试可以集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 调试测试

### 运行特定测试
```bash
python -m pytest tests/test_api.py::test_health_check -v -s
```

### 显示完整输出
```bash
python -m pytest tests/ -v -s --tb=long
```

### 调试模式
```bash
python -m pytest tests/ --pdb
```

## 添加新测试

### API 端点测试模板
```python
def test_new_endpoint(client: TestClient):
    """Test new endpoint."""
    response = client.get("/new-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### 安全功能测试模板
```python
def test_security_feature():
    """Test security feature."""
    # Arrange
    input_data = "test_input"
    
    # Act
    result = security_function(input_data)
    
    # Assert
    assert result is True
```

测试是确保代码质量和功能正确性的重要环节，建议在开发新功能时同步编写测试。