# JMeter Toolkit Test Suite

本目录包含 JMeter Toolkit 的完整测试套件，确保 API 端点的功能性、可靠性和性能。

## 测试文件结构

### 🧪 核心测试文件

| 文件名 | 描述 | 测试数量 | 测试类型 |
|--------|------|----------|----------|
| `test_api.py` | 基础 API 端点测试 | 4 | 单元测试 |
| `test_api_enhanced.py` | 增强的 API 功能测试 | - | 集成测试 |
| `test_security.py` | 安全相关测试 | - | 安全测试 |
| `test_execute_api.py` | **Execute API 专项测试** | 19 | 单元/集成测试 |
| `test_integration_execute.py` | **Execute API 集成测试** | 3 | 集成测试 |
| `test_performance_execute.py` | **Execute API 性能测试** | 8 | 性能测试 |

### 🔧 配置文件

| 文件名 | 描述 |
|--------|------|
| `conftest.py` | pytest 配置和测试装置 |
| `__init__.py` | 测试包初始化 |
| `../pytest.ini` | pytest 全局配置 |

## 新增的 Execute API 测试

### 📋 `test_execute_api.py` - 核心功能测试

**测试覆盖的功能：**

#### 上传相关测试
- ✅ `test_upload_valid_jmx_file` - 有效 JMX 文件上传
- ✅ `test_upload_invalid_file_extension` - 无效文件扩展名处理
- ✅ `test_case_insensitive_jmx_extension` - 文件扩展名大小写处理

#### 执行相关测试
- ✅ `test_execute_existing_jmx_file` - 执行已存在的 JMX 文件
- ✅ `test_execute_nonexistent_jmx_file` - 执行不存在的文件
- ✅ `test_execute_missing_file_name` - 缺少文件名参数
- ✅ `test_execute_invalid_file_name_type` - 无效文件名类型

#### 上传并执行测试
- ✅ `test_upload_and_execute_valid_file` - 有效文件的上传并执行
- ✅ `test_upload_and_execute_invalid_file` - 无效文件处理
- ✅ `test_upload_and_execute_empty_file` - 空文件处理
- ✅ `test_upload_and_execute_large_file` - 大文件处理

#### 并发和序列测试
- ✅ `test_sequential_executions` - 连续执行测试
- ✅ `test_concurrent_uploads` - 并发上传测试

#### 任务管理测试
- ✅ `test_get_task_after_execution` - 执行后任务查询
- ✅ `test_list_tasks_after_executions` - 任务列表查询

#### 错误处理测试
- ✅ `test_error_handling_in_upload_and_execute` - 错误处理机制
- ✅ `test_file_cleanup_and_isolation` - 文件清理和隔离

### 🔗 `test_integration_execute.py` - 集成测试

**需要真实测试服务器运行的测试：**

- ✅ `test_execute_with_real_jmx_against_test_server` - 对真实服务器执行测试
- ✅ `test_upload_and_execute_with_real_jmx` - 完整的上传执行流程
- ✅ `test_end_to_end_workflow` - 端到端工作流程测试

**特殊功能：**
- 自动启动 `test_examples/test_server.py`
- 验证与真实被测试服务器的交互
- 测试完整的 JMeter 执行流程

### ⚡ `test_performance_execute.py` - 性能测试

**性能指标测试：**

- ⏱️ `test_upload_response_time` - 上传响应时间 (< 2秒)
- ⏱️ `test_execute_response_time` - 执行响应时间 (< 1秒)
- ⏱️ `test_upload_and_execute_response_time` - 组合操作响应时间 (< 3秒)
- 🔄 `test_concurrent_uploads` - 并发上传性能
- 🔄 `test_concurrent_executions` - 并发执行性能
- 📁 `test_large_file_upload` - 大文件上传性能
- 💾 `test_memory_usage_multiple_operations` - 内存使用测试
- 🌐 `test_api_endpoint_response_times` - API 端点响应时间

## 测试标记 (Markers)

```ini
markers =
    slow: 标记慢速测试
    integration: 标记集成测试
    unit: 标记单元测试
    performance: 标记性能测试
    security: 标记安全测试
    api: 标记 API 测试
```

## 运行测试

### 🚀 运行特定测试套件

```bash
# 运行所有 Execute API 测试
pytest tests/test_execute_api.py -v

# 运行集成测试
pytest tests/test_integration_execute.py -v

# 运行性能测试
pytest tests/test_performance_execute.py -v -m performance

# 运行所有测试
pytest tests/ -v
```

