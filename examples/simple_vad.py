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
import pyaudio

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
    # 初始化VAD检测器，使用默认内置模型
    detector = RealTimeVadDetector(
        on_speech_data=on_speech_data,
        on_start_speaking=on_start_speaking,
        use_default_model=True  # 使用默认内置模型
    )
    
    # 启动VAD检测
    detector.start_detect()
    
    # 设置PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=512
    )
    
    print("开始录音和VAD检测，按Ctrl+C结束...")
    
    try:
        while True:
            # 读取音频数据
            data = stream.read(512)
            # 将数据送入VAD检测器
            detector.put_pcm_data(data)
            time.sleep(0.01)  # 防止CPU占用过高
    except KeyboardInterrupt:
        print("程序结束")
    finally:
        # 清理资源
        stream.stop_stream()
        stream.close()
        p.terminate()
        detector.close()


if __name__ == "__main__":
    main() 