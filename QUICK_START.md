# 🚀 AI播客生成器 - 快速启动指南

## 系统概述

AI播客生成器是一个基于AI的播客自动生成系统，支持：
- 输入URL链接或问题查询
- 自动生成单人/双人播客内容
- 通过豆包TTS API生成高质量音频
- 双人播客使用FFmpeg进行音频拼接

## 前置要求

- Node.js 14+ 
- Python 3.6+
- ffmpeg (用于音频拼接处理)

## 快速启动

### 1. 一键启动 (推荐)

```bash
cd AI_Podcast
./start.sh
```

### 2. 手动启动

#### 步骤1: 安装依赖
```bash
# 安装前端依赖
npm install

# 安装Python依赖
cd agent-server
pip install -r requirements.txt
cd ..
```

#### 步骤2: 配置API密钥
```bash
# 复制配置文件示例
cp agent-server/config/example_config.yaml agent-server/config/single_config.yaml
cp agent-server/config/example_config.yaml agent-server/config/double_config.yaml

# 编辑配置文件，填入你的豆包TTS API密钥
# 将 YOUR_APP_ID 和 YOUR_TOKEN 替换为实际值
```

#### 步骤3: 启动服务
```bash
# 启动后端服务 (终端1)
cd agent-server
python server.py

# 启动前端服务 (终端2)
npm run serve
```

## 访问应用

- 前端: http://localhost:8080
- 后端API: http://localhost:5001

## 使用说明

1. **输入内容**：在输入框中输入播客主题或粘贴URL链接
2. **选择类型**：选择播客类型（单人/双人）
3. **开始生成**：点击"立即生成"按钮
4. **系统处理**：
   - 判断输入类型（URL或问题）
   - 通过Dify工作流生成播客内容
   - 调用豆包TTS API生成音频
   - 双人播客使用FFmpeg拼接音频片段
5. **查看结果**：等待生成完成，查看播客详情

## 系统架构

### 内容生成流程
```
用户输入 → Dify工作流 → 播客文本内容
```

### 音频生成流程
**单人播客：**
```
完整文本 → 豆包TTS API → MP3音频文件
```

**双人播客：**
```
对话文本 → 豆包TTS API → 临时音频片段 → FFmpeg拼接 → 最终MP3文件
```

## 常见问题

### Q: 后端服务启动失败
A: 检查Python依赖是否正确安装，确保ffmpeg已安装

### Q: 音频生成失败
A: 检查豆包TTS API密钥配置是否正确

### Q: 双人播客生成时间过长
A: 这是正常现象，因为需要分别生成多个音频片段并进行拼接

### Q: 前端无法连接后端
A: 确保后端服务在5001端口运行，检查防火墙设置

## 开发模式

```bash
# 启动开发服务器
npm run serve

# 构建生产版本
npm run build
```

## 项目结构

```
AI_Podcast/
├── src/                # 前端代码
│   ├── views/          # Vue页面组件
│   ├── api/            # API接口
│   └── router/         # 路由配置
├── agent-server/       # 后端服务
│   ├── server.py       # Flask服务器
│   ├── podcast_generator.py # 双人播客生成器
│   ├── single_podcast_generator.py # 单人播客生成器
│   ├── config/         # 配置文件
│   └── output/         # 音频输出目录
├── package.json        # 前端依赖
└── README.md          # 详细文档
```

## 技术栈

- **前端**: Vue 3, Vue Router, Element Plus
- **后端**: Python, Flask, WebSocket, PyDub, FFmpeg
- **第三方服务**: Dify工作流, 豆包TTS API, Jina 