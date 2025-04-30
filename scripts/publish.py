#!/usr/bin/env python3
"""
打包并发布realtime-vad-python到PyPI
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")

def clean():
    """清理构建目录"""
    print("清理旧的构建文件...")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    
    # 删除所有 __pycache__ 目录
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            print(f"删除: {cache_dir}")
            shutil.rmtree(cache_dir)
            
    # 删除 .egg-info 目录
    for item in os.listdir(PROJECT_ROOT):
        if item.endswith(".egg-info"):
            egg_info_dir = os.path.join(PROJECT_ROOT, item)
            print(f"删除: {egg_info_dir}")
            shutil.rmtree(egg_info_dir)

def build():
    """构建源代码分发包和wheel包"""
    print("构建分发包...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build"], check=True)
    subprocess.run([sys.executable, "-m", "build"], cwd=PROJECT_ROOT, check=True)

def upload_test():
    """上传到TestPyPI进行测试"""
    print("上传到TestPyPI...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "twine"], 
        check=True
    )
    # 使用 --skip-existing 选项避免重复上传错误，添加 --verbose 获取更多错误信息
    try:
        subprocess.run(
            [sys.executable, "-m", "twine", "upload", "--repository", "testpypi", 
             "--skip-existing", "--verbose", "dist/*"], 
            cwd=PROJECT_ROOT,
            check=True
        )
        print("测试版本已上传到 TestPyPI")
        print("可以使用以下命令安装测试版本:")
        print("pip install --index-url https://test.pypi.org/simple/ realtime-vad-python")
    except subprocess.CalledProcessError:
        print("\n上传失败。可能的原因：")
        print("1. API 令牌认证问题 - 请检查你的 ~/.pypirc 文件")
        print("2. 同版本包已存在 - 尝试更新版本号")
        print("3. 包名已被占用 - 尝试更改包名")
        print("\n要使用 API 令牌认证，可添加环境变量:")
        print("export TWINE_USERNAME=__token__")
        print("export TWINE_PASSWORD=你的API令牌")
        sys.exit(1)

def upload_prod():
    """上传到PyPI"""
    print("上传到PyPI...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "twine"], 
        check=True
    )
    try:
        subprocess.run(
            [sys.executable, "-m", "twine", "upload", "--skip-existing", "--verbose", "dist/*"], 
            cwd=PROJECT_ROOT,
            check=True
        )
        print("已成功上传到PyPI!")
        print("可以使用以下命令安装:")
        print("pip install realtime-vad-python")
    except subprocess.CalledProcessError:
        print("\n上传失败。可能的原因：")
        print("1. API 令牌认证问题 - 请检查你的 ~/.pypirc 文件")
        print("2. 同版本包已存在 - 尝试更新版本号")
        print("3. 包名已被占用 - 尝试更改包名")
        print("\n要使用 API 令牌认证，可添加环境变量:")
        print("export TWINE_USERNAME=__token__")
        print("export TWINE_PASSWORD=你的API令牌")
        sys.exit(1)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python publish.py [clean|build|test|prod|all]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "clean":
        clean()
    elif action == "build":
        build()
    elif action == "test":
        upload_test()
    elif action == "prod":
        upload_prod()
    elif action == "all":
        clean()
        build()
        upload_prod()
    else:
        print(f"未知操作: {action}")
        print("可用操作: clean, build, test, prod, all")
        sys.exit(1)

if __name__ == "__main__":
    main() 