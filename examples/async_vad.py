#!/usr/bin/env python3
"""
异步实时VAD检测示例，使用asyncio处理音频流。
"""

import argparse
import asyncio
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


class AsyncVadProcessor:
    """异步VAD处理器，封装RealTimeVadDetector以便在异步环境中使用"""
    
    def __init__(self, config=None, output_dir=None):
        """
        初始化异步VAD处理器
        
        Args:
            config: VAD配置
            output_dir: 输出目录
        """
        self.config = config or VadConfig()
        self.output_dir = output_dir or "."
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建事件队列，用于处理VAD回调
        self.speech_queue = asyncio.Queue()
        
        # 创建VAD检测器
        self.detector = RealTimeVadDetector(
            config=self.config,
            on_speech_data=self._on_speech_data,
            on_start_speaking=self._on_start_speaking
        )
        
        self.last_segment_time = datetime.now()
        self.is_speaking = False
    
    def _on_speech_data(self, audio_data, duration_ms):
        """语音数据回调函数"""
        # 将检测到的语音放入队列
        asyncio.run_coroutine_threadsafe(
            self.speech_queue.put((audio_data, duration_ms)),
            asyncio.get_event_loop()
        )
    
    def _on_start_speaking(self):
        """开始说话的回调函数"""
        self.is_speaking = True
        self.last_segment_time = datetime.now()
    
    async def process_audio_stream(self, audio_stream_generator, sample_rate=16000):
        """
        处理音频流
        
        Args:
            audio_stream_generator: 音频数据生成器，产生float32或int16格式的数据
            sample_rate: 采样率
        """
        # 启动VAD检测器
        self.detector.start_detect()
        
        # 启动语音处理任务
        process_task = asyncio.create_task(self._process_speech_segments())
        
        try:
            # 处理音频流
            async for audio_chunk in audio_stream_generator:
                # 如果音频是float32格式，转换为int16
                if isinstance(audio_chunk, np.ndarray) and audio_chunk.dtype == np.float32:
                    audio_chunk = float2int(audio_chunk)
                
                # 如果是numpy数组，转换为字节
                if isinstance(audio_chunk, np.ndarray):
                    audio_chunk = audio_chunk.tobytes()
                
                # 喂入音频数据
                self.detector.put_pcm_data(audio_chunk)
                
                # 让出控制权，使其他协程可以运行
                await asyncio.sleep(0)
                
        finally:
            # 等待处理完所有语音片段
            await asyncio.sleep(1.0)
            
            # 取消处理任务
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass
            
            # 关闭检测器
            self.detector.close()
    
    async def _process_speech_segments(self):
        """处理语音片段的后台任务"""
        while True:
            # 从队列获取语音片段
            audio_data, duration_ms = await self.speech_queue.get()
            
            # 保存语音片段
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"speech_{timestamp}.wav")
            
            # 转换为int16数组
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
            
            # 保存为WAV文件
            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16位 = 2字节
                wf.setframerate(16000)
                wf.writeframes(audio_int16.tobytes())
            
            print(f"保存语音片段: {output_file}, 时长: {duration_ms}ms")
            
            # 标记任务完成
            self.speech_queue.task_done()


async def file_audio_stream(file_path, chunk_size=512, sample_rate=16000):
    """
    从文件创建音频流生成器
    
    Args:
        file_path: 音频文件路径
        chunk_size: 块大小（采样点数，默认512约32ms@16kHz）
        sample_rate: 目标采样率
        
    Yields:
        音频数据块（字节格式）
    """
    # 加载音频文件
    waveform, orig_sample_rate = torchaudio.load(file_path)
    
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
        
        # 转换为int16并返回
        chunk_int16 = float2int(chunk)
        
        # 模拟实时处理延迟
        chunk_duration = chunk_size / sample_rate
        await asyncio.sleep(chunk_duration / 2)  # 使处理速度稍快于实时
        
        yield chunk_int16.tobytes()


async def async_main():
    """异步主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="异步VAD处理示例")
    parser.add_argument("file", help="要处理的音频文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default="async_vad_outputs")
    parser.add_argument("--threshold", "-t", type=float, help="语音检测阈值", default=0.8)
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"错误: 音频文件 '{args.file}' 不存在")
        return
    
    # 创建VAD配置
    config = VadConfig(
        positive_speech_threshold=args.threshold,
        negative_speech_threshold=args.threshold * 0.4,
        min_speech_frames=2,  # 降低最小语音帧数，使检测更敏感
        frame_samples=512,  # 确保与Silero VAD模型兼容 (32ms at 16kHz)
    )
    
    # 创建异步VAD处理器
    processor = AsyncVadProcessor(config=config, output_dir=args.output)
    
    print(f"开始处理音频文件: {args.file}")
    print(f"VAD阈值: {args.threshold}")
    print(f"输出目录: {args.output}")
    print("---------------------------------------")
    
    # 创建音频流
    audio_stream = file_audio_stream(args.file)
    
    # 处理音频流
    await processor.process_audio_stream(audio_stream)
    
    print("处理完成")


def main():
    """主函数"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main() 