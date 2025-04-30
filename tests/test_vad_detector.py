#!/usr/bin/env python3
"""
VAD检测器单元测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from realtime_vad import AudioCache, RealTimeVadDetector, VadConfig


class TestAudioCache(unittest.TestCase):
    """测试音频缓存类"""
    
    def test_put_and_get_all(self):
        """测试放入和获取所有数据"""
        cache = AudioCache()
        data = b'test data'
        
        # 测试放入和获取所有
        cache.put(data)
        self.assertEqual(cache.size(), len(data))
        
        result = cache.get_all()
        self.assertEqual(result, data)
        self.assertEqual(cache.size(), 0)
    
    def test_get_size(self):
        """测试获取指定大小的数据"""
        cache = AudioCache()
        data = b'1234567890'
        
        # 放入数据
        cache.put(data)
        
        # 获取部分数据
        result = cache.get_size(5)
        self.assertEqual(result, b'12345')
        self.assertEqual(cache.size(), 5)
        
        # 获取比缓存更大的数据（应该补零）
        cache.clear()
        cache.put(data)
        result = cache.get_size(15)
        self.assertEqual(result, data + bytes(5))
        self.assertEqual(cache.size(), 0)


class TestVadDetector(unittest.TestCase):
    """测试VAD检测器"""
    
    def setUp(self):
        """测试前初始化"""
        # 模拟torch.hub.load的返回值
        self.mock_model = Mock()
        self.mock_model.return_value = torch.tensor([0.9])
        
        # 模拟on_speech_data回调函数
        self.on_speech_data = Mock()
        
        # 模拟on_start_speaking回调函数
        self.on_start_speaking = Mock()
    
    @patch('torch.hub.load')
    def test_init(self, mock_load):
        """测试初始化"""
        mock_load.return_value = (self.mock_model, None)
        
        # 创建检测器
        detector = RealTimeVadDetector(
            on_speech_data=self.on_speech_data,
            on_start_speaking=self.on_start_speaking
        )
        
        # 验证初始化结果
        self.assertIsNotNone(detector)
        self.assertEqual(detector.is_vad_speaking, False)
        self.assertEqual(detector.vad_not_pass_chunk_size, 0)
        self.assertEqual(len(detector.vad_not_speaking_frames), 0)
    
    @patch('torch.hub.load')
    def test_detect_pcm_atom(self, mock_load):
        """测试单次PCM检测"""
        mock_load.return_value = (self.mock_model, None)
        
        # 创建检测器
        detector = RealTimeVadDetector()
        
        # 创建16位PCM测试数据
        pcm_data = np.zeros(1600, dtype=np.int16).tobytes()
        
        # 测试检测函数
        confidence, error = detector.detect_pcm_atom(pcm_data)
        
        # 验证结果
        self.assertIsNone(error)
        
        # 验证差值小于 0.1 就行
        self.assertLess(abs(confidence - 0.9), 0.1)
    
    @patch('torch.hub.load')
    def test_pad_pre_speech_bytes(self, mock_load):
        """测试添加前部静音帧"""
        mock_load.return_value = (self.mock_model, None)
        
        # 创建检测器
        detector = RealTimeVadDetector()
        
        # 创建测试数据
        speech_data = b'speech'
        pre_frames = [b'pre1', b'pre2', b'pre3']
        
        # 测试添加
        result = detector._pad_pre_speech_bytes(speech_data, pre_frames, 2)
        
        # 验证结果
        self.assertEqual(result, b'pre1pre2speech')


if __name__ == '__main__':
    unittest.main() 