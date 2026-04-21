# EasyBot 开发常用指令

## 代码格式化

```bash
black .
isort . --profile=black
```

## 代码质量检查

### Lint 检查

```bash
flake8 easybot --max-line-length=88 --extend-ignore=E203,W503
```

### 类型检查

```bash
mypy easybot
```

### 运行测试

```bash
pytest                      # 基础测试
pytest -v                   # 详细输出
pytest --cov=easybot        # 带覆盖率
```

## 虚拟环境

### 创建虚拟环境

```bash
python -m venv .venv
```

### 激活虚拟环境

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

### 安装依赖

```bash
pip install -e .            # 开发模式安装
pip install -e ".[dev]"     # 包含开发依赖
```

## Git 常用操作

### 提交代码

```bash
git add .
git commit -m "feat: 描述"
git push
```

### 分支操作

```bash
git checkout -b feature/xxx     # 创建并切换分支
git merge main                  # 合并 main 到当前分支
```

## 文档

### 本地预览 VuePress 文档

```bash
cd docs && npm install && npm run dev
```

## 发布 PyPI

### GitHub Actions 自动发布（推荐）

项目已配置 `.github/workflows/publish.yml`，使用 Trusted Publishing 方式自动发布。

#### 1. 在 PyPI 上配置 Trusted Publisher

- 登录 https://pypi.org/manage/project/easybot-qq/settings/publishing/
- 添加新的 Trusted Publisher：
  - PyPI Project Name: `easybot-qq`
  - Owner: `SaucePlum`
  - Repository name: `easybot`
  - Workflow name: `publish.yml`
  - Environment name: (留空)

#### 2. 创建 GitHub Release 触发发布

**使用 GitHub CLI（推荐）：**

```bash
gh release create v1.0.0 --title "v1.0.0" --notes "发布说明内容"
```

**常用选项：**

```bash
gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG.md  # 从文件读取说明
gh release create v1.0.0 --draft                                      # 创建草稿
gh release create v1.0.0 --prerelease                                 # 创建预发布
gh release create v1.0.0 ./dist/*                                     # 附带构建产物
```

**或使用 git tag + 网页创建：**

```bash
git tag v1.0.0
git push origin v1.0.0
# 然后在 GitHub 网页上创建 Release
```

### 本地手动发布

```bash
# 1. 安装构建工具
pip install build twine

# 2. 构建包
python -m build

# 3. 检查包
twine check dist/*

# 4. 上传到 TestPyPI (测试)
twine upload --repository testpypi dist/*

# 5. 上传到 PyPI (正式)
twine upload dist/*
```

### 版本号更新

修改 `easybot/version.py` 中的 `__version__` 变量。


### skills打包指令

```bash
tar -cvf easybot-assistant.skill -C .trae/skills easybot-assistant
```