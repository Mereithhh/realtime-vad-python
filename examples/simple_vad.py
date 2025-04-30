#!/usr/bin/env python3
"""
简单的实时VAD检测示例，使用torchaudio进行音频处理。
"""

import os
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torchaudio
import torchaudio.functional as F

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from realtime_vad import RealTimeVadDetector, VadConfig
from realtime_vad.utils import float2int


def on_speech_data(audio_data: bytes, duration_ms: int):
    """语音数据回调函数"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"speech_{timestamp}.wav"
    
    print(f"检测到语音片段，时长：{duration_ms}ms，保存为：{filename}")
    
    # 将字节数据转换为int16数组
    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
    
    # 保存为WAV文件
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16位 = 2字节
        wf.setframerate(16000)
        wf.writeframes(audio_int16.tobytes())


def on_start_speaking():
    """开始说话的回调函数"""
    print("检测到开始说话")


def simulate_streaming(audio_file, chunk_size=512, sample_rate=16000):
    """
    模拟实时流式音频，从文件中读取并分块返回
    
    Args:
        audio_file: 音频文件路径
        chunk_size: 每次返回的采样点数
        sample_rate: 目标采样率
        
    Yields:
        音频数据块
    """
    # 读取音频文件
    waveform, orig_sample_rate = torchaudio.load(audio_file)
    
    # 转换为单声道
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    # 重采样到目标采样率
    if orig_sample_rate != sample_rate:
        waveform = F.resample(waveform, orig_sample_rate, sample_rate)
    
    # 分块处理
    waveform = waveform.squeeze().numpy()
    total_samples = len(waveform)
    
    for i in range(0, total_samples, chunk_size):
        chunk = waveform[i:min(i+chunk_size, total_samples)]
        
        # 如果最后一块不足，用0填充
        if len(chunk) < chunk_size:
            padded_chunk = np.zeros(chunk_size, dtype=np.float32)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk
        
        # 转换为int16格式
        chunk_int16 = float2int(chunk)
        
        # 模拟处理延迟
        time.sleep(chunk_size / sample_rate)  # 按实时速度处理
        
        yield chunk_int16.tobytes()


def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python simple_vad.py <音频文件绝对路径>")
        return
    
    audio_file = sys.argv[1]
    if not Path(audio_file).exists():
        print(f"错误: 音频文件 '{audio_file}' 不存在")
        return
    
    # 创建VAD配置
    config = VadConfig(
        positive_speech_threshold=0.8,  # 调整语音检测阈值
        negative_speech_threshold=0.3,
        redemption_frames=6, # 至少需要6帧连续置信度小于0.3才算结束（6x32ms=192ms）
    )
    
    # 创建VAD检测器
    detector = RealTimeVadDetector(
        config=config,
        on_speech_data=on_speech_data,
        on_start_speaking=on_start_speaking
    )
    
    # 启动VAD检测线程
    detector.start_detect()
    
    # 设置音频参数
    CHUNK = 512  # 约100ms
    SAMPLE_RATE = 16000
    
    print(f"开始处理音频文件: {audio_file}")
    
    try:
        # 模拟实时流处理
        for audio_chunk in simulate_streaming(audio_file, CHUNK, SAMPLE_RATE):
            # 将音频数据送入VAD检测器
            detector.put_pcm_data(audio_chunk)
            
    except KeyboardInterrupt:
        print("处理被中断")
    except Exception as e:
        print(f"处理错误: {e}")
    finally:
        # 关闭资源
        detector.close()
        print("处理完成")


if __name__ == "__main__":
    main() 