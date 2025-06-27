# JMeter 测试示例

本目录包含用于 JMeter Toolkit 测试的示例服务器和 JMX 文件。

## 文件说明

### 1. 被测试服务器 (`test_server.py`)
一个简单的 FastAPI 服务器，提供多种 API 端点用于测试：

**基础端点：**
- `GET /` - 根路径
- `GET /health` - 健康检查

**用户管理 API：**
- `POST /api/users` - 创建用户
- `GET /api/users` - 获取用户列表
- `GET /api/users/{id}` - 获取指定用户
- `PUT /api/users/{id}` - 更新用户
- `DELETE /api/users/{id}` - 删除用户

**订单管理 API：**
- `POST /api/orders` - 创建订单
- `GET /api/orders` - 获取订单列表
- `GET /api/orders/{id}` - 获取指定订单

**认证 API：**
- `POST /api/login` - 用户登录

**特殊测试端点：**
- `GET /api/slow` - 慢接口（1-3秒延迟）
- `GET /api/error` - 随机错误接口
- `POST /api/upload` - 文件上传模拟
- `GET /api/stats` - 统计信息

### 2. JMX 测试文件 (`sample_test.jmx`)
包含完整的 JMeter 测试计划：

**主要测试线程组：**
- 5个并发用户
- 每个用户执行3次循环
- 10秒内启动所有用户

**测试步骤：**
1. 健康检查
2. 用户登录
3. 创建用户
4. 获取用户信息
5. 创建订单
6. 获取用户列表
7. 获取统计信息

**压力测试线程组：**（默认禁用）
- 20个并发用户
- 每个用户执行10次循环
- 专门测试慢接口

## 使用方法

### 方法一：手动启动

1. **启动被测试服务器：**
   ```bash
   # 在终端1中启动测试服务器
   ./start_test_server.sh
   
   # 或者直接运行
   python test_server.py
   ```

2. **启动 JMeter Toolkit：**
   ```bash
   # 在终端2中启动 JMeter Toolkit
   ./start_dev.sh
   
   # 或者
   UV_INDEX_URL=https://pypi.org/simple uv run python main.py
   ```

3. **上传并执行 JMX 文件：**
   - 访问 http://localhost:8000
   - 上传 `sample_test.jmx` 文件
   - 点击执行测试
   - 查看测试结果和报告

### 方法二：使用 Docker 环境

1. **启动 Docker 服务：**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **设置环境变量并启动：**
   ```bash
   export DATABASE_URL=postgresql://jmeter:jmeter@localhost:5432/jmeter_toolkit
   export REDIS_URL=redis://localhost:6379/0
   
   # 启动测试服务器（终端1）
   python test_server.py
   
   # 启动 JMeter Toolkit（终端2）
   python main.py
   ```

## 测试场景说明

### 功能测试
- 验证各个 API 端点的基本功能
- 检查请求和响应的正确性
- 验证用户登录和数据创建流程

### 性能测试
- 测试并发用户访问
- 测量响应时间和吞吐量
- 识别性能瓶颈

### 压力测试
- 测试系统在高负载下的表现
- 验证错误处理机制
- 测试慢接口的处理能力

## 预期结果

### 正常运行结果：
- 所有 API 调用应该成功（HTTP 200）
- 断言检查全部通过
- 响应时间在合理范围内

### 性能指标：
- 平均响应时间：< 500ms（除慢接口外）
- 错误率：< 1%
- 吞吐量：根据并发用户数而定

## 自定义测试

### 修改测试参数：
1. 编辑 JMX 文件中的变量：
   - `BASE_URL`: 修改目标服务器地址
   - `USERNAME/PASSWORD`: 修改登录凭据
   - 线程数、循环次数、启动时间等

2. 添加新的测试用例：
   - 复制现有的 HTTP 请求
   - 修改路径、方法和参数
   - 添加相应的断言检查

### 扩展被测服务器：
1. 在 `test_server.py` 中添加新的端点
2. 实现相应的业务逻辑
3. 在 JMX 文件中添加对应的测试请求

## 故障排除

### 常见问题：

1. **连接被拒绝：**
   - 确保测试服务器在端口 3000 运行
   - 检查防火墙设置

2. **认证失败：**
   - 检查用户名密码是否正确
   - 确认登录 API 正常工作

3. **测试超时：**
   - 检查网络连接
   - 调整 JMeter 超时设置

4. **断言失败：**
   - 检查 API 返回的响应格式
   - 确认断言条件是否正确

## 日志和调试

### 查看服务器日志：
测试服务器会输出详细的访问日志，包括：
- 请求时间和路径
- 响应状态码
- 处理时间

### JMeter 调试：
- 使用 "View Results Tree" 查看详细请求/响应
- 使用 "Summary Report" 查看汇总统计
- 使用 "Aggregate Report" 查看聚合数据