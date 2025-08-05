<template>
  <div class="podcast-detail-container">
    <div class="detail-header">
      <button class="back-btn" @click="$router.go(-1)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </button>
      <h1 class="detail-title">{{ title }}</h1>
    </div>
    
    <div class="audio-player-section">
      <div class="audio-player">
        <audio 
          ref="audioPlayer" 
          :src="audioUrl" 
          controls 
          class="audio-element"
          @loadedmetadata="onAudioLoaded"
          @timeupdate="onTimeUpdate"
          @ended="onAudioEnded"
        ></audio>
      </div>
      
      <div class="player-controls">
        <button class="control-btn" @click="togglePlay" :disabled="!audioLoaded">
          <svg v-if="!isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5,3 19,12 5,21"></polygon>
          </svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="6" y="4" width="4" height="16"></rect>
            <rect x="14" y="4" width="4" height="16"></rect>
          </svg>
          {{ isPlaying ? '暂停' : '播放' }}
        </button>
        
        <button class="control-btn" @click="downloadAudio" :disabled="!audioLoaded">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7,10 12,15 17,10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          下载
        </button>
        
        <button class="control-btn" @click="sharePodcast">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="18" cy="5" r="3"></circle>
            <circle cx="6" cy="12" r="3"></circle>
            <circle cx="18" cy="19" r="3"></circle>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
          </svg>
          分享
        </button>
      </div>
    </div>
    
    <div class="content-section">
      <div class="content-header">
        <h2>播客内容</h2>
        <span class="podcast-type">{{ podcastType === 'single' ? '单人播客' : '双人播客' }}</span>
      </div>
      
      <div class="content-text" v-if="content">
        <div class="text-content" v-html="formattedContent"></div>
      </div>
      
      <div class="content-placeholder" v-else>
        <div class="placeholder-icon">📝</div>
        <div class="placeholder-text">暂无内容</div>
      </div>
    </div>
    
    <div class="action-section">
      <button class="action-btn primary" @click="generateNewPodcast">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 2v6h-6"></path>
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
          <path d="M3 22v-6h6"></path>
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
        </svg>
        生成新播客
      </button>
      
      <button class="action-btn secondary" @click="copyContent" v-if="content">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        复制内容
      </button>
    </div>
  </div>
</template>

<script>
import { downloadPodcast } from '@/api/podcast'
import { ElMessage } from 'element-plus'

export default {
  name: 'PodcastDetailView',
  data() {
    return {
      title: '',
      audioUrl: '',
      content: '',
      podcastType: 'single',
      isPlaying: false,
      audioLoaded: false,
      currentTime: 0,
      duration: 0
    }
  },
  computed: {
    formattedContent() {
      if (!this.content) return ''
      // 简单的格式化，将换行符转换为HTML
      return this.content.replace(/\n/g, '<br>')
    }
  },
  mounted() {
    this.loadPodcastData()
  },
  methods: {
    loadPodcastData() {
      const query = this.$route.query
      this.title = query.title || '播客详情'
      this.audioUrl = query.audioFile || ''
      this.content = query.content ? decodeURIComponent(query.content) : ''
      this.podcastType = query.type || 'single'
    },
    
    onAudioLoaded() {
      this.audioLoaded = true
      this.duration = this.$refs.audioPlayer.duration
    },
    
    onTimeUpdate() {
      this.currentTime = this.$refs.audioPlayer.currentTime
    },
    
    onAudioEnded() {
      this.isPlaying = false
    },
    
    togglePlay() {
      if (!this.audioLoaded) return
      
      if (this.isPlaying) {
        this.$refs.audioPlayer.pause()
      } else {
        this.$refs.audioPlayer.play()
      }
      this.isPlaying = !this.isPlaying
    },
    
    async downloadAudio() {
      if (!this.audioUrl) {
        ElMessage.error('音频文件不存在')
        return
      }
      
      try {
        const audioFile = this.audioUrl.split('/').pop()
        const result = await downloadPodcast(audioFile)
        
        if (result.success) {
          ElMessage.success('下载成功')
        } else {
          ElMessage.error(result.error || '下载失败')
        }
      } catch (error) {
        console.error('下载失败:', error)
        ElMessage.error('下载失败')
      }
    },
    
    sharePodcast() {
      if (navigator.share) {
        navigator.share({
          title: this.title,
          text: '听听这个AI生成的播客',
          url: window.location.href
        }).catch(error => {
          console.log('分享失败:', error)
          this.copyShareLink()
        })
      } else {
        this.copyShareLink()
      }
    },
    
    copyShareLink() {
      navigator.clipboard.writeText(window.location.href).then(() => {
        ElMessage.success('链接已复制到剪贴板')
      }).catch(() => {
        ElMessage.error('复制失败')
      })
    },
    
    generateNewPodcast() {
      this.$router.push('/podcast')
    },
    
    copyContent() {
      if (!this.content) {
        ElMessage.warning('没有内容可复制')
        return
      }
      
      navigator.clipboard.writeText(this.content).then(() => {
        ElMessage.success('内容已复制到剪贴板')
      }).catch(() => {
        ElMessage.error('复制失败')
      })
    }
  }
}
</script>

<style scoped>
.podcast-detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #fff5eb 0%, #ffe4cc 100%);
  padding: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 8px 16px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.detail-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.audio-player-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.audio-player {
  margin-bottom: 20px;
}

.audio-element {
  width: 100%;
  height: 60px;
  border-radius: 8px;
}

.player-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ff6700;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: #e55a00;
  transform: translateY(-1px);
}

.control-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.content-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h2 {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.podcast-type {
  background: #ff6700;
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.content-text {
  line-height: 1.8;
  color: #333;
  font-size: 16px;
}

.content-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 18px;
}

.action-section {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #ff6700;
  color: #fff;
}

.action-btn.primary:hover {
  background: #e55a00;
  transform: translateY(-1px);
}

.action-btn.secondary {
  background: #fff;
  color: #666;
  border: 1px solid #eee;
}

.action-btn.secondary:hover {
  background: #f5f5f5;
  color: #333;
}

@media (max-width: 768px) {
  .podcast-detail-container {
    padding: 16px;
  }
  
  .detail-title {
    font-size: 20px;
  }
  
  .player-controls {
    justify-content: center;
  }
  
  .action-section {
    justify-content: center;
  }
}
</style> 