### 📊 运行带覆盖率的测试

```bash
# 运行测试并生成覆盖率报告
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# 只运行 Execute API 测试的覆盖率
pytest tests/test_execute_api.py --cov=main --cov-report=term-missing
```

### 🔍 运行特定类型的测试

```bash
# 只运行单元测试
pytest -m unit

# 跳过慢速测试
pytest -m "not slow"

# 只运行性能测试
pytest -m performance

# 运行 API 相关测试
pytest -m api
```

## CI/CD 集成

测试已完全集成到 GitHub Actions CI/CD 流水线中：

### 📋 CI 测试步骤

1. **安全测试** - `test_security.py`
2. **API 测试** - `test_api.py`
3. **增强 API 测试** - `test_api_enhanced.py`
4. **Execute API 测试** - `test_execute_api.py` ⭐ (新增)
5. **集成测试** - `test_integration_execute.py` ⭐ (新增)
6. **性能测试** - `test_performance_execute.py` ⭐ (新增)
7. **完整测试套件** - 所有测试 + 覆盖率

### ⚙️ CI 配置特点

- ✅ 使用 UV 包管理器进行快速依赖安装
- ✅ 多 Python 版本测试 (3.9, 3.10, 3.11, 3.12)
- ✅ 并行测试执行提高效率
- ✅ 覆盖率报告自动生成和上传
- ✅ 性能测试设置为 `continue-on-error: true`

## 测试环境配置

### 🛠️ 测试装置 (Fixtures)

- `client` - FastAPI 测试客户端
- `setup_test_env` - 测试环境初始化
- 自动创建测试目录 (`jmx_files`, `jtl_files`, `reports`)
- 自动清理测试数据库

### 🔧 环境变量

```bash
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=testing
DEBUG=true
```

## 测试数据

### 📄 测试 JMX 文件

所有测试使用动态生成的有效 JMX 内容，包含：

- 基本的 TestPlan 结构
- 简单的 ThreadGroup 配置
- HTTPSamplerProxy 示例
- 标准的 JMeter XML 格式

### 📁 文件管理

- 测试文件自动生成和清理
- 唯一文件名避免冲突
- 路径和权限验证

## 断言策略

### ✅ 响应验证

- HTTP 状态码检查
- JSON 响应结构验证
- 业务逻辑结果验证
- 错误消息准确性检查

### 📋 数据完整性

- 文件上传后的存在性验证
- 任务创建后的状态检查
- 生成文件的内容和大小验证

### ⚡ 性能要求

- 响应时间阈值检查
- 并发处理能力验证
- 资源使用合理性检查

## 故障排除

### 🐛 常见测试失败原因

1. **时间戳相关失败** - 测试运行太快导致文件名重复
   - 解决方案：添加小延迟或使用更精确的时间戳

2. **文件路径问题** - 测试目录未正确创建
   - 解决方案：检查 `conftest.py` 中的目录创建逻辑

3. **端口冲突** - 测试服务器端口被占用
   - 解决方案：确保测试前清理端口或使用随机端口

4. **权限问题** - 文件创建/删除权限不足
   - 解决方案：检查测试目录权限

### 🔍 调试技巧

```bash
# 详细输出调试信息
pytest tests/test_execute_api.py -v -s

# 停在第一个失败的测试
pytest tests/test_execute_api.py -x

# 运行特定的测试方法
pytest tests/test_execute_api.py::TestExecuteAPI::test_upload_valid_jmx_file -v

# 显示本地变量
pytest tests/test_execute_api.py --tb=long
```

## 贡献指南

### 📝 添加新测试

1. 在适当的测试文件中添加测试方法
2. 使用描述性的测试名称
3. 添加适当的测试标记
4. 确保测试可以独立运行
5. 添加必要的文档字符串

### 🏷️ 测试命名规范

- `test_功能_场景()` - 如 `test_upload_valid_file()`
- 使用描述性名称说明测试目的
- 按功能模块组织测试类

### 📚 文档要求

- 每个测试方法都要有文档字符串
- 说明测试的目的和预期结果
- 记录特殊的测试条件或依赖

---

## 📈 测试覆盖率目标

- **单元测试覆盖率**: > 90%
- **集成测试覆盖率**: > 80%
- **关键路径覆盖率**: 100%

通过这个全面的测试套件，我们确保 JMeter Toolkit 的 Execute API 功能稳定、可靠且性能优良。