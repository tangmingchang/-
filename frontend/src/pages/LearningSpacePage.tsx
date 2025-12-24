import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Play, FileText, Search, ExternalLink, Video, Link as LinkIcon, Plus, X } from 'lucide-react'
import { api } from '../utils/api'
import PDFViewer from '../components/PDFViewer'

interface Course {
  id: number
  name: string
  description: string
  created_at: string
}

interface Chapter {
  id: number
  title: string
  content: string
  order: number
}

interface CourseResource {
  id: number
  course_id: number
  title: string
  resource_type: string
  file_path: string
  description: string
  created_at: string
}

export default function LearningSpacePage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
  const [chapterContent, setChapterContent] = useState<string>('')
  const [loadingContent, setLoadingContent] = useState(false)
  const [resources, setResources] = useState<CourseResource[]>([])
  const [activeTab, setActiveTab] = useState<'chapters' | 'resources'>('chapters')
  const [loading, setLoading] = useState(true)
  const [selectedPDF, setSelectedPDF] = useState<{ filePath: string; title?: string } | null>(null)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [showCreateCourse, setShowCreateCourse] = useState(false)
  const [newCourseName, setNewCourseName] = useState('')
  const [newCourseDesc, setNewCourseDesc] = useState('')
  const [showCreateChapter, setShowCreateChapter] = useState(false)
  const [newChapterTitle, setNewChapterTitle] = useState('')
  const [newChapterContent, setNewChapterContent] = useState('')
  const contentRef = useRef<HTMLDivElement>(null)
  
  const isTeacher = userInfo?.role === 'teacher' || userInfo?.role === 'admin'
  const isStudent = userInfo?.role === 'student'

  useEffect(() => {
    loadUserInfo()
    loadCourses()
  }, [])
  
  const loadUserInfo = async () => {
    try {
      const res = await api.get('/api/auth/me')
      setUserInfo(res.data)
    } catch (error) {
      console.error('加载用户信息失败:', error)
    }
  }

  useEffect(() => {
    if (selectedCourse) {
      loadChapters(selectedCourse.id)
      loadResources(selectedCourse.id)
    }
  }, [selectedCourse])

  const loadCourses = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    
    try {
      const res = await api.get('/api/courses/')
      setCourses(res.data)
      if (res.data.length > 0) {
        setSelectedCourse(res.data[0])
      }
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载课程失败:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadChapters = async (courseId: number) => {
    try {
      const res = await api.get(`/api/courses/${courseId}/chapters`)
      setChapters(res.data || [])
    } catch (error: any) {
      console.error('加载章节失败:', error)
      // 如果加载失败，清空章节列表并显示错误信息
      setChapters([])
      if (error.response?.status === 403) {
        console.error('无权访问此课程的章节')
      } else if (error.response?.status === 404) {
        console.error('课程不存在')
      }
    }
  }

  const loadResources = async (courseId: number) => {
    try {
      const res = await api.get(`/api/courses/${courseId}/resources`)
      setResources(res.data || [])
    } catch (error: any) {
      console.error('加载资源失败:', error)
      // 如果加载失败，清空资源列表
      setResources([])
      if (error.response?.status === 403) {
        console.error('无权访问此课程的资源')
      } else if (error.response?.status === 404) {
        console.error('课程不存在')
      }
    }
  }
  
  const createCourse = async () => {
    if (!newCourseName.trim()) {
      alert('请输入课程名称')
      return
    }
    try {
      const res = await api.post('/api/courses/', {
        name: newCourseName,
        description: newCourseDesc
      })
      setCourses([...courses, res.data])
      setSelectedCourse(res.data)
      setShowCreateCourse(false)
      setNewCourseName('')
      setNewCourseDesc('')
      alert('课程创建成功！')
    } catch (error: any) {
      alert('创建课程失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const createChapter = async () => {
    if (!selectedCourse || !newChapterTitle.trim()) {
      alert('请先选择课程并输入章节标题')
      return
    }
    try {
      const res = await api.post(`/api/courses/${selectedCourse.id}/chapters`, {
        title: newChapterTitle,
        content: newChapterContent,
        order: chapters.length + 1
      })
      setChapters([...chapters, res.data])
      setShowCreateChapter(false)
      setNewChapterTitle('')
      setNewChapterContent('')
      alert('章节创建成功！')
    } catch (error: any) {
      alert('创建章节失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getResourceIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'video':
        return <Video className="w-5 h-5" />
      case 'pdf':
        return <FileText className="w-5 h-5" />
      case 'link':
        return <LinkIcon className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  const openResource = (resource: CourseResource) => {
    if (!resource.file_path) return
    
    const resourceType = resource.resource_type?.toLowerCase()
    
    // 如果是PDF类型，检查是否是书籍搜索链接
    if (resourceType === 'pdf') {
      if (resource.file_path.startsWith('book_search:')) {
        // 书籍搜索链接，使用中间页面实现两层跳转
        const searchQuery = resource.file_path.replace('book_search:', '')
        // 跳转到中间页面，由中间页面处理搜索和跳转
        const searchUrl = `/book-search.html?q=${encodeURIComponent(searchQuery)}`
        window.open(searchUrl, '_blank', 'noopener,noreferrer')
        return
      } else if (resource.file_path.startsWith('/books/') || resource.file_path.includes('.pdf')) {
        // 本地PDF文件，使用PDFViewer
        let pdfPath = resource.file_path
        if (!pdfPath.startsWith('/')) {
          pdfPath = '/' + pdfPath
        }
        setSelectedPDF({
          filePath: pdfPath,
          title: resource.title
        })
        return
      } else if (resource.file_path.startsWith('http://') || resource.file_path.startsWith('https://')) {
        // 外部PDF链接，直接在新窗口打开
        window.open(resource.file_path, '_blank', 'noopener,noreferrer')
        return
      }
    }
    
    // 视频资源：直接跳转到外部链接
    if (resourceType === 'video') {
      if (resource.file_path.startsWith('http://') || resource.file_path.startsWith('https://')) {
        window.open(resource.file_path, '_blank', 'noopener,noreferrer')
        return
      }
    }
    
    // 其他类型资源（link等）
    if (resourceType === 'link' || resource.file_path.startsWith('http://') || resource.file_path.startsWith('https://')) {
      window.open(resource.file_path, '_blank', 'noopener,noreferrer')
    } else {
      window.open(resource.file_path, '_blank', 'noopener,noreferrer')
    }
  }

  const loadChapterContent = async (chapter: Chapter) => {
    setLoadingContent(true)
    setChapterContent('')
    
    try {
      // 直接使用数据库中的内容（已经更新为详细版本）
      const dbContent = chapter.content || ''
      if (dbContent && dbContent.length > 50) {
        // 如果数据库内容存在，直接使用
        setChapterContent(dbContent)
        setLoadingContent(false)
        return
      }
      
      // 如果数据库内容不够，尝试从PDF资源中提取（仅本地PDF）
      const pdfResources = resources.filter(r => {
        const type = r.resource_type?.toLowerCase()
        const path = r.file_path || ''
        // 只处理本地PDF文件，排除book_search链接和外部链接
        return type === 'pdf' && 
               !path.startsWith('book_search:') &&
               !path.startsWith('http://') &&
               !path.startsWith('https://') &&
               (path.startsWith('/books/') || path.includes('.pdf'))
      })
      
      if (pdfResources.length > 0) {
        // 使用第一个PDF资源
        const pdfResource = pdfResources[0]
        // 从file_path中提取文件名
        let filename = pdfResource.file_path
        if (filename.startsWith('/books/')) {
          filename = filename.replace('/books/', '')
        } else if (filename.includes('/')) {
          filename = filename.split('/').pop() || filename
        }
        
        try {
          const res = await api.get(`/api/pdf/chapter-content/${encodeURIComponent(filename)}`, {
            params: {
              chapter_title: chapter.title
            }
          })
          
          if (res.data?.content && res.data.content.length > 100) {
            // 如果从PDF提取到了详细内容，使用PDF内容
            setChapterContent(res.data.content)
          } else {
            // 如果PDF内容不够，使用数据库的详细描述
            const dbContent = chapter.content || ''
            // 如果数据库内容足够详细，使用它；否则提示查看资料
            if (dbContent && dbContent.length > 100) {
              setChapterContent(dbContent)
            } else {
              setChapterContent(dbContent || '本章节暂无详细内容，请查看相关学习资料。')
            }
          }
        } catch (error: any) {
          console.error('从PDF加载章节内容失败:', error)
          // 如果PDF加载失败，使用数据库的详细内容
          const dbContent = chapter.content || ''
          if (dbContent && dbContent.length > 100) {
            setChapterContent(dbContent)
          } else {
            setChapterContent(dbContent || '本章节暂无详细内容，请查看相关学习资料。')
          }
        }
      } else {
        // 没有PDF资源，使用数据库的详细内容
        const dbContent = chapter.content || ''
        if (dbContent && dbContent.length > 100) {
          setChapterContent(dbContent)
        } else {
          setChapterContent(dbContent || '本章节暂无详细内容，请查看相关学习资料。')
        }
      }
    } catch (error: any) {
      console.error('加载章节内容失败:', error)
      const dbContent = chapter.content || ''
      if (dbContent && dbContent.length > 100) {
        setChapterContent(dbContent)
      } else {
        setChapterContent(dbContent || '本章节暂无详细内容，请查看相关学习资料。')
      }
    } finally {
      setLoadingContent(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gold dark:text-white text-lg animate-pulse">加载中...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex overflow-hidden bg-gradient-paper dark:bg-transparent transition-all duration-300 relative z-10">
      {/* 左侧课程列表 */}
      <div className="w-80 glass border-r border-paper-300 dark:border-dark-border overflow-y-auto">
        <div className="p-6 border-b border-paper-300 dark:border-dark-border">
          <h2 className="section-title text-slate-800 dark:text-slate-50 mb-4">课程列表</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
            <input
              type="text"
              placeholder="搜索课程..."
              className="w-full pl-10 pr-4 py-2 glass rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
            />
          </div>
        </div>
        <div className="p-4 space-y-2">
          {courses.map((course) => (
            <div
              key={course.id}
              onClick={() => setSelectedCourse(course)}
              className="relative rounded-2xl p-[1px] bg-gradient-to-br from-amber-200/60 via-transparent to-sky-300/60 cursor-pointer transition-all card-hover"
            >
              <div className="h-full rounded-2xl bg-slate-50/90 dark:bg-slate-900/90 px-4 py-3 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <h3 className="card-title text-slate-800 dark:text-slate-50">
                    {course.name}
                  </h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-indigo-500/10 text-indigo-500">
                    课程
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
                  {course.description}
                </p>
              </div>
              {/* 小星星点缀 */}
              <span className="absolute -top-1 -right-1 text-amber-300 text-sm">
                ✦
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 overflow-y-auto p-8">
        {!localStorage.getItem('access_token') ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <BookOpen className="w-16 h-16 text-slate-400 dark:text-slate-500 mx-auto mb-4 animate-float" />
              <p className="text-gold-700 dark:text-slate-400 mb-4">请先登录以查看课程</p>
              <Link
                to="/login"
                className="inline-block px-6 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all card-hover"
              >
                立即登录
              </Link>
            </div>
          </div>
        ) : selectedCourse ? (
          <>
            <div className="mb-6 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div>
                <h1 className="page-title bg-gradient-to-r from-amber-400 via-rose-400 to-sky-400 bg-clip-text text-transparent">
                  书本星球 · 学习空间
                </h1>
                <p className="mt-2 text-lg text-slate-600 dark:text-slate-200">
                  这里是你的「知识星空书架」，课程像一颗颗小行星围绕着你。
                </p>
                <h2 className="mt-4 text-3xl md:text-4xl font-bold text-gold dark:text-white">
                  {selectedCourse.name}
                </h2>
                <p className="mt-1 text-gold-700 dark:text-slate-300">
                  {selectedCourse.description}
                </p>
              </div>

              {/* 学习玫瑰园小插图 */}
              <div className="hidden md:flex glass-card items-center gap-3 px-4 py-3">
                <img
                  src="/玫瑰小王子.png"
                  alt="学习玫瑰园"
                  className="h-20 floating"
                />
                <span className="text-sm text-rose-500 dark:text-rose-300 max-w-[180px]">
                  继续浇灌你的每一朵玫瑰，它们会在你的作品里开花。
                </span>
              </div>
            </div>

            {/* 标签页切换 */}
            <div className="flex gap-2 mb-6 border-b border-paper-300 dark:border-dark-border">
              <button
                onClick={() => setActiveTab('chapters')}
                className={`px-6 py-3 font-medium transition-all ${
                  activeTab === 'chapters'
                    ? 'border-b-2 border-primary-500 dark:border-neon-blue text-primary-500 dark:text-neon-blue'
                    : 'text-gold-700 dark:text-slate-400 hover:text-gold dark:hover:text-slate-300'
                }`}
              >
                章节 ({chapters.length})
              </button>
              <button
                onClick={() => setActiveTab('resources')}
                className={`px-6 py-3 font-medium transition-all ${
                  activeTab === 'resources'
                    ? 'border-b-2 border-primary-500 dark:border-neon-blue text-primary-500 dark:text-neon-blue'
                    : 'text-gold-700 dark:text-slate-400 hover:text-gold dark:hover:text-slate-300'
                }`}
              >
                学习资源 ({resources.length})
              </button>
            </div>

            {activeTab === 'chapters' ? (
              chapters.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-16 h-16 text-slate-400 dark:text-slate-500 mx-auto mb-4 animate-float" />
                <p className="text-gold-700 dark:text-slate-400">该课程暂无章节内容</p>
              </div>
            ) : (
              <div className="space-y-4">
                {chapters.map((chapter) => (
                  <div
                    key={chapter.id}
                    data-chapter-id={chapter.id}
                    className={`glass rounded-xl p-6 card-hover animate-slide-up ${selectedChapter?.id === chapter.id ? 'ring-2 ring-primary-500' : ''}`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-lg flex items-center justify-center flex-shrink-0">
                        <span className="text-white font-bold">{chapter.order}</span>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-gold dark:text-white mb-4">{chapter.title}</h3>
                        {/* 不显示简短描述，详细内容在展开时显示 */}
                        <div className="flex gap-3">
                          <button
                            onClick={async () => {
                              // 如果已经选中且已展开，则收起；否则展开
                              if (selectedChapter?.id === chapter.id && chapterContent) {
                                setSelectedChapter(null)
                                setChapterContent('')
                              } else {
                                setSelectedChapter(chapter)
                                setActiveTab('chapters')
                                await loadChapterContent(chapter)
                                // 滚动到内容显示区域（等待DOM更新）
                                setTimeout(() => {
                                  const chapterElement = document.querySelector(`[data-chapter-id="${chapter.id}"]`)
                                  if (chapterElement) {
                                    chapterElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
                                  }
                                }, 300)
                              }
                            }}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all card-hover"
                          >
                            <Play className="w-4 h-4" />
                            {selectedChapter?.id === chapter.id && chapterContent ? '收起内容' : '开始学习'}
                          </button>
                          <button
                            onClick={() => setActiveTab('resources')}
                            className="flex items-center gap-2 px-4 py-2 glass text-gold dark:text-slate-300 rounded-lg hover:bg-white/20 dark:hover:bg-white/10 transition-all card-hover"
                          >
                            <FileText className="w-4 h-4" />
                            查看资料
                          </button>
                        </div>
                        
                        {/* 章节详细内容展开区域 - PDF样式 */}
                        {selectedChapter?.id === chapter.id && (
                          <div ref={contentRef} className="mt-6 pt-6 border-t border-paper-300 dark:border-dark-border">
                            {loadingContent ? (
                              <div className="flex items-center justify-center py-8">
                                <div className="text-gold-700 dark:text-slate-300 animate-pulse">正在加载章节内容...</div>
                              </div>
                            ) : (
                              <div className="bg-white dark:bg-slate-900 rounded-lg p-6 shadow-inner border border-paper-200 dark:border-slate-700">
                                <div className="text-gold-900 dark:text-slate-100 whitespace-pre-line leading-relaxed font-serif text-base max-h-[600px] overflow-y-auto prose prose-lg dark:prose-invert max-w-none">
                                  {chapterContent || chapter.content || '本章节暂无详细内容，请查看相关学习资料。'}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
            ) : (
              resources.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-slate-400 dark:text-slate-500 mx-auto mb-4 animate-float" />
                  <p className="text-gold-700 dark:text-slate-400">该课程暂无学习资源</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {resources.map((resource) => (
                    <div
                      key={resource.id}
                      onClick={() => openResource(resource)}
                      className="glass rounded-xl p-6 card-hover animate-slide-up group cursor-pointer"
                    >
                      <div className="flex items-start gap-4 mb-3">
                        <div className="w-12 h-12 bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-lg flex items-center justify-center flex-shrink-0 text-white">
                          {getResourceIcon(resource.resource_type)}
                        </div>
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-gold dark:text-white mb-1 group-hover:text-primary-500 dark:group-hover:text-neon-blue transition-colors">
                            {resource.title}
                          </h4>
                          <p className="text-sm text-gold-700 dark:text-slate-300 line-clamp-2">{resource.description}</p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gold-600 dark:text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gold-600 dark:text-slate-400">
                        {resource.resource_type || '资源'}
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}
            
            {/* PDF查看器 */}
            {selectedPDF && (
              <PDFViewer
                filePath={selectedPDF.filePath}
                chapterTitle={selectedPDF.title}
                onClose={() => setSelectedPDF(null)}
              />
            )}
          </>
        ) : (
          <div className="text-center text-gold-700 dark:text-slate-400">暂无课程</div>
        )}
      </div>
    </div>
  )
}

