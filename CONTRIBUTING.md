# Contributing to JMeter Toolkit

欢迎为JMeter Toolkit贡献代码！本文档将指导您如何设置开发环境并参与项目贡献。

## 🚀 快速开始

### 1. 克隆项目并设置开发环境

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/jmeter_toolit.git
cd jmeter_toolit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 一键设置开发环境
make dev-setup
```

这将自动：
- 安装所有开发依赖
- 设置pre-commit钩子
- 配置代码质量工具

### 2. 验证环境设置

```bash
# 运行测试
make test

# 检查代码格式
make format-check

# 运行所有代码质量检查
make lint
```

## 🔧 开发工作流

### 代码修改流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码**
   - 遵循现有代码风格
   - 添加必要的测试
   - 更新文档

3. **代码质量检查**
   ```bash
   # 自动格式化代码
   make format
   
   # 运行测试
   make test
   
   # 检查代码质量
   make lint
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
   
   > **注意**：pre-commit钩子会自动运行，确保代码质量！

5. **推送并创建PR**
   ```bash
   git push origin feature/your-feature-name
   # 然后在GitHub上创建Pull Request
   ```

### Pre-commit钩子说明

提交代码时，以下检查会自动运行：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码规范检查
- **mypy**: 类型检查
- **bandit**: 安全扫描
- **autoflake**: 移除未使用的导入
- **docformatter**: 文档字符串格式化

如果检查失败，提交将被阻止。运行 `make format` 可以自动修复大多数问题。

## 📝 代码规范

### Python代码风格

- 使用 **Black** 进行代码格式化（行长度127字符）
- 使用 **isort** 对导入进行排序
- 遵循 **PEP 8** 标准
- 使用类型注解（Type Hints）
- 编写有意义的文档字符串

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型示例：**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建流程或工具变动

**示例：**
```
feat(api): add file upload validation
fix(docker): resolve health check timeout issue
docs(readme): update installation instructions
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 并行运行测试（更快）
make test-fast
```

### 编写测试

- 所有新功能都应该有相应的测试
- 测试文件放在 `tests/` 目录下
- 使用 `pytest` 作为测试框架
- 测试覆盖率应保持在90%以上

### 测试类型

1. **单元测试** (`tests/test_*.py`)
   - 测试单个函数或类
   - 快速执行
   - 高覆盖率

2. **集成测试** (`tests/test_api_enhanced.py`)
   - 测试组件间交互
   - 真实文件上传/下载
   - API端到端测试

3. **安全测试** (`tests/test_security.py`)
   - 文件验证
   - 命令注入防护
   - 路径遍历防护

## 🐳 Docker测试

```bash
# 构建并测试Docker镜像
make docker-ci

# 仅构建镜像
make docker-build

# 测试生产镜像
make docker-test
```

## 🔒 安全检查

```bash
# 运行所有安全检查
make security
```

包括：
- **Bandit**: Python安全漏洞扫描
- **Safety**: 依赖漏洞检查
- **pip-audit**: Python包安全审计

## 📊 代码质量工具

### 可用的Make命令

```bash
make help              # 显示所有可用命令
make install           # 安装生产依赖
make install-dev       # 安装开发依赖
make setup-hooks       # 设置pre-commit钩子
make format            # 格式化代码
make format-check      # 检查代码格式
make lint             # 运行代码检查
make test             # 运行测试
make test-cov         # 运行测试并生成覆盖率报告
make security         # 运行安全检查
make clean            # 清理临时文件
make ci-local         # 模拟完整CI流程
```

### CI/CD本地验证

在提交前，建议运行完整的CI流程：

```bash
make ci-local
```

这将运行与GitHub Actions相同的检查流程。

## 🚦 GitHub Actions

项目配置了完整的CI/CD流水线：

1. **CI Pipeline** - 多版本Python测试
2. **Code Quality** - 代码质量和格式检查
3. **Security Scan** - 安全漏洞扫描
4. **Performance Tests** - 性能和负载测试
5. **Docker Build** - 容器化构建测试

所有检查必须通过才能合并PR。

## 🤔 常见问题

### Q: Pre-commit钩子失败怎么办？

A: 运行以下命令修复：
```bash
make format          # 自动格式化
make lint           # 检查具体问题
git add .
git commit -m "fix: resolve pre-commit issues"
```

### Q: 如何跳过某个pre-commit检查？

A: 不建议跳过检查。如有特殊情况：
```bash
git commit -m "message" --no-verify
```

### Q: 如何更新pre-commit钩子？

A: 
```bash
make update-deps
pre-commit autoupdate
```

### Q: Docker构建很慢怎么办？

A: 使用CI专用的轻量级镜像：
```bash
make docker-ci  # 使用Dockerfile.ci，构建更快
```

## 📞 获得帮助

- 查看现有的[Issues](https://github.com/YOUR_USERNAME/jmeter_toolit/issues)
- 创建新的Issue描述问题
- 查看项目文档和代码注释
- 联系维护者

## 🎯 项目目标

JMeter Toolkit致力于成为：
- **易用性**：简单直观的API设计
- **可靠性**：高测试覆盖率和安全性
- **性能**：高效的异步处理
- **可维护性**：清晰的代码结构和文档

感谢您的贡献！🎉