# realtime-vad-python

Python实时语音活动检测(VAD)库，基于Silero VAD模型实现。此库可以实时检测音频流中的语音片段，适用于实时语音识别、在线会议等场景。

## 特性

- 实时处理音频流
- 低延迟检测（约32ms延迟）
- 可自定义语音检测阈值和参数
- 支持内置模型，无需手动下载
- 多线程设计，不阻塞主线程

## 安装

```bash
pip install realtime-vad-python
```

## 使用方法

### 简单示例

```python
import time
import pyaudio
from realtime_vad import RealTimeVadDetector

# 创建回调函数
def on_speech_data(audio_data, duration_ms):
    print(f"检测到语音片段，时长: {duration_ms}毫秒")

def on_start_speaking():
    print("检测到开始说话...")

# 初始化VAD检测器（使用内置模型）
detector = RealTimeVadDetector(
    on_speech_data=on_speech_data,
    on_start_speaking=on_start_speaking,
    use_default_model=True  # 使用默认内置模型
)

# 启动VAD检测
detector.start_detect()

# 设置PyAudio进行麦克风录音
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=512
)

try:
    while True:
        # 读取音频数据
        data = stream.read(512)
        # 将数据送入VAD检测器
        detector.put_pcm_data(data)
        time.sleep(0.01)
except KeyboardInterrupt:
    pass
finally:
    # 清理资源
    stream.stop_stream()
    stream.close()
    p.terminate()
    detector.close()
```

### 自定义配置

可以通过 `VadConfig` 类自定义VAD参数：

```python
from realtime_vad import RealTimeVadDetector, VadConfig

# 创建自定义配置
config = VadConfig(
    positive_speech_threshold=0.8,  # 语音检测的正阈值
    negative_speech_threshold=0.3,  # 语音检测的负阈值
    redemption_frames=6,           # 6帧无语音才判定说话结束
    min_speech_frames=3,           # 最少3帧才算有效语音
    frame_samples=512,             # 每帧样本数（32ms@16kHz）
    vad_interval=0.032             # VAD检测间隔
)

# 初始化VAD检测器
detector = RealTimeVadDetector(
    config=config,
    on_speech_data=on_speech_data,
    on_start_speaking=on_start_speaking
)
```

### 模型选项

该库提供了三种使用模型的方式：

1. **使用内置模型**（默认）：
   ```python
   detector = RealTimeVadDetector(use_default_model=True)
   ```

2. **指定自定义模型路径**：
   ```python
   detector = RealTimeVadDetector(model_path="/path/to/your/silero_vad.jit")
   ```

3. **从Torch Hub下载模型**：
   ```python 
   detector = RealTimeVadDetector(use_default_model=False)
   ```

## 开发说明

如果您想参与开发或修改源码，首先克隆仓库：

```bash
git clone https://github.com/your-username/realtime-vad-python.git
cd realtime-vad-python
```

### 下载并保存模型

如果您需要更新内置模型，可以使用提供的脚本：

```bash
python download_model.py
```

## 许可证

MIT 