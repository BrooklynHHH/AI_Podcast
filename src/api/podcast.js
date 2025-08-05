// podcast API 接口
const API_BASE_URL = 'http://localhost:5001'

export async function generatePodcast(text, type = 'single') {
  try {
    const response = await fetch(`${API_BASE_URL}/generate-podcast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        type: type
      })
    })

    const result = await response.json()
    
    if (result.success) {
      return {
        success: true,
        audioUrl: `${API_BASE_URL}/audio/${result.audio_file}`,
        audioFile: result.audio_file,
        podcastType: result.podcast_type
      }
    } else {
      return {
        success: false,
        error: result.error || '生成播客失败'
      }
    }
  } catch (error) {
    console.error('播客生成请求失败:', error)
    return {
      success: false,
      error: '网络请求失败，请检查服务器是否运行'
    }
  }
}

export async function downloadPodcast(audioFile) {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/${audioFile}`)
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = audioFile
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      return { success: true }
    } else {
      return { success: false, error: '下载失败' }
    }
  } catch (error) {
    console.error('下载播客失败:', error)
    return { success: false, error: '下载失败' }
  }
} 