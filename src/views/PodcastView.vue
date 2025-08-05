<template>
  <div class="chat-container podcast-bg">
    <div class="podcast-content-container">
      <div class="main-header">
        <h1 class="main-title">
          <span class="icon-circle"></span>
          <span class="gradient-ai">AI</span>
          <span class="icon-bell"></span>
          <span class="gradient-podcast">播客生成器</span>
          <span class="icon-books"></span>
        </h1>
        <div class="main-desc">在几秒钟内将您的内容转为可分享的播客节目</div>
      </div>
      <div class="input-card">
        <div class="input-row">
          <textarea v-model="podcastText" class="topic-input" placeholder="粘贴URL到这里" />
        </div>
        <div class="option-row">
          <div class="host-select">
            <span>主持人：</span>
            <span class="host-avatar">🧑‍💼 李静</span>
            <span class="host-avatar">🧑‍💼 王涛</span>
            <button class="type-btn" :class="{active: selectedType==='single'}" @click="selectType('single')">单人</button>
            <button class="type-btn" :class="{active: selectedType==='double'}" @click="selectType('double')">双人</button>
          </div>
        </div>
        <button 
          class="main-generate-btn" 
          :disabled="!podcastText.trim() || isGenerating" 
          @click="handleGenerate"
        >
          <img src="@/assets/light.svg" alt="生成" class="btn-icon" />
          <span v-if="isGenerating">生成中...</span>
          <span v-else>立即生成</span>
        </button>
      </div>
      <div class="example-section">
        <div class="example-title">示例提示词</div>
        <div class="example-list">
          <span class="example-item" @click="useExample('斯坦福 AI 指数报告 2024')">斯坦福 AI 指数报告 2024</span>
          <span class="example-item" @click="useExample('马斯克的愿景：构建明天')">马斯克的愿景：构建明天</span>
          <span class="example-item" @click="useExample('大语言模型中的知识蒸馏')">大语言模型中的知识蒸馏</span>
          <span class="example-item" @click="useExample('5 个日常生产力小贴士')">5 个日常生产力小贴士</span>
        </div>
      </div>
      <div class="podcast-output" v-if="isGenerating">
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <div class="loading-text">播客生成中，请稍候...</div>
        </div>
      </div>
      <div class="error-message" v-if="error">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import { generatePodcast } from '@/api/podcast'
import { ElMessage } from 'element-plus'

export default {
  name: 'PodcastView',
  data() {
    return {
      selectedType: 'single', // 默认单人
      podcastText: '', // 用户输入的播客主题
      difyGeneratedContent: '', // Dify 生成的文本内容
      isGenerating: false,
      error: null,
      loadingDify: false, // 新增：Dify 生成中状态
      loadingAudio: false, // 新增：音频生成中状态
      userId: 'podcast-user', // Dify 用户 ID
      controller: null // 用于取消 Dify 请求
    }
  },
  methods: {
    useExample(text) {
      this.podcastText = text
    },
    selectType(type) {
      this.selectedType = type
    },
    async handleGenerate() {
      if (!this.podcastText.trim()) {
        this.error = '请输入播客主题'
        return
      }

      this.isGenerating = true
      this.loadingDify = true
      this.error = null
      this.difyGeneratedContent = ''

      try {
        // 步骤 1: 呼叫 Dify API 生成播客文本
        const apiKey = this.selectedType === 'single' ? 'YOUR_SINGLE_API_KEY' : 'YOUR_DOUBLE_API_KEY'
        const url = 'YOUR_DIFY_API_URL'
        const headers = {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
        const body = {
          query: this.podcastText,
          inputs: {},
          response_mode: 'streaming',
          user: this.userId
        }

        this.controller = new AbortController()
        const response = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify(body),
          signal: this.controller.signal
        })

        if (!response.body) throw new Error('无法获取 Dify 流式数据')

        const reader = response.body.getReader()
        let buffer = ''
        let fullAnswer = ''
        let finishedDify = false

        while (!finishedDify) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += new TextDecoder().decode(value)
          const parts = buffer.split('\n\n')
          buffer = parts.pop()

          for (const part of parts) {
            if (!part.trim().startsWith('data:')) continue
            const jsonStr = part.replace(/^data:\s*/, '')
            if (!jsonStr) continue
            let data
            try {
              data = JSON.parse(jsonStr)
            } catch (e) { continue }

            if (data.event === 'message') {
              if (data.answer) {
                fullAnswer += data.answer
              }
            }
            if (data.event === 'message_end') {
              finishedDify = true
            }
          }
        }
        this.difyGeneratedContent = fullAnswer

        // 步骤 2: Dify 文本生成完成，开始生成音频
        this.loadingDify = false
        this.loadingAudio = true

        const result = await generatePodcast(this.difyGeneratedContent, this.selectedType)
        if (result.success) {
          ElMessage.success('生成成功')
          this.$router.push({
            path: '/podcast-detail',
            query: {
              audioFile: result.audioUrl,
              title: this.podcastText,
              content: encodeURIComponent(this.difyGeneratedContent),
              type: this.selectedType
            }
          })
        } else {
          this.error = result.error || '生成播客音频失败'
          ElMessage.error(this.error)
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Dify 请求被取消')
          this.error = '生成已被取消'
        } else {
          this.error = error.message || '生成播客时出错'
        }
        ElMessage.error(this.error)
      } finally {
        this.isGenerating = false
        this.loadingDify = false
        this.loadingAudio = false
      }
    }
  }
}
</script>

