/**
 * WebSocket工具类
 */
export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  constructor(url: string) {
    this.url = url
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = token ? `${this.url}?token=${token}` : this.url
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
        this.reconnectAttempts = 0
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        reject(error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket连接已关闭')
        this.attemptReconnect()
      }
    })
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        const token = localStorage.getItem('access_token')
        this.connect(token || undefined).catch(() => {
          // 重连失败，继续尝试
        })
      }, this.reconnectDelay)
    }
  }

  private handleMessage(data: any) {
    const type = data.type
    const listeners = this.listeners.get(type)
    if (listeners) {
      listeners.forEach((listener) => listener(data))
    }
    // 触发通用消息监听
    const allListeners = this.listeners.get('*')
    if (allListeners) {
      allListeners.forEach((listener) => listener(data))
    }
  }

  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }))
    } else {
      console.warn('WebSocket未连接')
    }
  }

  on(type: string, callback: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set())
    }
    this.listeners.get(type)!.add(callback)
  }

  off(type: string, callback: (data: any) => void) {
    const listeners = this.listeners.get(type)
    if (listeners) {
      listeners.delete(callback)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
  }

  // 心跳检测
  startHeartbeat(interval = 30000) {
    const heartbeat = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', {})
      } else {
        clearInterval(heartbeat)
      }
    }, interval)
  }
}

// 创建WebSocket客户端实例
// 使用相对路径，通过nginx代理
const getWebSocketUrl = () => {
  // 开发环境强制使用相对路径
  const apiUrl = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '')
  if (apiUrl) {
    return `${apiUrl.replace('http', 'ws')}/ws/default`
  }
  // 如果没有设置API_URL，使用当前页面的协议和主机（通过Nginx代理）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/chat/ws`
}
export const wsClient = new WebSocketClient(getWebSocketUrl())
