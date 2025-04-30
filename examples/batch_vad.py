#!/usr/bin/env python3
"""
批量VAD处理示例，用于处理音频文件并提取语音片段。
"""

import argparse
import os
import sys
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


class AudioSegment:
    """语音片段类，保存VAD检测到的语音片段信息"""
    
    def __init__(self, start_time_ms, audio_data, duration_ms):
        self.start_time_ms = start_time_ms
        self.audio_data = audio_data
        self.duration_ms = duration_ms
    
    def __repr__(self):
        return f"语音片段: 开始于{self.start_time_ms}ms, 持续{self.duration_ms}ms"


def process_audio_file(file_path, output_dir=None, config=None):
    """
    处理单个音频文件，提取语音片段
    
    Args:
        file_path: 音频文件路径
        output_dir: 输出目录，如果为None则使用当前目录
        config: VAD配置
        
    Returns:
        检测到的语音片段列表
    """
    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = "."
        
    # 加载音频文件
    waveform, sample_rate = torchaudio.load(file_path)
    
    # 转换为单声道
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    # 重采样到16kHz
    if sample_rate != 16000:
        waveform = F.resample(waveform, sample_rate, 16000)
        sample_rate = 16000
    
    # 转换为numpy数组
    audio_data = waveform.squeeze().numpy()
    
    # 转换为16位整数
    audio_int16 = float2int(audio_data)
    audio_bytes = audio_int16.tobytes()
    
    # 语音片段列表
    segments = []
    current_position_ms = 0
    
    # 保存和回调函数
    def on_speech_data(data, duration_ms):
        nonlocal segments, current_position_ms
        
        # 创建语音片段
        segment = AudioSegment(
            start_time_ms=max(0, current_position_ms - duration_ms),
            audio_data=data,
            duration_ms=duration_ms
        )
        segments.append(segment)
        
        # 保存为WAV文件
        file_name = Path(file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{file_name}_{timestamp}.wav")
        
        # 转换为int16数组
        audio_int16 = np.frombuffer(data, dtype=np.int16)
        
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16位 = 2字节
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())
            
        print(f"保存语音片段: {output_file}, 时长: {duration_ms}ms")
    
    # 创建VAD配置
    vad_config = config if config else VadConfig()
    
    # 创建VAD检测器
    detector = RealTimeVadDetector(
        config=vad_config,
        on_speech_data=on_speech_data,
        on_start_speaking=lambda: print("检测到语音开始")
    )
    
    # 设置批处理的块大小
    chunk_size = 1600  # 100ms at 16kHz
    
    try:
        # 启动VAD检测
        detector.start_detect()
        
        # 分块处理音频数据
        for i in range(0, len(audio_bytes), chunk_size * 2):  # *2因为每个采样点占2字节
            end = min(i + chunk_size * 2, len(audio_bytes))
            chunk = audio_bytes[i:end]
            
            # 喂入音频数据
            detector.put_pcm_data(chunk)
            
            # 更新当前位置
            current_position_ms = (i // 2) / 16  # 转换为毫秒
            
        # 等待处理完成
        import time
        time.sleep(0.5)
        
    finally:
        # 关闭资源
        detector.close()
    
    return segments


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="VAD音频批处理工具")
    parser.add_argument("files", nargs="+", help="要处理的音频文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default="vad_outputs")
    parser.add_argument("--threshold", "-t", type=float, help="语音检测阈值", default=0.8)
    args = parser.parse_args()
    
    # 创建VAD配置
    config = VadConfig(
        positive_speech_threshold=args.threshold,
        negative_speech_threshold=args.threshold * 0.4,
    )
    
    # 处理每个文件
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"警告: 文件 '{file_path}' 不存在，已跳过")
            continue
            
        print(f"处理文件: {file_path}")
        segments = process_audio_file(file_path, args.output, config)
        print(f"检测到 {len(segments)} 个语音片段")
        print("-" * 50)


if __name__ == "__main__":
    main() 