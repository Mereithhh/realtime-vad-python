"""
音频缓冲区模块，用于存储和管理音频数据。
"""
from typing import List, Optional


class AudioCache:
    """音频缓冲区，可以自动变长并提供多种数据获取方式"""

    def __init__(self):
        """初始化一个空的音频缓冲区"""
        self.cache: bytearray = bytearray()

    def put(self, data: bytes) -> None:
        """
        放入音频数据到缓冲区
        
        Args:
            data: 要放入的字节数据
        """
        self.cache.extend(data)

    def get_all(self) -> bytes:
        """
        获取并清空所有缓冲区数据
        
        Returns:
            所有缓冲区数据
        """
        if len(self.cache) == 0:
            return b''
        
        data = bytes(self.cache)
        self.cache.clear()
        return data

    def get_size(self, size: int) -> bytes:
        """
        获取指定大小的数据
        
        Args:
            size: 要获取的字节数
            
        Returns:
            指定大小的数据，如果缓冲区数据不足，将用零填充
        """
        if len(self.cache) == 0:
            return b''
        
        fix_num = 0
        actual_size = size
        
        if len(self.cache) < size:
            fix_num = size - len(self.cache)
            actual_size = len(self.cache)
        
        data = bytes(self.cache[:actual_size])
        self.cache = self.cache[actual_size:]
        
        if fix_num > 0:
            data += bytes(fix_num)
        
        return data

    def clear(self) -> None:
        """清空缓冲区"""
        self.cache.clear()

    def size(self) -> int:
        """
        获取缓冲区大小
        
        Returns:
            缓冲区字节数
        """
        return len(self.cache) 