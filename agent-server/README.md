# AI播客生成器 - 后端服务

这是AI播客生成器的后端服务，提供播客音频生成API。

## 功能特性

- 🎙️ 支持单人播客和双人播客生成
- 🔧 基于豆包TTS API的语音合成
- 🎵 支持音频拼接和格式转换
- 📡 RESTful API接口
- 🔒 跨域支持

## 系统要求

- Python 3.8+
- ffmpeg (用于音频处理)
- 豆包TTS API密钥

## 安装步骤

### 1. 创建虚拟环境

```bash
python3 -m venv venv
```

### 2. 启动虚拟环境

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置API密钥

编辑配置文件，填入你的豆包TTS API密钥：

```bash
# 编辑单人播客配置
vim config/single_config.yaml

# 编辑双人播客配置  
vim config/double_config.yaml
```

将 `YOUR_APP_ID` 和 `YOUR_TOKEN` 替换为实际的API密钥。

## 启动服务

```bash
python server.py
```

服务将在 `http://localhost:5001` 启动。

## API接口

### 健康检查

```
GET /health
```

### 生成播客

```
POST /generate-podcast
```

**请求参数：**
```json
{
  "text": "播客内容文本",
  "type": "single"  // "single" 或 "double"
}
```

**响应：**
```json
{
  "success": true,
  "audio_file": "generated_audio.wav",
  "podcast_type": "single"
}
```

### 获取音频文件

```
GET /audio/{filename}
```

## 项目结构

```
agent-server/
├── server.py                    # Flask服务器
├── podcast_generator.py         # 双人播客生成器
├── single_podcast_generator.py  # 单人播客生成器
├── requirements.txt             # Python依赖
├── config/                     # 配置文件
│   ├── single_config.yaml      # 单人播客配置
│   └── double_config.yaml      # 双人播客配置
├── output/                     # 音频输出目录
└── README.md                   # 说明文档
```

## 开发说明

- 使用Flask提供RESTful API
- 支持CORS跨域请求
- 音频文件保存在output目录
- 支持WAV格式音频输出

## 注意事项

1. 确保ffmpeg已正确安装
2. 需要有效的豆包TTS API密钥
3. 双人播客生成时间较长，属于正常现象
4. 建议在生产环境中使用HTTPS协议

## 许可证

MIT License 