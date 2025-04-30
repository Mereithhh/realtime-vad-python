#!/usr/bin/env python3
"""
下载Silero VAD模型并保存为JIT格式
"""

import os
import pathlib
import torch

# 获取当前目录路径
SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
MODEL_DIR = os.path.join(PROJECT_ROOT, "realtime_vad", "files")
MODEL_PATH = os.path.join(MODEL_DIR, "silero_vad.jit")

def download_and_save_model():
    """下载Silero VAD模型并保存为JIT格式"""
    # 确保目录存在
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("正在从torch hub下载Silero VAD模型...")
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=True
    )
    
    # 将模型保存为JIT格式
    print(f"将模型保存到 {MODEL_PATH}")
    torch.jit.save(torch.jit.script(model), MODEL_PATH)
    print("模型下载并保存完成!")

if __name__ == "__main__":
    download_and_save_model() 