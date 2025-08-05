# AI Podcast Generator

一个基于AI的播客自动生成系统，用户输入问题或网址，系统自动生成单人或双人对话形式的播客音频。

## 演示视频

### 🎥 方式一：在线播放（推荐）

<video width="100%" controls>
  <source src="https://raw.githubusercontent.com/BrooklynHHH/AI_Podcast/main/AI_podcast.mp4" type="video/mp4">
  您的浏览器不支持视频播放，请使用下方下载链接。
</video>

### 📥 方式二：直接下载

> 💡 **提示**: 如果上方视频无法播放，请点击下方链接下载观看
> 
> [📥 下载演示视频](https://raw.githubusercontent.com/BrooklynHHH/AI_Podcast/main/AI_podcast.mp4)

## 功能特性

- 🎙️ 支持单人播客和双人播客生成
- 🌐 支持URL链接和问题查询两种输入方式
- 🎨 现代化的用户界面设计
- 📱 响应式设计，支持移动端
- 🎵 内置音频播放器
- 💾 支持播客下载和分享
- 🔄 实时生成状态显示
- 🤖 基于大模型的智能内容生成

## 系统架构

### 核心架构流程

#### 3.1 内容获取与LLM处理层（Dify工作流）

**输入识别：**
- 系统首先判断用户输入是URL还是普通问题
- 如果是URL：使用Jina工具抓取网页内容，获取结构化文本数据
- 如果是问题：使用搜索引擎获取相关信息

**内容加工：**
- 将获取的原始内容通过大模型进行播客化改写
- 单人播客：生成连贯的独白形式文本，模拟主播口语化表达
- 双人播客：生成对话形式文本，每行代表一个人的发言，用换行符分隔

**Dify工作流地址：**
- 单人播客：请配置你的Dify工作流地址
- 双人播客：请配置你的Dify工作流地址

#### 3.2 音频生成层（TTS服务）

**豆包TTS API文档：**
- 单人播客：请参考豆包官方文档
- 双人播客：请参考豆包官方文档

**单人播客生成流程：**
```
完整文本 → 豆包TTS API → MP3音频文件
```
- 直接将整段文本发送给豆包TTS API
- 使用固定女声音色，一次性生成完整音频

**双人播客生成流程：**
```
对话文本 → 豆包语音播客TTS API → 临时音频片段 → FFmpeg拼接 → 最终MP3音频文件
```
- 按换行符分割文本，获得多个对话片段
- 奇数行使用男声音色，偶数行使用女声音色
- 每个片段单独调用豆包TTS API生成音频文件
- 使用FFmpeg将所有音频片段按顺序拼接成最终的双人对话播客音频

#### 3.3 服务接口层

服务端提供统一的API接口，接收前端请求，协调Dify工作流和TTS服务，返回生成的音频文件链接。

## 技术栈

### 前端
- Vue 3
- Vue Router
- Element Plus
- CSS3

### 后端
- Python 3.6+
- Flask
- WebSocket
- PyDub (音频处理)
- FFmpeg (音频拼接)

### 第三方服务
- Dify工作流 (内容生成)
- 豆包TTS API (语音合成)
- Jina (网页内容抓取)

## 安装和运行

### 1. 安装前端依赖

```bash
cd AI_Podcast
npm install
```

### 2. 安装Python依赖

```bash
cd agent-server
pip install -r requirements.txt
```

### 3. 配置API密钥

在 `agent-server/config/` 目录下配置你的API密钥：

- `single_config.yaml` - 单人播客配置
- `double_config.yaml` - 双人播客配置

参考 `example_config.yaml` 文件，将配置文件中的 `YOUR_APP_ID` 和 `YOUR_TOKEN` 替换为你的实际豆包TTS API密钥。

### 4. 启动后端服务

```bash
cd agent-server
python server.py
```

后端服务将在 `http://localhost:5001` 启动。

### 5. 启动前端服务

```bash
npm run serve
```

前端应用将在 `http://localhost:8080` 启动。

## 使用说明

1. 在输入框中输入播客主题或粘贴URL链接
2. 选择播客类型（单人/双人）
3. 点击"立即生成"按钮
4. 系统会自动：
   - 判断输入类型（URL或问题）
   - 通过Dify工作流生成播客内容
   - 调用豆包TTS API生成音频
   - 对于双人播客，使用FFmpeg拼接音频片段
5. 等待生成完成，系统会自动跳转到播客详情页面
6. 在详情页面可以播放、下载或分享播客

## 项目结构

```
AI_Podcast/
├── src/                        # 前端代码
│   ├── api/
│   │   └── podcast.js          # API接口
│   ├── views/
│   │   ├── PodcastView.vue     # 播客生成页面
│   │   └── PodcastDetailView.vue # 播客详情页面
│   ├── router/
│   │   └── index.js            # 路由配置
│   ├── App.vue                 # 主应用组件
│   └── main.js                 # 应用入口
├── agent-server/               # 后端服务
│   ├── server.py               # Flask服务器
│   ├── podcast_generator.py    # 双人播客生成器
│   ├── single_podcast_generator.py # 单人播客生成器
│   ├── requirements.txt        # Python依赖
│   ├── config/                 # 配置文件
│   │   ├── single_config.yaml  # 单人播客配置
│   │   ├── double_config.yaml  # 双人播客配置
│   │   └── example_config.yaml # 配置示例
│   ├── output/                 # 音频输出目录
│   └── README.md               # 后端说明文档
├── package.json                # 前端依赖
├── start.sh                    # 一键启动脚本
├── README.md                   # 项目说明
└── QUICK_START.md             # 快速启动指南
```

## 注意事项

1. 确保已安装ffmpeg用于音频拼接处理
2. 需要有效的豆包TTS API密钥才能使用语音合成服务
3. 生成的音频文件会保存在 `src/scripts/podcast/output/` 目录下
4. 双人播客由于音频拼接技术问题，生成时间会比单人播客更长
5. 建议在生产环境中使用HTTPS协议

## 开发说明

- 前端使用Vue 3 Composition API
- 后端使用Flask提供RESTful API
- 音频处理使用PyDub库和FFmpeg
- 支持WebSocket实时通信
- 通过Dify工作流实现智能内容生成
- 使用豆包TTS API实现高质量语音合成

## 许可证

MIT License 
