import { useState, useEffect, useRef } from 'react'
import { X, ChevronLeft, ChevronRight, BookOpen, ZoomIn, ZoomOut } from 'lucide-react'

interface PDFViewerProps {
  filePath: string
  chapterTitle?: string
  chapterPage?: number
  onClose: () => void
}

export default function PDFViewer({ filePath, chapterTitle, chapterPage, onClose }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.2)
  const [loading, setLoading] = useState(true)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const pdfRef = useRef<any>(null) // 保存PDF对象，避免重复加载

  useEffect(() => {
    if (chapterPage) {
      setPageNumber(chapterPage)
    }
  }, [chapterPage])

  useEffect(() => {
    loadPDF()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filePath])

  const loadPDF = async () => {
    try {
      setLoading(true)
      // 动态导入pdfjs-dist
      const pdfjsLib = await import('pdfjs-dist')
      
      // 设置worker - 使用pdfjs-dist包自带的worker文件
      // 使用unpkg CDN或jsdelivr CDN，这些更可靠
      if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
        // 方法1: 使用unpkg CDN（推荐，更稳定）
        pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`
        
        // 如果unpkg失败，可以尝试jsdelivr
        // pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`
      }
      
      // 加载PDF文件
      // 如果路径不是完整URL，根据路径前缀使用不同的后端API端点
      // 使用相对路径，通过nginx代理
      // 开发环境强制使用相对路径
      const API_URL = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '')
      let pdfUrl = filePath
      if (!filePath.startsWith('http://') && !filePath.startsWith('https://')) {
        if (filePath.startsWith('/books/') || filePath.startsWith('/knowledge/')) {
          // 使用后端API路径（/books/或/knowledge/）
          pdfUrl = `${API_URL}${filePath}`
        } else if (!filePath.startsWith('/')) {
          // 相对路径，尝试/knowledge/端点（知识库文档）
          pdfUrl = `${API_URL}/knowledge/${filePath}`
        } else {
          // 其他绝对路径，直接使用
          pdfUrl = `${API_URL}${filePath}`
        }
      }
      const loadingTask = pdfjsLib.getDocument(pdfUrl)
      const pdf = await loadingTask.promise
      
      pdfRef.current = pdf // 保存PDF对象
      setNumPages(pdf.numPages)
      setLoading(false)
      
      // 渲染当前页
      await renderPage(pdf, pageNumber)
    } catch (error) {
      console.error('加载PDF失败:', error)
      setLoading(false)
    }
  }

  const renderPage = async (pdf: any, pageNum: number) => {
    if (!canvasRef.current || !pdf) return
    
    try {
      const page = await pdf.getPage(pageNum)
      const viewport = page.getViewport({ scale })
      const canvas = canvasRef.current
      const context = canvas.getContext('2d')
      
      canvas.height = viewport.height
      canvas.width = viewport.width
      
      const renderContext = {
        canvasContext: context,
        viewport: viewport
      }
      
      await page.render(renderContext).promise
    } catch (error) {
      console.error('渲染页面失败:', error)
    }
  }

  // 当页码或缩放改变时，只重新渲染页面，不重新加载PDF
  useEffect(() => {
    if (!loading && pdfRef.current && numPages > 0) {
      renderPage(pdfRef.current, pageNumber)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageNumber, scale])

  const goToPrevPage = () => {
    if (pageNumber > 1) {
      setPageNumber(pageNumber - 1)
    }
  }

  const goToNextPage = () => {
    if (pageNumber < numPages) {
      setPageNumber(pageNumber + 1)
    }
  }

  const zoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3))
  }

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5))
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
        <div className="text-white text-lg">加载PDF中...</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/90 z-50 flex flex-col">
      {/* 顶部工具栏 */}
      <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          {chapterTitle && (
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              <span className="font-medium">{chapterTitle}</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={zoomOut}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm">{Math.round(scale * 100)}%</span>
            <button
              onClick={zoomIn}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={goToPrevPage}
              disabled={pageNumber <= 1}
              className="p-2 hover:bg-gray-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="text-sm min-w-[80px] text-center">
              第 {pageNumber} / {numPages} 页
            </span>
            <button
              onClick={goToNextPage}
              disabled={pageNumber >= numPages}
              className="p-2 hover:bg-gray-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* PDF内容区域 */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto flex items-center justify-center p-4"
      >
        <canvas
          ref={canvasRef}
          className="shadow-2xl"
        />
      </div>
    </div>
  )
}



