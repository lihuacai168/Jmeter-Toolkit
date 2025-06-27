# GitHub Actions Workflows

This directory contains all the GitHub Actions workflows for the JMeter Toolkit project.

## 🔄 Workflows Overview

### 1. **CI/CD Pipeline** (`ci.yml`)
**Triggers**: Push to main branches, Pull requests
- ✅ **Multi-Python Testing** (3.9, 3.10, 3.11, 3.12)
- 🧪 **Full Test Suite** with coverage reporting
- 🐳 **Docker Build Testing**
- 🔗 **Integration Tests** with PostgreSQL
- 📦 **Deployment Readiness Check**

### 2. **Code Quality** (`code-quality.yml`)
**Triggers**: Push to main branches, Pull requests
- 🔍 **Linting** (flake8, pylint)
- 🎨 **Code Formatting** (black, isort)
- 🏷️ **Type Checking** (mypy)
- 📊 **Complexity Analysis** (radon)
- 🔒 **Dependency Security** (safety, pip-audit)

### 3. **Performance Tests** (`performance.yml`)
**Triggers**: Weekly schedule, Manual trigger, Main branch changes
- ⚡ **Performance Testing** 
- 🚛 **Load Testing** (Locust)
- 💾 **Memory Usage Monitoring**
- 📈 **Concurrent Request Testing**

### 4. **Release Management** (`release.yml`)
**Triggers**: Version tags (v*), Manual trigger
- 🏷️ **Automated Release Creation**
- 📦 **Release Package Generation**
- 🐳 **Docker Image Building**
- 📋 **Release Notes Generation**
- 📤 **Asset Upload** (tar.gz, zip, docker)

### 5. **Dependency Updates** (`dependency-update.yml`)
**Triggers**: Weekly schedule, Manual trigger
- 🔄 **Automated Dependency Updates**
- 🔒 **Security Vulnerability Scanning**
- 📝 **Update Report Generation**
- 🔀 **Automated Pull Request Creation**

## 📊 Status Badges

Add these badges to your main README.md:

```markdown
![CI/CD](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/CI/CD%20Pipeline/badge.svg)
![Code Quality](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Code%20Quality/badge.svg)
![Security](https://github.com/YOUR_USERNAME/jmeter_toolit/workflows/Security%20Scan/badge.svg)
```

## 🔧 Configuration Files

The workflows use these configuration files:
- `.flake8` - Flake8 linting configuration
- `pyproject.toml` - Python dependencies, project configuration, and tool settings

## 🚀 Triggering Workflows

### Automatic Triggers
- **Push to main/master/develop**: Runs CI/CD and Code Quality
- **Pull Requests**: Runs CI/CD and Code Quality
- **Weekly Schedule**: Runs Performance Tests and Dependency Updates
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
2. **Dependencies**: Update pyproject.toml if imports fail, run `uv pip install -e "."`
3. **Python Version**: Ensure compatibility with all tested versions
4. **Docker Build**: Check Dockerfile syntax and UV installation

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