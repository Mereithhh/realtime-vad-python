"""
实时语音活动检测(VAD)模块，基于Silero VAD模型实现。
"""

import threading
import time
import os
import pathlib
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np
import torch

from .audio_cache import AudioCache

# 获取模型默认路径
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(PACKAGE_DIR, "files", "silero_vad.jit")

@dataclass
class VadConfig:
    """VAD配置参数"""
    positive_speech_threshold: float = 0.85  # 语音检测的正阈值
    negative_speech_threshold: float = 0.35  # 语音检测的负阈值
    redemption_frames: int = 8  # 保留多少帧再判断是否真正结束语音 (8 * 32ms = 256ms)
    min_speech_frames: int = 3  # 最少需要多少帧才算有效语音 (3 * 64ms = 192ms)
    pre_speech_pad_frames: int = 1  # 在语音前额外加入多少帧
    frame_samples: int = 512  # 每帧采样点数 (32ms at 16kHz)
    vad_interval: float = 0.032  # VAD检测间隔，单位秒


class RealTimeVadDetector:
    """实时语音活动检测器"""

    def __init__(
        self, 
        config: Optional[VadConfig] = None, 
        on_speech_data: Optional[Callable[[bytes, int], None]] = None,
        on_start_speaking: Optional[Callable[[], None]] = None,
        model_path: Optional[str] = None,
        use_default_model: bool = True
    ):
        """
        初始化实时VAD检测器
        
        Args:
            config: VAD配置，如果为None则使用默认配置
            on_speech_data: 当检测到语音片段时的回调函数，接收音频数据和时长(ms)
            on_start_speaking: 当检测到开始说话时的回调函数
            model_path: 模型路径，如果为None则使用默认内置模型或从torch hub下载
            use_default_model: 是否使用默认内置模型，设为False则从torch hub下载
        """
        self.config = config if config else VadConfig()
        self.on_speech_data = on_speech_data
        self.on_start_speaking = on_start_speaking
        
        # 初始化模型
        self._init_model(model_path, use_default_model)
        
        # 初始化音频缓存
        self.input_audio_cache = AudioCache()
        self.vad_audio_cache = AudioCache()
        
        # VAD状态
        self.vad_not_speaking_frames: List[bytes] = []
        self.vad_not_pass_chunk_size: int = 0
        self.is_vad_speaking: bool = False
        
        # 线程控制
        self.done = threading.Event()
        self.vad_thread = None
        self.is_closed = False

    def _init_model(self, model_path: Optional[str] = None, use_default_model: bool = True) -> None:
        """
        初始化Silero VAD模型
        
        Args:
            model_path: 模型路径，如果为None则使用默认路径或从torch hub下载
            use_default_model: 是否使用默认内置模型，设为False则从torch hub下载
        """
        # 设置单线程运行以避免性能问题
        torch.set_num_threads(1)
        
        if model_path:
            # 使用指定的模型路径
            self.model = torch.jit.load(model_path)
        elif use_default_model and os.path.exists(DEFAULT_MODEL_PATH):
            # 使用默认内置模型
            self.model = torch.jit.load(DEFAULT_MODEL_PATH)
        else:
            # 从torch hub下载模型
            print("未找到默认模型，从torch hub下载中...")
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=True
            )
            self.model = model
            
        self.sample_rate = 16000  # Silero VAD固定使用16kHz采样率

    def detect_pcm_atom(
        self, 
        pcm_data: bytes, 
        channel_num: int = 1, 
        sample_rate: int = 16000, 
        bit_size: int = 16
    ) -> Tuple[float, Optional[Exception]]:
        """
        检测给定的PCM数据中是否包含语音
        
        Args:
            pcm_data: PCM格式的音频数据
            channel_num: 通道数
            sample_rate: 采样率
            bit_size: 位深度（16或32）
            
        Returns:
            语音检测的置信度，错误信息
        """
        if bit_size not in [16, 32]:
            return 0, ValueError("不支持的位深度，只支持16位或32位")
            
        try:
            byte_size = bit_size // 8
            
            # 将字节数据转换为numpy数组
            if bit_size == 16:
                # 16位整数格式
                audio_int16 = np.frombuffer(pcm_data, dtype=np.int16)
                # 转换为float32并归一化到[-1, 1]
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
            else:  # bit_size == 32
                # 32位浮点格式
                audio_float32 = np.frombuffer(pcm_data, dtype=np.float32)
            
            # 确保是单声道
            if channel_num > 1:
                # 如果是多声道，只取第一个通道
                audio_float32 = audio_float32[::channel_num]
            
            # 重采样到16kHz(如果需要)
            if sample_rate != self.sample_rate:
                # 这里应该添加重采样代码
                # 为简单起见，我们假设已经是16kHz
                pass
                
            # 转换为PyTorch张量并进行推理
            tensor = torch.from_numpy(audio_float32)
            confidence = self.model(tensor, self.sample_rate).item()
            
            return confidence, None
            
        except Exception as e:
            return 0, e

    def _try_vad(self) -> None:
        """尝试对缓冲区中的数据进行VAD检测"""
        frame_size = self.config.frame_samples * 2  # 16位PCM，每个采样点占2字节
        
        # 确保有足够的数据来进行VAD
        if self.input_audio_cache.size() >= frame_size:
            # 获取一帧数据
            data = self.input_audio_cache.get_size(frame_size)
            
            # 进行VAD检测
            vad_result, error = self.detect_pcm_atom(data)
            if error:
                print(f"VAD检测错误: {error}")
                return
                
            # 根据VAD结果更新状态
            if vad_result > self.config.positive_speech_threshold:
                # 检测到语音
                self.vad_not_pass_chunk_size = 0
                if not self.is_vad_speaking:
                    self.is_vad_speaking = True
                    if self.on_start_speaking:
                        self.on_start_speaking()
            elif vad_result < self.config.negative_speech_threshold:
                # 未检测到语音
                self.vad_not_pass_chunk_size += 1
                if self.vad_not_pass_chunk_size >= self.config.redemption_frames:
                    if self.is_vad_speaking:
                        self.is_vad_speaking = False
                        # 处理已缓存的语音数据
                        all_vad_cache = self.vad_audio_cache.get_all()
                        this_frame_size = len(all_vad_cache) // frame_size
                        
                        if this_frame_size > self.config.min_speech_frames:
                            # 如果语音片段足够长，则回调
                            padded_bytes = self._pad_pre_speech_bytes(
                                all_vad_cache, 
                                self.vad_not_speaking_frames,
                                self.config.pre_speech_pad_frames
                            )
                            duration_ms = len(padded_bytes) // 32  # 16kHz, 16bit = 32字节/ms
                            self.vad_not_speaking_frames = []
                            
                            if self.on_speech_data:
                                self.on_speech_data(padded_bytes, duration_ms)
            
            # 更新缓存
            if self.is_vad_speaking:
                # 在说话状态，将数据缓存到语音缓冲区
                self.vad_audio_cache.put(data)
            else:
                # 不在说话状态，更新未说话帧缓存
                max_frames = self.config.pre_speech_pad_frames
                if len(self.vad_not_speaking_frames) >= max_frames:
                    self.vad_not_speaking_frames.pop(0)
                self.vad_not_speaking_frames.append(data)

    def _pad_pre_speech_bytes(self, data: bytes, to_pad_data: List[bytes], frame_size: int) -> bytes:
        """
        在语音数据前添加静音帧
        
        Args:
            data: 语音数据
            to_pad_data: 待添加的静音帧列表
            frame_size: 要添加的帧数
            
        Returns:
            添加了静音帧的语音数据
        """
        if not data:
            return data
            
        get_size = frame_size
        to_pad_frame_size = len(to_pad_data)
        
        if to_pad_frame_size < frame_size:
            get_size = to_pad_frame_size
            
        # 从to_pad_data中取出get_size个帧的数据
        data_to_merge = to_pad_data[:get_size]
        pad_data = b''.join(data_to_merge)
        
        return pad_data + data

    def _vad_thread_fn(self) -> None:
        """VAD检测线程函数"""
        while not self.done.is_set():
            self._try_vad()
            time.sleep(self.config.vad_interval)

    def start_detect(self) -> None:
        """开始VAD检测"""
        if self.vad_thread is not None and self.vad_thread.is_alive():
            return
            
        self.done.clear()
        self.vad_thread = threading.Thread(target=self._vad_thread_fn)
        self.vad_thread.daemon = True
        self.vad_thread.start()

    def put_pcm_data(self, pcm_data: bytes) -> None:
        """
        放入PCM数据到输入缓冲区
        
        Args:
            pcm_data: PCM格式的音频数据
        """
        self.input_audio_cache.put(pcm_data)

    def close(self) -> None:
        """关闭VAD检测器并释放资源"""
        if self.is_closed:
            return
            
        self.done.set()
        if self.vad_thread and self.vad_thread.is_alive():
            self.vad_thread.join(timeout=1.0)
            
        self.is_closed = True

    def get_input_cache(self) -> AudioCache:
        """获取输入缓冲区"""
        return self.input_audio_cache

    def get_speaking_cache(self) -> AudioCache:
        """获取语音缓冲区"""
        return self.vad_audio_cache 