<style scoped>
.chat-container.podcast-bg {
  position: fixed;
  display: grid;
  grid-template-rows: 1fr auto;
  height: 100vh;
  width: 100vw;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.podcast-content-container {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 0 32px 0;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.main-header {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
}
.main-title {
  font-size: 48px; /* 根據最新圖片調整大小 */
  font-weight: 800; /* 調整字體粗細 */
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px; /* 調整文字和圖標之間的間距 */
}
.gradient-ai {
  background: linear-gradient(to right, #ff6b6b, #e03636); /* 红色渐变 */
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.gradient-podcast {
  background: linear-gradient(to right, #333, #000); /* 黑色渐变 */
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
/* 小图标的占位符样式，您可以替换为实际的 SVG 或 CSS 图标 */
.icon-circle,
.icon-bell,
.icon-books {
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  vertical-align: middle;
}
.icon-circle {
  width: 20px;
  height: 20px;
  background-color: #333; /* 模拟圆点 */
  border-radius: 50%;
  margin-right: 5px; /* 调整间距 */
}
.icon-bell {
  width: 24px;
  height: 24px;
  background-image: url('@/assets/bell-icon.svg'); /* 替换为您的铃铛图标 SVG 路径 */
  margin: 0 5px;
}
.icon-books {
  width: 28px;
  height: 28px;
  background-image: url('@/assets/books-icon.svg'); /* 替换为您的书籍图标 SVG 路径 */
  margin-left: 5px;
}
.main-desc {
  font-size: 18px;
  color: #666;
}
.input-card {
  background: rgba(255, 255, 255, 0.6); /* 半透明背景，讓毛玻璃效果可見 */
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); /* 調整陰影，使其更柔和 */
  backdrop-filter: blur(10px); /* 毛玻璃效果 */
  -webkit-backdrop-filter: blur(10px); /* 兼容 Safari */
  border: 1px solid transparent; /* 基礎邊框，寬度減小 */
  border-image: linear-gradient(to right, #ff6700, #ffb300); /* 漸變邊框 */
  border-image-slice: 1; /* 確保漸變應用於整個邊框 */
  /* 這些屬性有助於確保 border-radius 與 border-image 正確結合 */
  background-origin: border-box;
  background-clip: padding-box, border-box;
  padding: 30px;
  width: 100%;
  box-sizing: border-box;
}
.input-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.topic-input {
  width: 100%;
  min-height: 70px;
  padding: 14px;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 16px;
  background: #f5f5f5;
  resize: none;
  margin-bottom: 20px; /* 增加与下方选项的间距 */
}
.option-row {
  display: flex;
  align-items: center;
  gap: 20px; /* 调整选项之间的间距 */
  font-size: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px; /* 增加与立即生成按钮的间距 */
}
.host-select {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.host-avatar {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 4px 14px;
  font-size: 16px;
}
.type-btn {
  padding: 8px 20px; /* 调整按钮内边距 */
  border: 1px solid #eee;
  border-radius: 12px;
  background: #fff;
  color: #888;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}
.type-btn.active, .type-btn:hover {
  background: #ff6700;
  color: #fff;
  border-color: #ff6700;
}
.main-generate-btn {
  background: linear-gradient(90deg, #ff6700 0%, #ffb300 100%);
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 16px;
  width: 100%;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 12px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.main-generate-btn:disabled {
  background: #eee;
  color: #bbb;
  cursor: not-allowed;
}

.btn-icon {
  width: 24px;
  height: 24px;
}
.example-section {
  margin-bottom: 12px;
}
.example-title {
  color: #888;
  font-size: 16px;
  margin-bottom: 8px;
}
.example-list {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.example-item {
  background: #f5f5f5;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 15px;
  color: #444;
  cursor: pointer;
  transition: all 0.2s ease;
}
.example-item:hover {
  background: #ffecdb;
  color: #333;
  transform: translateY(-1px);
}
.podcast-output {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px;
  margin-top: 12px;
}
.podcast-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.message {
  padding: 12px 18px;
  border-radius: 8px;
  background: #f5f5f5;
  font-size: 16px;
  color: #333;
}
.message.system {
  color: #ff6700;
  font-style: italic;
  background: transparent;
  box-shadow: none;
}
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 16px;
}
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #ff6700;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.loading-text {
  color: #666;
  font-size: 16px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
@media (max-width: 900px) {
  .podcast-content-container {
    max-width: 100vw;
    padding: 16px 2px 12px 2px;
  }
  .input-card {
    padding: 10px 2px 8px 2px;
  }
}
.error-message {
  color: #ff6700;
  font-size: 16px;
  margin-top: 12px;
  text-align: center;
}
.podcast-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #fff5eb 0%, #ffe4cc 100%);
  padding: 20px;
}

.podcast-container {
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.podcast-header {
  margin-bottom: 24px;
}
</style> 