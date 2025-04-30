# 发布指南

本文档详细说明了如何将 realtime-vad-python 包发布到 PyPI。

## 先决条件

在发布之前，请确保你已经：

1. 已有 PyPI 帐户（用于正式发布）：https://pypi.org/account/register/
2. 已有 TestPyPI 帐户（用于测试发布）：https://test.pypi.org/account/register/
3. 安装了必要的工具：`pip install build twine`

## 配置认证方式

有两种方式可以配置 PyPI 认证：

### 方式一：使用 API 令牌（推荐）

1. 访问 PyPI 账户设置，创建 API 令牌：https://pypi.org/manage/account/token/
2. 访问 TestPyPI 账户设置，创建 API 令牌：https://test.pypi.org/manage/account/token/
3. 设置环境变量（每次发布前设置）：

```bash
# 发布到 PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=你的PyPI令牌

# 或发布到 TestPyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=你的TestPyPI令牌
```

### 方式二：使用 .pypirc 文件

在用户主目录创建或编辑 `~/.pypirc` 文件：

```
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = 你的PyPI令牌

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = 你的TestPyPI令牌
```

## 使用脚本发布

我们提供了一个简单的发布脚本来自动化发布过程。

### 清理旧的构建文件

```bash
python scripts/publish.py clean
```

### 构建包

```bash
python scripts/publish.py build
```

### 上传到 TestPyPI 进行测试

```bash
python scripts/publish.py test
```

上传后，你可以使用以下命令测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ realtime-vad-python
```

### 正式发布到 PyPI

确认测试版本工作正常后，可以发布到正式的 PyPI：

```bash
python scripts/publish.py prod
```

### 一键完成所有步骤

如果你已经确认所有内容都没问题，可以一次性完成所有步骤：

```bash
python scripts/publish.py all
```

## 常见问题

### 403 Forbidden 错误

如果遇到 403 错误，通常是由于认证问题，请确保：

1. 使用了正确的 API 令牌
2. 令牌有适当的权限（上传权限）
3. 包名未被占用

### 版本冲突错误

如果遇到版本已存在的错误，请在 `setup.py` 中更新版本号后重试。

## 版本控制

在每次发布新版本之前，请确保：

1. 在 `setup.py` 中更新版本号
2. 在 `README.md` 中更新相关文档
3. 确保所有测试用例通过

## 更新模型文件

如果需要更新内置模型，可以使用以下命令：

```bash
python scripts/download_model.py
```

## 注意事项

- 确保内置模型文件存在于 `realtime_vad/files` 目录中
- 确保 `MANIFEST.in` 文件正确配置，以包含所有必要文件
- 发布前确保已在虚拟环境中测试安装和功能 