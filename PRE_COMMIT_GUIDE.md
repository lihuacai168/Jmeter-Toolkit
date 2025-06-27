# Pre-commit Hooks 使用指南

## 🎯 概述

本项目已配置完整的pre-commit钩子系统，可以在提交前自动检查和修复代码质量问题。

## 🚀 快速开始

### 1. 安装开发环境

```bash
# 自动安装和配置开发环境
./setup_dev.sh

# 或者手动安装
pip install -r requirements-dev.txt
make setup-hooks
```

### 2. 验证安装

```bash
# 检查pre-commit是否正确安装
pre-commit --version

# 运行所有钩子测试
pre-commit run --all-files
```

## 🔧 配置的钩子

### 基础检查
- **trailing-whitespace**: 移除行尾空格
- **end-of-file-fixer**: 确保文件以换行符结尾
- **check-yaml**: 验证YAML文件语法
- **check-json**: 验证JSON文件语法
- **check-added-large-files**: 检查大文件
- **check-merge-conflict**: 检查合并冲突标记
- **debug-statements**: 检查调试语句

### Python代码质量
- **black**: 代码格式化（行长度127字符）
- **isort**: 导入排序（兼容black配置）
- **flake8**: 代码规范检查（配置忽略E203,W503,F401,E402）
- **autoflake**: 移除未使用的导入和变量

## 🎨 使用方式

### 日常开发流程

```bash
# 1. 编写代码
vim main.py

# 2. 格式化代码（可选，钩子会自动执行）
make format

# 3. 运行测试
make test

# 4. 提交代码（钩子自动运行）
git add .
git commit -m "feat: add new feature"
```

### 如果钩子失败

```bash
# 查看具体错误
git commit -m "your message"

# 自动修复格式问题
make format

# 手动修复剩余问题，然后重新提交
git add .
git commit -m "your message"
```

### 跳过钩子（不推荐）

```bash
# 仅在紧急情况下使用
git commit -m "emergency fix" --no-verify
```

## 📋 Make命令

```bash
# 开发环境设置
make dev-setup          # 一键设置开发环境
make install-dev         # 安装开发依赖
make setup-hooks         # 安装pre-commit钩子

# 代码质量
make format              # 格式化代码
make format-check        # 检查代码格式
make lint               # 运行代码检查
make security           # 运行安全检查

# 测试
make test               # 运行测试
make test-cov           # 运行测试并生成覆盖率报告
make test-fast          # 并行运行测试

# CI模拟
make ci-local           # 本地运行完整CI流程
make pre-commit-all     # 运行所有pre-commit钩子
```

## 🔍 代码质量标准

### Black格式化
- 行长度：127字符
- 自动格式化字符串引号
- 自动调整缩进和空行

### isort导入排序
- 按类型分组：标准库 → 第三方库 → 本地模块
- 每组内按字母排序
- 兼容black的配置

### flake8检查
- 最大行长度：127字符
- 忽略的错误：
  - E203: 空格相关（与black冲突）
  - W503: 换行符相关（与black冲突）
  - F401: 未使用导入（由autoflake处理）
  - E402: 导入位置（某些文件需要）

## 🚨 常见问题

### 问题1：钩子运行失败
**解决方案：**
```bash
# 清除pre-commit缓存
rm -rf ~/.cache/pre-commit
pre-commit install --install-hooks
```

### 问题2：格式化后仍有错误
**解决方案：**
```bash
# 手动运行格式化
black . --line-length 127
isort . --profile black --line-length 127
autoflake --in-place --remove-all-unused-imports --recursive .

# 检查剩余问题
flake8 . --max-line-length=127
```

### 问题3：某些文件不需要检查
**解决方案：**
在`.pre-commit-config.yaml`中添加exclude规则：
```yaml
- id: flake8
  exclude: ^(specific_file\.py|folder/.*)
```

## 📈 最佳实践

### 1. 提交前检查
```bash
# 完整的提交前检查流程
make format              # 自动格式化
make lint               # 代码质量检查
make test               # 运行测试
make security           # 安全检查
git add . && git commit -m "message"
```

### 2. 持续集成

#### 本地模拟
```bash
# 模拟CI环境
make ci-local
```

#### 自动化CI (pre-commit.ci)
项目已配置 `pre-commit.ci`，这是一个与 pre-commit 配套的CI/CD应用，它可以：
- **自动修复PR**: 当你提交一个Pull Request时，`pre-commit.ci`会自动运行钩子，并直接将修复提交到你的分支，无需手动拉取和修复。
- **自动更新钩子**: 每周自动检查并更新 `.pre-commit-config.yaml` 中的钩子版本，并创建一个PR。
- **保持代码库整洁**: 确保所有合并到主分支的代码都符合质量标准。

你可以在 `.pre-commit-config.yaml` 文件中看到 `ci:` 部分的配置。

### 3. 团队协作
- 所有开发者都应该安装pre-commit钩子
- 提交信息遵循[Conventional Commits](https://www.conventionalcommits.org/)格式
- 定期更新钩子配置：`pre-commit autoupdate`

## 🔧 自定义配置

### 修改代码格式
编辑`.pre-commit-config.yaml`：
```yaml
- repo: https://github.com/psf/black
  rev: 24.10.0
  hooks:
    - id: black
      args: [--line-length=100]  # 修改行长度
```

### 添加新钩子
```yaml
- repo: https://github.com/pycqa/bandit
  rev: 1.7.9
  hooks:
    - id: bandit
      args: [-r, ., -f, json]
```

## 📚 相关文档

- [Pre-commit官方文档](https://pre-commit.com/)
- [Black代码格式化](https://black.readthedocs.io/)
- [isort导入排序](https://pycqa.github.io/isort/)
- [flake8代码检查](https://flake8.pycqa.org/)
- [项目贡献指南](CONTRIBUTING.md)

## 💡 提示

1. **IDE集成**: 建议在IDE中配置Black和isort，实时格式化
2. **Git别名**: 设置有用的Git别名简化工作流
3. **定期更新**: 定期运行`pre-commit autoupdate`更新钩子版本
4. **团队同步**: 确保团队成员使用相同的pre-commit配置

---

通过proper使用pre-commit钩子，可以显著提高代码质量，减少代码审查时间，确保团队代码风格一致。