import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Upload,
  FileText,
  Trash2,
  Loader2,
  BookOpen,
} from 'lucide-react'
import { knowledgeApi, Document } from '../utils/api'
import PDFViewer from '../components/PDFViewer'

export default function KnowledgePage() {
  const [selectedPDF, setSelectedPDF] = useState<{ filePath: string; title?: string } | null>(null)

  const queryClient = useQueryClient()

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: knowledgeApi.getDocuments,
  })

  const uploadMutation = useMutation({
    mutationFn: knowledgeApi.uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: knowledgeApi.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (
      Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
    )
  }

  const docCount = documents?.length || 0

  return (
    <div className="flex flex-col h-full bg-gradient-paper dark:bg-transparent p-6 md:p-8 transition-all duration-300 relative z-10">
      <div className="max-w-6xl mx-auto w-full space-y-7 md:space-y-8">
        {/* 顶部：书本星球标题 + 简短说明 + 小统计 */}
        <header className="animate-slide-up">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="page-title bg-gradient-to-r from-amber-400 via-rose-400 to-sky-400 bg-clip-text text-transparent mb-2">
                书本星球 · 知识库管理
              </h1>
              <p className="text-lg text-gold-700 dark:text-purple-200">
                这里是小王子的「知识星空书架」，你上传的每一份文档都会变成一颗微亮的星。
              </p>
              <p className="mt-1 text-sm text-gold-600 dark:text-slate-300">
                在星光书架上管理文档，上传新的学习资料。
              </p>
            </div>
            <div className="glass-card dark:bg-purple-900/20 rounded-2xl px-4 py-3 flex items-center gap-3 border border-paper-300 dark:border-purple-900/60">
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-amber-300 to-rose-300 flex items-center justify-center shadow-[0_0_18px_rgba(251,191,36,0.8)]">
                <BookOpen className="w-5 h-5 text-slate-900" />
              </div>
              <div className="text-xs text-gold-700 dark:text-purple-100 leading-snug">
                <div>
                  当前书架上共有{' '}
                  <span className="font-semibold text-amber-600 dark:text-amber-300">
                    {docCount}
                  </span>{' '}
                  本文档
                </div>
                <div className="text-[11px] text-gold-600 dark:text-slate-300">
                  适合存放课程讲义、脚本示例、剪辑手册等资料
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* 上传区（文档入口） */}
        <section className="glass-card dark:bg-purple-900/10 backdrop-blur-lg rounded-2xl p-5 md:p-6 border border-paper-300 dark:border-purple-900/50 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-1">
                上传文档 · 放上新书
              </h2>
              <p className="text-sm text-gold-700 dark:text-purple-200">
                支持上传 txt / pdf / doc / docx / md，用于教学资料、剧本示例、技术手册等。
              </p>
            </div>
            <label className="px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 cursor-pointer transition-all flex items-center gap-2 font-medium text-sm">
              <Upload className="w-4 h-4" />
              选择文件
              <input
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                accept=".txt,.pdf,.doc,.docx,.md"
              />
            </label>
          </div>

          <div className="text-xs text-gold-600 dark:text-slate-400">
            建议：把课程讲义、评分标准、剪辑操作步骤、色彩搭配表等都集中放在这里，方便学生随时检索。
          </div>

          {uploadMutation.isPending && (
            <div className="flex items-center gap-2 text-gold-600 dark:text-purple-300 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="dark:text-purple-200">上传中...</span>
            </div>
          )}
          {uploadMutation.isSuccess && (
            <div className="text-sm text-green-600 dark:text-emerald-400">
              上传成功！文档已经被放到书本星球的星光书架上。
            </div>
          )}
          {uploadMutation.isError && (
            <div className="text-sm text-red-600 dark:text-red-400">
              上传失败，请重试。
            </div>
          )}
        </section>

        {/* 星光书架（文档列表） */}
        <section className="glass-card dark:bg-purple-900/10 backdrop-blur-lg rounded-2xl p-5 md:p-6 border border-paper-300 dark:border-purple-900/50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-1">
                星光书架 · 文档列表
              </h2>
              <p className="text-sm text-gold-700 dark:text-purple-200">
                每一个文档是一本小书，可以随时删除或替换，保持你的知识库干净、清晰。
              </p>
            </div>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-8 h-8 text-gold-600 dark:text-purple-300 animate-spin" />
            </div>
          ) : documents && documents.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
              {documents.map((doc: Document) => {
                // 检查是否是PDF文件
                const isPDF = doc.file_type === 'application/pdf' || doc.filename?.toLowerCase().endsWith('.pdf')
                const filePath = (doc as any).file_path || doc.filename
                
                return (
                  <article
                    key={doc.id}
                    className={`flex items-center justify-between glass rounded-xl p-4 border border-paper-300 dark:border-purple-900/50 hover:bg-white/40 dark:hover:bg-purple-900/40 transition-all ${
                      isPDF ? 'cursor-pointer' : ''
                    } card-hover`}
                    onClick={() => {
                      if (isPDF && filePath) {
                        // 构建PDF路径
                        let pdfPath = filePath
                        // 如果路径是相对路径或包含knowledge_base，转换为/knowledge/路径
                        if (!pdfPath.startsWith('/') && !pdfPath.startsWith('http')) {
                          // 直接使用文件名，通过/knowledge/端点访问
                          pdfPath = `/knowledge/${doc.filename}`
                        } else if (pdfPath.includes('knowledge_base')) {
                          // 如果路径包含knowledge_base，提取文件名
                          const filename = pdfPath.split(/[\/\\]/).pop() || doc.filename
                          pdfPath = `/knowledge/${filename}`
                        } else if (!pdfPath.startsWith('http')) {
                          // 如果已经是绝对路径但不是http，确保以/knowledge/开头
                          if (!pdfPath.startsWith('/knowledge/')) {
                            const filename = pdfPath.split(/[\/\\]/).pop() || doc.filename
                            pdfPath = `/knowledge/${filename}`
                          }
                        }
                        setSelectedPDF({
                          filePath: pdfPath,
                          title: doc.filename
                        })
                      }
                    }}
                  >
                    <div className="flex items-center gap-4 min-w-0 flex-1">
                      <div className="w-11 h-11 bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-xl flex items-center justify-center shadow-md">
                        <FileText className="w-5 h-5 text-white" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm md:text-base text-gold dark:text-white font-medium truncate">
                          {doc.filename}
                        </p>
                        <p className="text-[11px] md:text-xs text-gold-700 dark:text-purple-200 mt-0.5">
                          {formatFileSize(doc.file_size)} · {doc.file_type}
                        </p>
                        {isPDF && (
                          <p className="text-[10px] text-amber-600 dark:text-amber-400 mt-1">
                            点击查看PDF内容
                          </p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation() // 阻止触发父元素的点击事件
                        deleteMutation.mutate(doc.id)
                      }}
                      disabled={deleteMutation.isPending}
                      className="p-2 text-red-400 hover:text-red-500 hover:bg-red-400/10 rounded-lg transition-all ml-3 shrink-0"
                      title="从书架上移除"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </article>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <FileText className="w-10 h-10 text-gold-600 dark:text-purple-300 mb-3 animate-float" />
              <p className="text-sm text-gold-700 dark:text-purple-100 mb-1">
                星光书架上暂时还没有任何文档。
              </p>
              <p className="text-xs text-gold-600 dark:text-slate-400 mb-3">
                可以先在上方上传一两份课程文档，试着用星空检索台搜一搜。
              </p>
            </div>
          )}
        </section>
      </div>
      
      {/* PDF查看器 */}
      {selectedPDF && (
        <PDFViewer
          filePath={selectedPDF.filePath}
          chapterTitle={selectedPDF.title}
          onClose={() => setSelectedPDF(null)}
        />
      )}
    </div>
  )
}
