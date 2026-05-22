# RoMER 多模态情感识别

基于视觉-语言-音频多模态融合的对话说话人情感识别项目，包含算法模型、后端服务和前端界面。

## 算法架构

### 模型结构

RoMER (Robust Multimodal Emotion Recognition) 采用三路编码器 + 跨模态融合的架构。

输入为三种模态数据：人脸图像序列、文本（字幕）、音频（语音），分别通过对应的编码器提取特征后，使用 Cross-Attention 机制进行跨模态融合，最终通过分类头输出 7 种情感类别的概率分布。

### 编码器

- **视觉编码器**: ConvNeXt + Transformer Decoder，提取人脸表情特征
- **文本编码器**: RoBERTa-base，提取语义特征（768 维）
- **音频编码器**: HuBERT-base，提取语音韵律特征（768 维）

### 融合策略

- 使用 Cross-Attention 机制实现跨模态交互
- 视觉特征与文本/音频特征双向融合
- 支持模态缺失（使用可学习的缺失 token）

### 人脸检测与追踪

- **S3FD**: 单尺度人脸检测器，用于检测图像/视频帧中的人脸
- **TalkNet**: 音视频联合说话人活跃检测，判断谁在说话
- **IoU 跟踪**: 基于 IoU 的人脸跨帧跟踪算法

## 环境要求

- Python 3.10+
- Node.js 16+
- FFmpeg（需添加到系统 PATH）
- NVIDIA GPU（推荐）

## 准备工作

### 1. 申请有道翻译 API Key

本项目使用有道翻译 API 将中文翻译为英文（用于文本编码）：

1. 访问 [有道智云](https://ai.youdao.com/) 注册账号
2. 创建翻译应用，获取 `appKey` 和 `appSecret`
3. 打开 `predict.py`，找到第 31 行：

```python
def translate(text, appKey='你的appKey', appSecret='你的appSecret'):
```

4. 替换为你的 API Key

### 2. 下载 TalkNet-ASD

```bash
cd data
git clone https://github.com/TaoRuijie/TalkNet-ASD.git
```

### 3. 下载模型权重

将 `best_model_acc.pth` 放到 `./weights/` 目录。

### 4. 准备预训练模型

运行 `utils.py` 会自动下载 RoBERTa 和 HuBERT 预训练模型到 `./data` 目录：

```bash
python utils.py
```

也可以手动从 Hugging Face 下载：
- RoBERTa: `roberta-base`
- HuBERT: `facebook/hubert-base-ls960`

## 安装与运行

### 后端

```bash
pip install -r requirements.txt
python backend/main.py
```

服务启动在 http://localhost:8000，API 文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
├── backend/                    # 后端 API 服务
│   ├── main.py                # FastAPI 主程序
│   ├── predict_detail.py      # 预测逻辑
│   └── progress_tracker.py    # 进度追踪
├── frontend/                   # 前端 Vue 项目
│   └── src/
│       ├── views/             # 页面组件
│       └── components/        # 通用组件
├── data/                       # 模型数据
│   ├── roberta-base/          # RoBERTa 预训练模型
│   ├── hubert-base/           # HuBERT 预训练模型
│   └── TalkNet-ASD/           # TalkNet 说话人检测模型
├── weights/                    # 模型权重
│   └── best_model_acc.pth
├── predict/                    # 预测相关
│   ├── images/                # 测试图片
│   ├── videos/                # 测试视频（含 .srt 字幕）
│   ├── result/                # 输出结果
│   └── temp/                  # 临时文件（人脸、音频、文本）
├── dataset.py                  # MELD 数据集定义与加载
├── detect.py                   # 人脸检测（S3FD）与说话人识别（TalkNet）
├── model.py                    # RoMER 模型定义
├── predict.py                  # 预测入口脚本
├── train.py                    # 模型训练脚本
├── utils.py                    # 环境构建与数据准备工具
└── requirements.txt            # Python 依赖
```

### 根目录脚本说明

| 脚本 | 功能 |
|------|------|
| `dataset.py` | MELD 数据集定义，支持训练/验证模式的数据加载 |
| `detect.py` | 人脸检测（S3FD）+ 说话人检测（TalkNet）+ 人脸跟踪 |
| `model.py` | RoMER 模型定义（ConvNeXt + Cross-Attention） |
| `predict.py` | 预测入口，支持图片和视频两种模式 |
| `train.py` | 模型训练脚本 |
| `utils.py` | 环境构建工具，自动下载预训练模型、提取特征、处理数据集 |

## 使用说明

### 图片识别

1. 访问 http://localhost:5173/image
2. 上传图片（支持多张）
3. 点击"开始识别"
4. 查看结果：标注图片、情感分布、人脸详情

### 视频识别

1. 访问 http://localhost:5173/video
2. 上传视频（.mp4）和字幕（.srt）
3. 点击"开始识别"
4. 等待处理完成（视频处理较慢）
5. 查看结果：标注视频、关键帧、片段详情

### 支持的情感类型

| 情感 | 英文 |
|------|------|
| 惊讶 | surprise |
| 快乐 | joy |
| 中性 | neutral |
| 悲伤 | sadness |
| 愤怒 | anger |
| 厌恶 | disgust |
| 恐惧 | fear |

## 常见问题

**Q: 视频识别很慢？**
A: 使用 GPU 加速，或缩短视频时长。

**Q: 翻译功能不工作？**
A: 检查 `predict.py` 中的有道 API Key 配置。

**Q: 找不到模块？**
A: 运行 `pip install -r requirements.txt`

**Q: 缺少预训练模型？**
A: 运行 `python utils.py` 自动下载，或手动下载放到 `./data` 目录。

## 训练数据集

**MELD数据集**：https://affective-meld.github.io/  
**预处理后的MELD数据集**：https://pan.baidu.com/s/1QQWzi4a_DXtka3Kri-zaLw?pwd=ucas
