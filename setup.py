#!/usr/bin/env python3
"""
Python实时VAD检测库安装脚本
"""

from setuptools import setup, find_packages

setup(
    name="realtime-vad-python",
    version="0.1.0",
    description="Python实时VAD检测库，基于Silero VAD模型",
    author="Mereith",
    packages=find_packages(exclude=["examples", "tests"]),
    install_requires=[
        "numpy",
        "torch",
        "torchaudio",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
) 