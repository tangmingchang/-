import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { chatApi, Conversation, ChatMessage } from '../utils/api'
import { format } from 'date-fns'

export default function HistoryPage() {
  const [expandedConversations, setExpandedConversations] = useState<Set<number>>(new Set())
  const [messagesMap, setMessagesMap] = useState<Map<number, ChatMessage[]>>(new Map())
  const [loadingMessages, setLoadingMessages] = useState<Set<number>>(new Set())
  
  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getConversations,
  })

  const toggleConversation = async (convId: number) => {
    const newExpanded = new Set(expandedConversations)
    
    if (newExpanded.has(convId)) {
      // 收起
      newExpanded.delete(convId)
    } else {
      // 展开 - 加载消息
      newExpanded.add(convId)
      if (!messagesMap.has(convId)) {
        setLoadingMessages(prev => new Set(prev).add(convId))
        try {
          const messages = await chatApi.getMessages(String(convId))
          setMessagesMap(prev => new Map(prev).set(convId, messages))
        } catch (error) {
          console.error('加载消息失败:', error)
        } finally {
          setLoadingMessages(prev => {
            const newSet = new Set(prev)
            newSet.delete(convId)
            return newSet
          })
        }
      }
    }
    
    setExpandedConversations(newExpanded)
  }

  return (
    <div className="flex flex-col h-full bg-gradient-paper dark:bg-transparent p-6 transition-all duration-300 relative z-10">
      <div className="max-w-4xl mx-auto w-full">
        {/* 标题 */}
        <div className="mb-6">
          <h1 className="page-title bg-gradient-to-r from-sky-400 via-indigo-400 to-rose-400 bg-clip-text text-transparent mb-2">
            通信星球 · 对话日志
          </h1>
          <p className="text-lg text-gold-700 dark:text-slate-400">
            这里记录了你和小王子在通信星球上的每一次交流与灵感火花。
          </p>
        </div>

        {/* 对话列表 */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-gold-600 dark:text-purple-400 animate-spin" />
          </div>
        ) : conversations && conversations.length > 0 ? (
          <div className="space-y-4">
            {conversations.map((conv: Conversation) => {
              const convId = typeof conv.id === 'string' ? parseInt(conv.id) : conv.id
              const isExpanded = expandedConversations.has(convId)
              const messages = messagesMap.get(convId) || []
              const isLoading = loadingMessages.has(convId)
              
              return (
                <div
                  key={conv.id}
                  className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl border border-paper-300 dark:border-purple-900/50 hover:bg-white/30 dark:hover:bg-purple-900/30 transition-all"
                >
                  <div
                    className="flex items-start gap-4 p-6 cursor-pointer"
                    onClick={() => toggleConversation(convId)}
                  >
                    <div className="w-12 h-12 bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-xl flex items-center justify-center flex-shrink-0">
                      <MessageSquare className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-gold dark:text-white font-semibold text-lg mb-1">
                          {conv.title}
                        </h3>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gold-600 dark:text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gold-600 dark:text-slate-400" />
                        )}
                      </div>
                      <p className="text-gold-700 dark:text-slate-400 text-sm">
                        {conv.created_at &&
                          format(new Date(conv.created_at), 'yyyy-MM-dd HH:mm')}
                      </p>
                    </div>
                  </div>
                  
                  {/* 展开的对话内容 */}
                  {isExpanded && (
                    <div className="px-6 pb-6 pt-2 border-t border-paper-300/50 dark:border-purple-900/50">
                      {isLoading ? (
                        <div className="flex justify-center py-4">
                          <Loader2 className="w-5 h-5 text-gold-600 dark:text-purple-400 animate-spin" />
                        </div>
                      ) : messages.length > 0 ? (
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                          {messages.map((msg, index) => (
                            <div
                              key={index}
                              className={`p-3 rounded-lg ${
                                msg.role === 'user'
                                  ? 'bg-gradient-to-r from-emerald-400/20 via-sky-400/20 to-indigo-400/20 ml-auto max-w-[80%]'
                                  : 'bg-slate-100/50 dark:bg-slate-800/50 mr-auto max-w-[80%]'
                              }`}
                            >
                              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
                                {msg.role === 'user' ? '你' : '小王子'}
                              </div>
                              <div className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-wrap">
                                {msg.content}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gold-600 dark:text-slate-400 text-sm text-center py-4">
                          暂无消息
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-20 h-20 glass rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-10 h-10 text-gold-600 dark:text-slate-400" />
            </div>
            <p className="text-gold-700 dark:text-slate-400">暂无对话记录</p>
            <p className="text-gold-600 dark:text-slate-500 text-sm mt-2">
              开始一个新的对话，记录将显示在这里
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

