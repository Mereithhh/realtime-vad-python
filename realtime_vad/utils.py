"""
工具函数模块，提供音频处理相关的辅助函数。
"""

import numpy as np


def int2float(sound: np.ndarray) -> np.ndarray:
    """
    将int16格式的音频转换为float32格式
    
    Args:
        sound: int16格式的音频数据
        
    Returns:
        float32格式的音频数据，范围为[-1, 1]
    """
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768  # 归一化到[-1, 1]
    sound = sound.squeeze()
    return sound


def float2int(sound: np.ndarray) -> np.ndarray:
    """
    将float32格式的音频转换为int16格式
    
    Args:
        sound: float32格式的音频数据，范围为[-1, 1]
        
    Returns:
        int16格式的音频数据
    """
    sound = np.clip(sound, -1.0, 1.0)
    sound = sound * 32767
    sound = sound.astype(np.int16)
    return sound 