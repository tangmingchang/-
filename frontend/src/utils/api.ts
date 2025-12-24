import axios from 'axios'

// 使用相对路径，通过Vite代理（开发环境）或Nginx代理（生产环境）到后端
// 开发环境：强制使用相对路径，忽略VITE_API_URL环境变量
// 生产环境：如果设置了VITE_API_URL，使用它；否则使用相对路径通过Nginx代理
const API_URL = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '')

// 工具函数：确保URL使用相对路径（通过Nginx代理）
export function ensureRelativeUrl(url: string): string {
  if (!url) return url
  // 处理包含 localhost:8000 的旧URL
  if (url.includes('localhost:8000') || url.includes('127.0.0.1:8000')) {
    try {
      const urlObj = new URL(url)
      return urlObj.pathname + urlObj.search
    } catch {
      return url.replace(/^https?:\/\/[^/]+/, '')
    }
  }
  // 如果是完整URL，提取路径部分
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const urlObj = new URL(url)
      return urlObj.pathname + urlObj.search
    } catch {
      return url.replace(/^https?:\/\/[^/]+/, '')
    }
  }
  // 如果已经是相对路径，直接返回
  return url
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 添加请求拦截器，自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers = config.headers || {}
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器，处理401错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 网络错误（后端未启动）不显示错误，静默处理
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      // 静默处理，不抛出错误，让页面正常显示
      return Promise.reject(error)
    }
    
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname
      
      // 如果已经在登录页，只清除token，不跳转
      if (currentPath === '/login' || currentPath.startsWith('/login')) {
        localStorage.removeItem('access_token')
        return Promise.reject(error)
      }
      
      // 清除token
      localStorage.removeItem('access_token')
      
      // 延迟跳转，避免在组件加载时立即跳转导致闪退
      setTimeout(() => {
        if (window.location.pathname !== '/login' && !window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
      }, 500)
    }
    return Promise.reject(error)
  }
)

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  stream?: boolean
}

export interface ChatResponse {
  conversation_id: string
  message: string
  role: string
  timestamp: string
}

export interface Conversation {
  id: string
  title: string
  created_at: string
}

export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  created_at: string
}

// API函数
export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/api/chat', request)
    return response.data
  },
  
  getConversations: async (): Promise<Conversation[]> => {
    const response = await api.get<Conversation[]>('/api/conversations')
    return response.data
  },
  
  getMessages: async (conversationId: string): Promise<ChatMessage[]> => {
    const response = await api.get<ChatMessage[]>(
      `/api/conversations/${conversationId}/messages`
    )
    return response.data
  },
}

export const knowledgeApi = {
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<Document>('/api/knowledge/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  
  searchKnowledge: async (query: string, limit: number = 5) => {
    const response = await api.get('/api/knowledge/search', {
      params: { query, limit },
    })
    return response.data
  },
  
  getDocuments: async (): Promise<Document[]> => {
    const response = await api.get<Document[]>('/api/knowledge/documents')
    return response.data
  },
  
  deleteDocument: async (documentId: number): Promise<void> => {
    await api.delete(`/api/knowledge/documents/${documentId}`)
  },
}

