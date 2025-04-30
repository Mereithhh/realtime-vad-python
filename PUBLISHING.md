# 发布指南

本文档详细说明了如何将 realtime-vad-python 包发布到 PyPI。

## 先决条件

在发布之前，请确保你已经：

1. 已有 PyPI 帐户（用于正式发布）
2. 已有 TestPyPI 帐户（用于测试发布）
3. 安装了必要的工具：`pip install build twine`

## 配置 PyPI 凭据

为了避免每次上传时输入用户名和密码，你可以在 `~/.pypirc` 文件中配置你的凭据：

```
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = your_username
password = your_password

[testpypi]
repository = https://test.pypi.org/legacy/
username = your_username
password = your_password
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

- 确保内置模型文件存在于 `files` 目录中
- 确保 `MANIFEST.in` 文件正确配置，以包含所有必要文件
- 发布前确保已在虚拟环境中测试安装和功能 