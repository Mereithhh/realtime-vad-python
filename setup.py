#!/usr/bin/env python3
"""
Python实时VAD检测库安装脚本
"""

import os
from setuptools import setup, find_packages

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="realtime-vad-python",
    version="0.1.1",
    description="Python实时VAD检测库，基于Silero VAD模型",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mereith",
    author_email="wanglu@mereith.com",
    url="https://github.com/mereithhh/realtime-vad-python",
    packages=find_packages(exclude=["examples", "tests"]),
    package_data={
        "realtime_vad": ["files/*.jit"],  # 包含realtime_vad包内的模型文件
    },
    include_package_data=True,
    install_requires=[
        "numpy",
        "torch>=1.13.0",
        "torchaudio>=0.13.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "isort",
            "flake8",
            "build",
            "twine",
        ],
        "examples": [
            "pyaudio",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
) 