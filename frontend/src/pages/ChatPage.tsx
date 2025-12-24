import { useState, useRef, useEffect } from 'react'
import { Send, User, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { chatApi, ChatMessage } from '../utils/api'

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const connectWebSocket = () => {
    // 使用相对路径，通过nginx代理
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/api/chat/ws`)
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'session') {
        setConversationId(data.conversation_id)
      } else if (data.type === 'start') {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '' },
        ])
        setLoading(true)
      } else if (data.type === 'chunk') {
        setMessages((prev) => {
          // 创建新数组，避免直接修改原数组
          const newMessages = prev.map(msg => ({ ...msg }))
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.role === 'assistant') {
            // 直接追加新内容（流式传输是逐字符的，不需要检查重复）
            const newContent = data.content || ''
            lastMessage.content = (lastMessage.content || '') + newContent
          }
          return newMessages
        })
      } else if (data.type === 'end') {
        setLoading(false)
        scrollToBottom()
      } else if (data.type === 'error') {
        setLoading(false)
        alert(`错误: ${data.message}`)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      setLoading(false)
    }

    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
    }

    wsRef.current = ws
    return ws
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageContent = input
    setInput('')
    setLoading(true)

    // 确保WebSocket连接
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      const ws = connectWebSocket()
      // 等待连接建立
      ws.onopen = () => {
        console.log('WebSocket连接已建立，发送消息')
        ws.send(JSON.stringify({ message: messageContent }))
      }
    } else if (wsRef.current.readyState === WebSocket.CONNECTING) {
      // 如果正在连接，等待连接完成
      const checkConnection = setInterval(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          clearInterval(checkConnection)
          wsRef.current.send(JSON.stringify({ message: messageContent }))
        } else if (wsRef.current && wsRef.current.readyState === WebSocket.CLOSED) {
          clearInterval(checkConnection)
          // 重新连接
          const ws = connectWebSocket()
          ws.onopen = () => {
            ws.send(JSON.stringify({ message: messageContent }))
          }
        }
      }, 100)
    } else if (wsRef.current.readyState === WebSocket.OPEN) {
      // 连接已建立，直接发送
      wsRef.current.send(JSON.stringify({ message: messageContent }))
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="space-y-6 relative p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title bg-gradient-to-r from-sky-400 via-indigo-400 to-rose-400 bg-clip-text text-transparent">
            通信星球 · 智能对话
          </h1>
          <p className="mt-2 text-lg text-slate-600 dark:text-slate-200">
            在宇宙中央的玻璃气泡里，你和智能体小王子进行创作对话。
          </p>
        </div>
        <img
          src="/飞翔小王子.png"
          alt="飞翔小王子"
          className="hidden md:block h-24 fly-little-prince drop-shadow-[0_0_25px_rgba(129,140,248,0.6)]"
        />
      </header>

      <section className="chat-bubble p-4 md:p-6 min-h-[360px] flex flex-col">
        {/* 消息区域 */}
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6 overflow-hidden">
                <img
                  src="/飞翔小王子.png"
                  alt="智能助手"
                  className="w-full h-full object-contain"
                />
              </div>
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-2">
                欢迎使用影视制作教育智能体
              </h2>
            <p className="text-gold-700 dark:text-slate-400 max-w-md">
              我是您的专业影视制作教育助手，可以帮您解答关于影视制作、摄影、剪辑、后期制作等方面的问题。
            </p>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
              {[
                '什么是影视制作流程？',
                '如何拍摄高质量的视频？',
                '后期制作有哪些技巧？',
                '如何选择合适的摄影设备？',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion)
                    setTimeout(sendMessage, 100)
                  }}
                  className="p-4 glass-card hover:bg-white/20 dark:hover:bg-white/10 rounded-lg text-left text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-all card-hover"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-4 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden">
                  <img
                    src="/飞翔小王子.png"
                    alt="智能助手"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              <div
                className={`max-w-3xl ${
                  message.role === 'user'
                    ? 'message-bubble bg-gradient-to-r from-emerald-400/80 via-sky-400/80 to-indigo-400/80'
                    : 'message-bubble'
                }`}
              >
                <div className="break-words">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0 text-slate-700 dark:text-slate-200 leading-relaxed">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-slate-700 dark:text-slate-200 ml-4">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-slate-700 dark:text-slate-200 ml-4">{children}</ol>,
                      li: ({ children }) => <li className="mb-1">{children}</li>,
                      code: ({ children, className }) => {
                        const isInline = !className
                        return isInline ? (
                          <code className="bg-slate-800/50 dark:bg-slate-700/50 px-1.5 py-0.5 rounded text-xs text-slate-200 font-mono">{children}</code>
                        ) : (
                          <code className="block bg-slate-900/80 dark:bg-slate-800/80 p-3 rounded-lg text-xs overflow-x-auto text-slate-200 font-mono my-2">{children}</code>
                        )
                      },
                      pre: ({ children }) => <pre className="mb-2">{children}</pre>,
                      strong: ({ children }) => <strong className="font-semibold text-slate-800 dark:text-slate-100">{children}</strong>,
                      em: ({ children }) => <em className="italic">{children}</em>,
                      h1: ({ children }) => (
                        <h1 className="text-2xl md:text-3xl font-bold mb-3 mt-4 first:mt-0 text-slate-800 dark:text-slate-100 border-b border-slate-300 dark:border-slate-700 pb-2">
                          {children}
                        </h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="text-xl md:text-2xl font-bold mb-2 mt-3 first:mt-0 text-slate-800 dark:text-slate-100">
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="text-lg md:text-xl font-semibold mb-2 mt-2 first:mt-0 text-slate-800 dark:text-slate-100">
                          {children}
                        </h3>
                      ),
                      h4: ({ children }) => (
                        <h4 className="text-base md:text-lg font-semibold mb-1 mt-2 text-slate-800 dark:text-slate-100">
                          {children}
                        </h4>
                      ),
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-amber-400 dark:border-amber-500 pl-4 py-2 my-2 italic text-slate-600 dark:text-slate-300 bg-amber-50/30 dark:bg-amber-900/10 rounded-r">
                          {children}
                        </blockquote>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
              {message.role === 'user' && (
                <div className="w-10 h-10 glass rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-6 h-6 text-gold dark:text-white" />
                </div>
              )}
            </div>
          ))
        )}
        {loading && messages.length > 0 && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden">
              <img
                src="/飞翔小王子.png"
                alt="智能助手"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="glass dark:bg-purple-900/10 rounded-2xl px-6 py-4 border border-paper-300 dark:border-purple-900/50">
              <Loader2 className="w-5 h-5 text-gold-600 dark:text-purple-400 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

        {/* 输入区 */}
        <div className="mt-4 flex gap-3">
          <input
            className="flex-1 rounded-2xl bg-slate-950/40 border border-slate-600/60 px-4 py-2 text-sm md:text-base text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-400/70"
            placeholder="对小王子说点什么……"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
          />
          <button 
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="rounded-2xl px-4 py-2 text-sm md:text-base bg-gradient-to-r from-sky-400 to-indigo-500 text-white shadow-[0_0_20px_rgba(56,189,248,0.5)] hover:shadow-[0_0_30px_rgba(56,189,248,0.8)] transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '发送'}
          </button>
        </div>
      </section>
    </div>
  )
}

