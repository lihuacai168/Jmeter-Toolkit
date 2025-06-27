# GitHub Actions 集成测试指南

## 🎯 总览

项目现已配置完整的 GitHub Actions CI/CD 流水线，包含 5 个主要工作流，确保代码质量、安全性和部署准备。

## 🔄 工作流详情

### 1. **CI/CD 流水线** (`ci.yml`)
![CI/CD](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/CI/CD%20Pipeline/badge.svg)

**触发条件**: 
- Push 到 main/master/develop/feature/* 分支
- Pull Request 到 main/master/develop 分支

**功能**:
- ✅ **多版本 Python 测试** (3.9, 3.10, 3.11, 3.12)
- 🧪 **完整测试套件** (30个测试用例)
- 📊 **代码覆盖率报告** (上传到 Codecov)
- 🐳 **Docker 构建测试**
- 🔗 **PostgreSQL 集成测试**
- 📦 **部署就绪检查**

### 2. **代码质量** (`code-quality.yml`)
![Code Quality](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Code%20Quality/badge.svg)

**触发条件**: Push 和 Pull Request

**功能**:
- 🔍 **代码检查** (flake8, pylint)
- 🎨 **格式化检查** (black, isort)
- 🏷️ **类型检查** (mypy)
- 📊 **复杂度分析** (radon)
- 🔒 **依赖安全扫描** (safety, pip-audit)

### 3. **性能测试** (`performance.yml`)
![Performance](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Performance%20Tests/badge.svg)

**触发条件**: 
- 每周一凌晨 2 点 (UTC)
- 手动触发
- main 分支的核心文件变更

**功能**:
- ⚡ **性能基准测试**
- 🚛 **负载测试** (使用 Locust)
- 💾 **内存使用监控**
- 📈 **并发请求测试** (10个并发用户)

### 4. **发布管理** (`release.yml`)
![Release](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Release/badge.svg)

**触发条件**:
- 版本标签推送 (v1.0.0, v2.1.0 等)
- 手动触发

**功能**:
- 🏷️ **自动发布创建**
- 📦 **发布包生成** (tar.gz, zip)
- 🐳 **Docker 镜像构建**
- 📋 **发布说明生成**
- 📤 **资源上传**

### 5. **依赖更新** (`dependency-update.yml`)
![Dependencies](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Dependency%20Updates/badge.svg)

**触发条件**:
- 每周一上午 9 点 (UTC)
- 手动触发

**功能**:
- 🔄 **自动依赖更新**
- 🔒 **安全漏洞扫描**
- 📝 **更新报告生成**
- 🔀 **自动创建 Pull Request**

## 📋 状态检查

### 必需检查
- ✅ CI/CD Pipeline
- ✅ Code Quality
- ✅ Security Scan

### 可选检查
- 📊 Performance Tests (手动/定期)
- 🔄 Dependency Updates (自动 PR)

## 🚀 使用指南

### 开发流程
1. **创建分支**: `git checkout -b feature/your-feature`
2. **开发代码**: 编写功能和测试
3. **提交变更**: `git commit -m "feat: add new feature"`
4. **推送分支**: `git push origin feature/your-feature`
5. **创建 PR**: GitHub 会自动运行 CI/CD
6. **等待检查**: 所有检查通过后可合并

### 发布流程
1. **更新版本**: 更新 `config/settings.py` 中的版本号
2. **提交变更**: `git commit -m "chore: bump version to v1.0.0"`
3. **创建标签**: `git tag v1.0.0`
4. **推送标签**: `git push origin v1.0.0`
5. **自动发布**: GitHub Actions 会自动创建发布

### 手动触发
在 GitHub 的 **Actions** 标签页:
1. 选择要运行的工作流
2. 点击 **Run workflow**
3. 选择分支和参数
4. 点击绿色的 **Run workflow** 按钮

## 📊 监控和报告

### 报告位置
- **测试报告**: Actions 页面的 Artifacts 部分
- **覆盖率报告**: Codecov (如果配置)
- **安全报告**: Security 标签页
- **性能报告**: Actions Artifacts

### 通知设置
- **失败通知**: GitHub 会发送邮件通知
- **状态徽章**: 在 README.md 中显示状态
- **PR 检查**: 阻止有问题的代码合并

## 🔧 配置文件

### 工作流配置
- `.github/workflows/ci.yml` - 主要 CI/CD 流水线
- `.github/workflows/code-quality.yml` - 代码质量检查
- `.github/workflows/performance.yml` - 性能测试
- `.github/workflows/release.yml` - 发布管理
- `.github/workflows/dependency-update.yml` - 依赖更新

### 工具配置
- `.flake8` - Flake8 代码检查配置
- `pyproject.toml` - Black, isort, mypy, pytest 配置
- `requirements.txt` - Python 依赖

## 🛠️ 自定义配置

### 添加新的 Python 版本
编辑 `ci.yml` 中的矩阵:
```yaml
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11, 3.12, 3.13]
```

### 修改测试计划
编辑 `performance.yml` 中的计划:
```yaml
schedule:
  - cron: '0 2 * * 1'  # 每周一凌晨 2 点
```

### 添加环境变量
在工作流文件中添加:
```yaml
env:
  CUSTOM_VAR: value
```

## 🔍 故障排除

### 常见问题
1. **测试失败**: 检查 Actions 页面的详细日志
2. **依赖问题**: 更新 `requirements.txt`
3. **Docker 构建失败**: 检查 `Dockerfile` 语法
4. **代码质量问题**: 运行本地 flake8/black 检查

### 调试技巧
在工作流步骤中添加调试信息:
```yaml
- name: Debug Info
  run: |
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    ls -la
    env | grep -E "(GITHUB_|PYTHON_)"
```

## 📈 最佳实践

### 代码质量
- ✅ 保持 flake8 检查通过
- ✅ 使用 black 格式化代码
- ✅ 编写单元测试
- ✅ 保持测试覆盖率 > 40%

### 安全性
- ✅ 定期更新依赖
- ✅ 运行安全扫描
- ✅ 不提交敏感信息
- ✅ 使用环境变量存储配置

### 性能
- ✅ 监控应用性能
- ✅ 定期运行负载测试
- ✅ 优化慢查询和API
- ✅ 监控内存使用

## 📚 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [工作流语法](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions 市场](https://github.com/marketplace?type=actions)
- [Codecov 集成](https://codecov.io/)
- [Dependabot 配置](https://docs.github.com/en/code-security/dependabot)

---

🎉 **恭喜！** 你的项目现在有了完整的 CI/CD 流水线！