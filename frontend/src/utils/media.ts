/**
 * 媒体处理工具
 */
export interface VideoMetadata {
  duration: number
  width: number
  height: number
  bitrate: number
  codec: string
}

export interface AudioMetadata {
  duration: number
  bitrate: number
  sampleRate: number
  channels: number
}

/**
 * 获取视频元数据
 */
export async function getVideoMetadata(file: File): Promise<VideoMetadata> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    
    video.onloadedmetadata = () => {
      resolve({
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
        bitrate: 0, // 浏览器无法直接获取
        codec: '' // 浏览器无法直接获取
      })
      URL.revokeObjectURL(video.src)
    }
    
    video.onerror = () => {
      reject(new Error('无法加载视频文件'))
      URL.revokeObjectURL(video.src)
    }
    
    video.src = URL.createObjectURL(file)
  })
}

/**
 * 获取音频元数据
 */
export async function getAudioMetadata(file: File): Promise<AudioMetadata> {
  return new Promise((resolve, reject) => {
    const audio = document.createElement('audio')
    audio.preload = 'metadata'
    
    audio.onloadedmetadata = () => {
      resolve({
        duration: audio.duration,
        bitrate: 0, // 浏览器无法直接获取
        sampleRate: 0, // 浏览器无法直接获取
        channels: 0 // 浏览器无法直接获取
      })
      URL.revokeObjectURL(audio.src)
    }
    
    audio.onerror = () => {
      reject(new Error('无法加载音频文件'))
      URL.revokeObjectURL(audio.src)
    }
    
    audio.src = URL.createObjectURL(file)
  })
}

/**
 * 生成视频缩略图
 */
export async function generateVideoThumbnail(
  videoFile: File,
  time: number = 0
): Promise<string> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.currentTime = time
    
    video.onloadeddata = () => {
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        resolve(canvas.toDataURL('image/jpeg', 0.8))
      } else {
        reject(new Error('无法创建canvas上下文'))
      }
      
      URL.revokeObjectURL(video.src)
    }
    
    video.onerror = () => {
      reject(new Error('无法加载视频文件'))
      URL.revokeObjectURL(video.src)
    }
    
    video.src = URL.createObjectURL(videoFile)
  })
}

/**
 * 格式化时长
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * 视频播放器组件（简化版）
 */
export class SimpleVideoPlayer {
  private video: HTMLVideoElement
  private container: HTMLElement
  
  constructor(container: HTMLElement, videoUrl: string) {
    this.container = container
    this.video = document.createElement('video')
    this.video.src = videoUrl
    this.video.controls = true
    this.video.className = 'w-full h-full'
    this.container.appendChild(this.video)
  }
  
  play() {
    return this.video.play()
  }
  
  pause() {
    this.video.pause()
  }
  
  setCurrentTime(time: number) {
    this.video.currentTime = time
  }
  
  getCurrentTime(): number {
    return this.video.currentTime
  }
  
  getDuration(): number {
    return this.video.duration
  }
  
  destroy() {
    this.video.pause()
    this.video.src = ''
    this.container.removeChild(this.video)
  }
}












