# 手动发布指南

以下是在不使用脚本的情况下，手动发布 realtime-vad-python 包到 PyPI 的详细步骤。

## 准备工作

1. 注册 PyPI 账号: https://pypi.org/account/register/
2. 注册 TestPyPI 账号: https://test.pypi.org/account/register/
3. 安装必要工具:

```bash
pip install build twine
```

## 步骤 1: 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info
```

## 步骤 2: 构建包

```bash
python -m build
```

这将在 `dist/` 目录下创建 wheel 包和源码包。

## 步骤 3: 上传到 TestPyPI (测试)

使用 API 令牌认证:

1. 访问 https://test.pypi.org/manage/account/token/ 生成 API 令牌
2. 运行以下命令上传:

```bash
python -m twine upload --repository testpypi dist/* --verbose

# 当提示输入用户名时，输入: __token__
# 当提示输入密码时，输入你的 TestPyPI API 令牌
```

3. 测试安装:

```bash
pip install --index-url https://test.pypi.org/simple/ realtime-vad-python
```

## 步骤 4: 上传到 PyPI (正式发布)

1. 访问 https://pypi.org/manage/account/token/ 生成 API 令牌
2. 运行以下命令上传:

```bash
python -m twine upload dist/* --verbose

# 当提示输入用户名时，输入: __token__
# 当提示输入密码时，输入你的 PyPI API 令牌
```

3. 验证发布:

```bash
pip install realtime-vad-python
```

## 常见问题

### 403 Forbidden 错误

如果遇到 403 Forbidden 错误，可能原因包括:

1. API 令牌不正确或过期
2. 包名已被占用
3. 你试图上传一个已经存在的版本

### 包名冲突

如果包名已被占用，你需要更改 `setup.py` 中的包名，例如:

```python
setup(
    name="realtime-vad-python-[你的用户名]",
    # 其他配置...
)
```

### 版本冲突

如果版本号已存在，你需要更新 `setup.py` 中的版本号，例如从 `0.1.1` 更新到 `0.1.2`:

```python
setup(
    # 其他配置...
    version="0.1.2",
    # 其他配置...
)
```

## 版本更新

每次发布新版本时，请务必:

1. 更新 `setup.py` 中的版本号
2. 更新 `README.md` 描述相关变更
3. 确保所有测试通过

## 开发者模式安装

对于开发者，可以使用以下命令在本地安装开发版:

```bash
pip install -e .
``` 