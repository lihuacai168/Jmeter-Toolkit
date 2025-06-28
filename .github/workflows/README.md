# GitHub Actions Workflows

This directory contains all the GitHub Actions workflows for the JMeter Toolkit project.

## 🔄 Workflows Overview

### 1. **CI/CD Pipeline** (`ci.yml`)
**Triggers**: Push to main branches, Pull requests, feature branches
- ✅ **Multi-Python Testing** (3.9, 3.10, 3.11, 3.12)
- 🧪 **Full Test Suite** with coverage reporting
- 🔍 **Code Quality Checks** (flake8, black, isort, mypy, pylint)
- 📊 **Complexity Analysis** (radon)
- 🔒 **Security Scanning** (bandit, safety, pip-audit)
- 🐳 **Docker Build Testing**
- 🔗 **Integration Tests** with Docker Compose
- 📦 **Deployment Readiness Check**

### 2. **Release Management** (`release.yml`)
**Triggers**: Version tags (v*), Manual trigger
- 🏷️ **Automated Release Creation**
- 📦 **Release Package Generation**
- 🐳 **Docker Image Building**
- 📋 **Release Notes Generation**
- 📤 **Asset Upload** (tar.gz, zip, docker)

### 3. **Docker Image Build & Push** (`build_and_push_image.yml`)
**Triggers**: Push to main branches, Manual trigger
- 🐳 **Multi-architecture Docker builds**
- 📤 **Push to Docker registry**
- 🏷️ **Automated tagging**

### 4. **Dependency Updates** (`dependency-update.yml`)
**Triggers**: Weekly schedule, Manual trigger
- 🔄 **Automated Dependency Updates**
- 🔒 **Security Vulnerability Scanning**
- 📝 **Update Report Generation**
- 🔀 **Automated Pull Request Creation**

## 📊 Status Badges

Add these badges to your main README.md:

```markdown
![CI/CD Pipeline](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/CI/CD%20Pipeline/badge.svg)
![Docker Build](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Build%20and%20Push%20Image/badge.svg)
![Release](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Release/badge.svg)
![Dependency Update](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Dependency%20Update/badge.svg)
```

## 🔧 Configuration Files

The workflows use these configuration files:
- `pyproject.toml` - Python dependencies, project configuration, and tool settings
- `uv.lock` - UV dependency lockfile for reproducible builds
- `Dockerfile` - Production Docker image build
- `Dockerfile.ci` - CI-specific Docker image with test dependencies
- `docker-compose.yml` - Production environment setup
- `docker-compose.ci.yml` - CI testing environment

## ⚡ Modern Features

### UV Dependency Management
All workflows use **UV** for fast and reliable dependency management:
- 🚀 **Faster installs** compared to pip
- 🔒 **Lockfile support** for reproducible builds
- 📦 **Virtual environment management**
- 🔄 **Fallback mechanisms** for locked/unlocked dependencies

### Multi-stage Docker Builds
- 🏗️ **Builder stage** for compilation and dependency installation
- 🐳 **Runtime stage** with minimal dependencies
- 📦 **Cached layers** for faster builds
- 🔒 **Security-focused** with non-root user

### Enhanced Quality Gates
- 📊 **Complexity analysis** with detailed reports
- 🔍 **Multi-tool linting** (flake8, pylint, mypy)
- 🔒 **Security scanning** (bandit, safety, pip-audit)
- 📈 **Coverage reporting** with Codecov integration

## 🚀 Triggering Workflows

### Automatic Triggers
- **Push to main/master/develop**: Runs CI/CD Pipeline and Docker Build
- **Push to feature branches**: Runs CI/CD Pipeline (all jobs)
- **Pull Requests**: Runs full CI/CD Pipeline with all quality checks
- **Weekly Schedule**: Runs Dependency Updates
- **Version Tags**: Runs Release workflow

### Manual Triggers
All workflows can be triggered manually through the GitHub Actions interface:
1. Go to the **Actions** tab in your repository
2. Select the workflow you want to run
3. Click **Run workflow**
4. Choose the branch and any required inputs

## 📋 Requirements

### Secrets Required
- `GITHUB_TOKEN` (automatically provided)

### Optional Secrets
- `CODECOV_TOKEN` (for code coverage reporting)
- `DOCKER_HUB_USERNAME` and `DOCKER_HUB_TOKEN` (for Docker registry)

## 🛠️ Customization

### Adding New Tests
1. Add test files to the `tests/` directory
2. Tests will automatically run in the CI pipeline

### Modifying Python Versions
Edit the `matrix.python-version` in `ci.yml`:
```yaml
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11, 3.12]
```

### Changing Schedule
Modify the `cron` expression in workflow files:
```yaml
schedule:
  - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
```

### Adding Environment Variables
Add to the workflow file:
```yaml
env:
  MY_VARIABLE: value
```

## 🔍 Monitoring

### Viewing Results
- **Actions Tab**: See all workflow runs and their status
- **Artifacts**: Download test reports, coverage reports, and logs
- **Checks**: See status on Pull Requests

### Notifications
- **Email**: GitHub sends notifications for failed workflows
- **Status Checks**: Required checks prevent merging with failures
- **Slack/Discord**: Can be integrated with webhooks

## 🐛 Troubleshooting

### Common Issues

1. **Tests Failing**: Check the test logs in the Actions tab
2. **UV Dependencies**: Update `uv.lock` if dependency issues occur, run `uv lock`
3. **Python Version**: Ensure compatibility with all tested versions (3.9-3.12)
4. **Docker Build**: Check Dockerfile syntax and UV installation
5. **Lock File Sync**: If dependencies change, run `uv sync` locally and commit `uv.lock`
6. **Permission Issues**: Check Docker user permissions in multi-stage builds

### Debug Mode
Add this to any workflow step for debugging:
```yaml
- name: Debug
  run: |
    echo "Debug information"
    env
    ls -la
```

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Marketplace Actions](https://github.com/marketplace?type=actions)