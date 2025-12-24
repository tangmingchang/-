import { useEffect, useState } from 'react'
import { Plus, FileText, Image, Play, Edit, Trash2, PenTool, Sparkles, Wand2, Loader2, Save, X } from 'lucide-react'
import { api } from '../utils/api'
import InspirationDice from '../components/InspirationDice'
import AgentCharacter from '../components/AgentCharacter'

interface Project {
  id: number
  name: string
  description: string
  status: string
  course_id: number
  created_at: string
}

interface Script {
  id: number
  title: string
  content: string
  analysis_result: any
}

interface Storyboard {
  id: number
  scene_number: number
  description: string
  image_path: string
  shot_type: string
  camera_angle?: string | null
  camera_movement?: string | null
  notes?: string | null
  order: number
}

export default function CreationSpacePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [scripts, setScripts] = useState<Script[]>([])
  const [storyboards, setStoryboards] = useState<Storyboard[]>([])
  const [activeTab, setActiveTab] = useState<'script' | 'storyboard'>('script')
  const [loading, setLoading] = useState(true)
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [courses, setCourses] = useState<any[]>([])
  const [generatingImageId, setGeneratingImageId] = useState<number | null>(null)
  const [editingScriptId, setEditingScriptId] = useState<number | null>(null)
  const [editingStoryboardId, setEditingStoryboardId] = useState<number | null>(null)
  const [editScriptTitle, setEditScriptTitle] = useState('')
  const [editScriptContent, setEditScriptContent] = useState('')
  const [editStoryboardDesc, setEditStoryboardDesc] = useState('')
  const [editStoryboardShotType, setEditStoryboardShotType] = useState('')

  useEffect(() => {
    // 检查token是否存在，避免未登录时触发401错误
    const token = localStorage.getItem('access_token')
    if (token) {
      loadProjects()
      loadCourses()
    }
  }, [])

  useEffect(() => {
    if (selectedProject) {
      loadScripts(selectedProject.id)
      loadStoryboards(selectedProject.id)
    }
  }, [selectedProject])

  const loadProjects = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    
    try {
      const res = await api.get('/api/projects/')
      setProjects(res.data)
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK' && error.response?.status !== 401) {
        console.error('加载项目失败:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadCourses = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      return
    }
    
    try {
      const res = await api.get('/api/courses/')
      setCourses(res.data)
      if (res.data.length > 0) {
        setSelectedCourseId(res.data[0].id)
      }
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK' && error.response?.status !== 401) {
        console.error('加载课程失败:', error)
      }
    }
  }

  const loadScripts = async (projectId: number) => {
    try {
      const res = await api.get(`/api/projects/${projectId}/scripts`)
      setScripts(res.data)
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载剧本失败:', error)
      }
    }
  }

  const loadStoryboards = async (projectId: number) => {
    try {
      const res = await api.get(`/api/projects/${projectId}/storyboards`)
      setStoryboards(res.data)
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载分镜失败:', error)
      }
    }
  }

  const createProject = async () => {
    if (!newProjectName || !selectedCourseId) {
      alert('请填写项目名称并选择课程')
      return
    }
    try {
      const res = await api.post('/api/projects/', {
        name: newProjectName,
        description: newProjectDesc,
        course_id: selectedCourseId
      })
      setProjects([...projects, res.data])
      setShowCreateProject(false)
      setNewProjectName('')
      setNewProjectDesc('')
      setSelectedProject(res.data)
      setActiveTab('script')
    } catch (error: any) {
      alert('创建项目失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const createScript = async () => {
    if (!selectedProject) return
    const content = prompt('请输入剧本内容:')
    if (!content) return
    try {
      const res = await api.post(`/api/projects/${selectedProject.id}/scripts`, {
        title: '新剧本',
        content
      })
      setScripts([...scripts, res.data])
    } catch (error: any) {
      alert('创建剧本失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const createStoryboard = async () => {
    if (!selectedProject) return
    const description = prompt('请输入场景描述:')
    if (!description) return
    try {
      const res = await api.post(`/api/projects/${selectedProject.id}/storyboards`, {
        description,
        order: storyboards.length
      })
      setStoryboards([...storyboards, res.data])
    } catch (error: any) {
      alert('创建分镜失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const startEditScript = (script: Script) => {
    setEditingScriptId(script.id)
    setEditScriptTitle(script.title || '')
    setEditScriptContent(script.content)
  }

  const cancelEditScript = () => {
    setEditingScriptId(null)
    setEditScriptTitle('')
    setEditScriptContent('')
  }

  const saveScript = async (scriptId: number) => {
    if (!selectedProject) return
    if (!editScriptContent.trim()) {
      alert('剧本内容不能为空')
      return
    }
    try {
      const res = await api.put(`/api/projects/${selectedProject.id}/scripts/${scriptId}`, {
        title: editScriptTitle || '未命名',
        content: editScriptContent
      })
      setScripts(scripts.map(s => s.id === scriptId ? res.data : s))
      cancelEditScript()
    } catch (error: any) {
      alert('保存剧本失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const deleteScript = async (scriptId: number) => {
    if (!selectedProject) return
    if (!confirm('确定要删除这个剧本吗？')) return
    try {
      await api.delete(`/api/projects/${selectedProject.id}/scripts/${scriptId}`)
      // 删除成功后重新加载剧本列表，确保数据同步
      await loadScripts(selectedProject.id)
    } catch (error: any) {
      console.error('删除剧本错误:', error)
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert('删除剧本失败: ' + errorMessage)
    }
  }

  const startEditStoryboard = (storyboard: Storyboard) => {
    setEditingStoryboardId(storyboard.id)
    setEditStoryboardDesc(storyboard.description)
    setEditStoryboardShotType(storyboard.shot_type || '')
  }

  const cancelEditStoryboard = () => {
    setEditingStoryboardId(null)
    setEditStoryboardDesc('')
    setEditStoryboardShotType('')
  }

  const saveStoryboard = async (storyboardId: number) => {
    if (!selectedProject) return
    const storyboard = storyboards.find(s => s.id === storyboardId)
    if (!storyboard) return
    if (!editStoryboardDesc.trim()) {
      alert('场景描述不能为空')
      return
    }
    try {
      const res = await api.put(`/api/projects/${selectedProject.id}/storyboards/${storyboardId}`, {
        scene_number: storyboard.scene_number,
        description: editStoryboardDesc,
        shot_type: editStoryboardShotType || null,
        camera_angle: storyboard.camera_angle || null,
        camera_movement: storyboard.camera_movement || null,
        notes: storyboard.notes || null,
        order: storyboard.order
      })
      setStoryboards(storyboards.map(s => s.id === storyboardId ? res.data : s))
      cancelEditStoryboard()
    } catch (error: any) {
      alert('保存分镜失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const deleteStoryboard = async (storyboardId: number) => {
    if (!selectedProject) return
    if (!confirm('确定要删除这个分镜吗？')) return
    try {
      await api.delete(`/api/projects/${selectedProject.id}/storyboards/${storyboardId}`)
      // 删除成功后重新加载分镜列表，确保数据同步
      await loadStoryboards(selectedProject.id)
    } catch (error: any) {
      console.error('删除分镜错误:', error)
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert('删除分镜失败: ' + errorMessage)
    }
  }

  const generateStoryboardImage = async (storyboard: Storyboard) => {
    if (!selectedProject) return
    
    // 询问是否使用自定义提示词
    const customPrompt = prompt(`请输入图片生成提示词（留空将使用分镜描述）:\n当前描述: ${storyboard.description}`)
    if (customPrompt === null) return // 用户取消
    
    setGeneratingImageId(storyboard.id)
    try {
      const res = await api.post(`/api/projects/${selectedProject.id}/storyboards/${storyboard.id}/generate-image`, {
        prompt: customPrompt || undefined
      })
      
      if (res.data.success) {
        alert('图片生成成功！')
        // 重新加载分镜列表以显示新生成的图片
        await loadStoryboards(selectedProject.id)
      } else {
        alert('图片生成失败: ' + (res.data.message || '未知错误'))
      }
    } catch (error: any) {
      console.error('生成图片错误:', error)
      const errorMessage = error.response?.data?.detail || error.message || '未知错误'
      alert('生成图片失败: ' + errorMessage)
    } finally {
      setGeneratingImageId(null)
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
    <div className="h-full flex flex-col bg-gradient-paper dark:bg-transparent transition-all duration-300 relative z-10">
      {/* 悬浮灵感骰子（保持原有交互） */}
      <InspirationDice />

      {/* 顶部：画板星球头部区域 */}
      <div className="glass border-b border-paper-300 dark:border-dark-border px-6 py-4 md:px-8 md:py-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="page-title bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 bg-clip-text text-transparent">
              画板星球 · 创作空间
            </h1>
            <p className="mt-2 text-lg text-slate-600 dark:text-slate-200">
              在这颗星球上，你可以管理项目、绘制分镜、摇出灵感骰子，让一部作品从想法变成画面。
            </p>
            <p className="mt-1 text-gold-700 dark:text-purple-200 text-sm md:text-base">
              先在左侧选择一个项目，再在右侧的剧本星球与分镜星球之间来回穿梭。
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:block">
              <AgentCharacter type="editor" message="让我陪你一起在画板星球上创作吧。" />
            </div>
            <button
              onClick={() => setShowCreateProject(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all card-hover"
            >
              <Plus className="w-4 h-4" />
              新建项目
            </button>
          </div>
        </div>
      </div>

      {/* 三颗星球横向摆放：项目 / 分镜 / 灵感骰子 */}
      <div className="px-6 pt-4 md:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 项目星球 */}
          <div className="glass-card rounded-2xl p-4 md:p-5 flex items-start gap-3 relative overflow-hidden">
            <div className="absolute -right-6 -top-8 w-24 h-24 rounded-full bg-gradient-to-br from-amber-200/60 via-rose-200/40 to-sky-200/40 blur-xl pointer-events-none" />
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-emerald-400 text-white shadow-md">
              <FileText className="w-5 h-5" />
            </div>
            <div className="relative">
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-1">
                项目星球
              </h2>
              <p className="text-sm text-gold-700 dark:text-purple-200">
                左侧是你的项目星球列表。选中一颗行星，它会亮起星环。
              </p>
              <p className="mt-1 text-xs text-gold-600 dark:text-slate-400">
                当前项目：{selectedProject ? selectedProject.name : '尚未选择'}
              </p>
            </div>
          </div>

          {/* 分镜星球 */}
          <button
            type="button"
            onClick={() => selectedProject && setActiveTab('storyboard')}
            className="glass-card rounded-2xl p-4 md:p-5 flex items-start gap-3 relative overflow-hidden text-left card-hover"
          >
            <div className="absolute -right-8 -bottom-10 w-28 h-28 rounded-full bg-gradient-to-tr from-violet-300/60 via-sky-200/40 to-emerald-200/40 blur-xl pointer-events-none" />
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-violet-400 to-sky-400 text-white shadow-md">
              <Image className="w-5 h-5" />
            </div>
            <div className="relative">
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-1">
                分镜星球
              </h2>
              <p className="text-sm text-gold-700 dark:text-purple-200">
                为每个场景画出关键画面，像在星球表面刻下分镜。
              </p>
              <p className="mt-1 text-xs text-gold-600 dark:text-slate-400">
                点击此卡片会跳转到右侧的「分镜设计」工作台。
              </p>
            </div>
          </button>

          {/* 灵感骰子星球 */}
          <div className="glass-card rounded-2xl p-4 md:p-5 flex items-start gap-3 relative overflow-hidden">
            <div className="absolute -left-10 -bottom-12 w-28 h-28 rounded-full bg-gradient-to-tr from-rose-300/60 via-amber-200/40 to-sky-200/40 blur-xl pointer-events-none" />
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-rose-400 to-amber-400 text-white shadow-md">
              <Play className="w-5 h-5" />
            </div>
            <div className="relative">
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-1">
                灵感骰子星球
              </h2>
              <p className="text-sm text-gold-700 dark:text-purple-200">
                屏幕一角会有一颗小骰子星球，摇一摇，为你的项目丢入新的点子。
              </p>
              <p className="mt-1 text-xs text-gold-600 dark:text-slate-400">
                适合卡壳时使用，为剧本和分镜补充意想不到的元素。
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden mt-4 md:mt-6">
        {/* 左侧：项目列表（项目星球） */}
        <div className="w-72 glass border-r border-paper-300 dark:border-dark-border overflow-y-auto">
          <div className="p-4 md:p-5">
            <h2 className="section-title text-slate-800 dark:text-slate-50 mb-3">
              我的项目星球
            </h2>
            {projects.length === 0 ? (
              <div className="text-center py-10">
                <PenTool className="w-10 h-10 text-slate-400 dark:text-purple-300 mx-auto mb-3 animate-float" />
                <p className="text-sm text-gold-700 dark:text-purple-200 mb-3">
                  还没有任何项目星球，先创建一颗属于你的行星吧。
                </p>
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg transition-all card-hover text-sm"
                >
                  创建项目星球
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {projects.map((project) => {
                  const isActive = selectedProject?.id === project.id
                  return (
                    <div
                      key={project.id}
                      onClick={() => {
                        setSelectedProject(project)
                        setActiveTab('script')
                      }}
                      className={`relative p-3 rounded-2xl cursor-pointer transition-all card-hover ${
                        isActive
                          ? 'bg-gradient-to-r from-sky-400/80 via-violet-400/80 to-rose-400/80 text-white ring-planet shadow-lg scale-[1.02]'
                          : 'glass text-gold dark:text-purple-200 hover:bg-white/20 dark:hover:bg-purple-900/30'
                      }`}
                    >
                      {/* 点状星辰装饰 */}
                      {isActive && (
                        <div className="pointer-events-none absolute inset-0 rounded-2xl border border-white/30 shadow-[0_0_25px_rgba(251,191,36,0.5)]" />
                      )}
                      <h3 className="font-semibold mb-1 line-clamp-1">{project.name}</h3>
                      <p className="text-xs opacity-80 line-clamp-2 mb-1">{project.description}</p>
                      <div className="flex items-center justify-between text-[11px] opacity-80">
                        <span>
                          状态：{project.status === 'draft' ? '草稿' : project.status === 'in_progress' ? '进行中' : '已完成'}
                        </span>
                        <span>
                          {project.created_at
                            ? new Date(project.created_at).toLocaleDateString()
                            : ''}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* 右侧：工作区（剧本 / 分镜 星球） */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedProject ? (
            <>
              {/* 顶部 Tab：剧本星球 / 分镜星球 */}
              <div className="glass border-b border-slate-200/50 dark:border-dark-border px-4 md:px-6">
                <div className="flex flex-wrap gap-2 py-2">
                  <button
                    onClick={() => setActiveTab('script')}
                    className={`px-4 py-2 rounded-lg transition-all card-hover flex items-center gap-2 ${
                      activeTab === 'script'
                        ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                        : 'glass text-gold dark:text-purple-200 hover:bg-white/20 dark:hover:bg-white/10'
                    }`}
                  >
                    <FileText className="w-4 h-4" />
                    剧本星球
                  </button>
                  <button
                    onClick={() => setActiveTab('storyboard')}
                    className={`px-4 py-2 rounded-lg transition-all card-hover flex items-center gap-2 ${
                      activeTab === 'storyboard'
                        ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                        : 'glass text-gold dark:text-purple-200 hover:bg-white/20 dark:hover:bg-white/10'
                    }`}
                  >
                    <Image className="w-4 h-4" />
                    分镜星球
                  </button>
                  <div className="ml-auto flex items-center gap-2 text-xs text-gold-700 dark:text-slate-400">
                    <Sparkles className="w-3 h-3" />
                    <span>当前项目：{selectedProject.name}</span>
                  </div>
                </div>
              </div>

              {/* 内容区 */}
              <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                {activeTab === 'script' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="section-title text-slate-800 dark:text-slate-50">
                        剧本编辑工作台
                      </h2>
                      <button
                        onClick={createScript}
                        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm card-hover"
                      >
                        <Plus className="w-4 h-4" />
                        新建剧本
                      </button>
                    </div>

                    {scripts.length === 0 ? (
                      <div className="text-center py-12 glass-card dark:bg-purple-900/10 rounded-2xl border border-paper-300 dark:border-purple-900/50">
                        <FileText className="w-14 h-14 text-gold-600 dark:text-purple-300 mx-auto mb-4 animate-float" />
                        <p className="text-gold-700 dark:text-purple-200 mb-2">
                          还没有剧本，在这颗星球写下你的第一个故事吧。
                        </p>
                        <p className="text-xs text-gold-600 dark:text-slate-400">
                          点击右上方「新建剧本」，可先用简单文本占位，后续再到文字星球（剧本分析页）做精修。
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {scripts.map((script) => (
                          <div
                            key={script.id}
                            className="glass-card dark:bg-slate-950/60 backdrop-blur-lg rounded-2xl p-5 border border-paper-300 dark:border-purple-900/60 relative overflow-hidden"
                          >
                            <div className="absolute -top-6 -right-10 w-24 h-24 rounded-full bg-gradient-to-br from-amber-200/40 via-rose-200/40 to-sky-200/40 blur-xl pointer-events-none" />
                            {editingScriptId === script.id ? (
                              // 编辑模式
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <h3 className="text-lg font-semibold text-gold dark:text-white">
                                    编辑剧本
                                  </h3>
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => saveScript(script.id)}
                                      className="p-2 text-green-600 dark:text-green-400 hover:text-green-500 dark:hover:text-green-300 rounded-full hover:bg-white/10 transition-colors"
                                      title="保存"
                                    >
                                      <Save className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={cancelEditScript}
                                      className="p-2 text-slate-400 hover:text-slate-300 rounded-full hover:bg-white/10 transition-colors"
                                      title="取消"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                                <div>
                                  <label className="block text-xs text-gold-600 dark:text-slate-400 mb-1">
                                    剧本标题
                                  </label>
                                  <input
                                    type="text"
                                    value={editScriptTitle}
                                    onChange={(e) => setEditScriptTitle(e.target.value)}
                                    className="w-full px-3 py-2 glass border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500 text-sm"
                                    placeholder="请输入剧本标题"
                                  />
                                </div>
                                <div>
                                  <label className="block text-xs text-gold-600 dark:text-slate-400 mb-1">
                                    剧本内容
                                  </label>
                                  <textarea
                                    value={editScriptContent}
                                    onChange={(e) => setEditScriptContent(e.target.value)}
                                    className="w-full px-3 py-2 glass border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500 text-sm font-mono min-h-[200px]"
                                    placeholder="请输入剧本内容"
                                  />
                                </div>
                              </div>
                            ) : (
                              // 查看模式
                              <>
                                <div className="flex items-start justify-between mb-3 relative">
                                  <div>
                                    <h3 className="text-lg font-semibold text-gold dark:text-white mb-1">
                                      {script.title}
                                    </h3>
                                    <p className="text-xs text-gold-600 dark:text-slate-400">
                                      剧本片段 / 草稿内容预览：
                                    </p>
                                  </div>
                                  <div className="flex gap-2">
                                    <button 
                                      onClick={() => startEditScript(script)}
                                      className="p-2 text-gold-600 dark:text-purple-300 hover:text-gold dark:hover:text-white rounded-full hover:bg-white/10 transition-colors"
                                      title="编辑剧本"
                                    >
                                      <Edit className="w-4 h-4" />
                                    </button>
                                    <button 
                                      onClick={() => deleteScript(script.id)}
                                      className="p-2 text-slate-400 hover:text-red-400 rounded-full hover:bg-white/10 transition-colors"
                                      title="删除剧本"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                                <div className="glass dark:bg-slate-900/70 rounded-xl p-3 mb-3 border border-paper-300/60 dark:border-purple-900/50 max-h-48 overflow-auto">
                                  <pre className="text-slate-700 dark:text-slate-200 whitespace-pre-wrap font-mono text-xs leading-relaxed">
                                    {script.content}
                                  </pre>
                                </div>
                              </>
                            )}
                            {script.analysis_result && (
                              <div className="mt-2 rounded-xl bg-purple-900/40 border border-purple-500/40 p-3">
                                <h4 className="text-xs font-semibold text-purple-200 mb-1">
                                  AI 分析摘要（来自文字星球）
                                </h4>
                                <pre className="text-[11px] text-slate-100 whitespace-pre-wrap max-h-32 overflow-auto">
                                  {JSON.stringify(script.analysis_result, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'storyboard' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="section-title text-slate-800 dark:text-slate-50">
                        分镜设计工作台
                      </h2>
                      <button
                        onClick={createStoryboard}
                        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm card-hover"
                      >
                        <Plus className="w-4 h-4" />
                        新建分镜
                      </button>
                    </div>

                    {storyboards.length === 0 ? (
                      <div className="text-center py-12 glass-card dark:bg-purple-900/10 rounded-2xl border border-paper-300 dark:border-purple-900/50">
                        <Image className="w-14 h-14 text-gold-600 dark:text-purple-300 mx-auto mb-4 animate-float" />
                        <p className="text-gold-700 dark:text-purple-200 mb-2">
                          还没有分镜画面，可以先为关键场景写一点描述，再逐步补充画面。
                        </p>
                        <p className="text-xs text-gold-600 dark:text-slate-400">
                          未来可以接入图像/视频生成模型，一键把分镜文字变成画面。
                        </p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {storyboards.map((storyboard) => (
                          <div
                            key={storyboard.id}
                            className="glass-card dark:bg-slate-950/70 backdrop-blur-lg rounded-2xl p-4 border border-paper-300 dark:border-purple-900/60 relative overflow-hidden"
                          >
                            <div className="absolute -left-8 -top-10 w-24 h-24 rounded-full bg-gradient-to-br from-sky-300/40 via-violet-300/40 to-emerald-200/40 blur-xl pointer-events-none" />
                            <div className="relative">
                              {editingStoryboardId === storyboard.id ? (
                                // 编辑模式
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold text-gold-700 dark:text-purple-200">
                                      场景 {storyboard.scene_number || storyboard.order + 1}
                                    </span>
                                    <div className="flex gap-1">
                                      <button
                                        onClick={() => saveStoryboard(storyboard.id)}
                                        className="p-1.5 text-green-600 dark:text-green-400 hover:text-green-500 dark:hover:text-green-300 rounded-full hover:bg-white/10 transition-colors"
                                        title="保存"
                                      >
                                        <Save className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        onClick={cancelEditStoryboard}
                                        className="p-1.5 text-slate-400 hover:text-slate-300 rounded-full hover:bg-white/10 transition-colors"
                                        title="取消"
                                      >
                                        <X className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  </div>
                                  <div>
                                    <label className="block text-xs text-gold-600 dark:text-slate-400 mb-1">
                                      场景描述
                                    </label>
                                    <textarea
                                      value={editStoryboardDesc}
                                      onChange={(e) => setEditStoryboardDesc(e.target.value)}
                                      className="w-full px-3 py-2 glass border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500 text-sm min-h-[80px]"
                                      placeholder="请输入场景描述"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-xs text-gold-600 dark:text-slate-400 mb-1">
                                      景别（可选）
                                    </label>
                                    <input
                                      type="text"
                                      value={editStoryboardShotType}
                                      onChange={(e) => setEditStoryboardShotType(e.target.value)}
                                      className="w-full px-3 py-2 glass border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500 text-sm"
                                      placeholder="如：全景、中景、特写等"
                                    />
                                  </div>
                                  <div className="rounded-xl border border-dashed border-amber-200/70 dark:border-amber-300/50 bg-slate-900/40 h-40 flex items-center justify-center overflow-hidden">
                                    {storyboard.image_path ? (
                                      <img
                                        src={storyboard.image_path}
                                        alt={editStoryboardDesc}
                                        className="max-h-full max-w-full object-contain"
                                      />
                                    ) : (
                                      <Image className="w-10 h-10 text-slate-500" />
                                    )}
                                  </div>
                                </div>
                              ) : (
                                // 查看模式
                                <>
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                      <div className="mb-1 flex items-center justify-between text-xs text-gold-700 dark:text-purple-200">
                                        <span className="font-semibold">
                                          场景 {storyboard.scene_number || storyboard.order + 1}
                                        </span>
                                        {storyboard.shot_type && (
                                          <span className="px-2 py-0.5 rounded-full bg-amber-100/70 dark:bg-amber-400/20 border border-amber-300/60 text-[11px]">
                                            景别：{storyboard.shot_type}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    <div className="flex gap-1 ml-2">
                                      <button 
                                        onClick={() => generateStoryboardImage(storyboard)}
                                        disabled={generatingImageId === storyboard.id}
                                        className="p-1.5 text-purple-600 dark:text-purple-300 hover:text-purple-500 dark:hover:text-purple-200 rounded-full hover:bg-white/10 transition-colors disabled:opacity-50"
                                        title="AI生成图片"
                                      >
                                        {generatingImageId === storyboard.id ? (
                                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        ) : (
                                          <Wand2 className="w-3.5 h-3.5" />
                                        )}
                                      </button>
                                      <button 
                                        onClick={() => startEditStoryboard(storyboard)}
                                        className="p-1.5 text-gold-600 dark:text-purple-300 hover:text-gold dark:hover:text-white rounded-full hover:bg-white/10 transition-colors"
                                        title="编辑分镜"
                                      >
                                        <Edit className="w-3.5 h-3.5" />
                                      </button>
                                      <button 
                                        onClick={() => deleteStoryboard(storyboard.id)}
                                        className="p-1.5 text-slate-400 hover:text-red-400 rounded-full hover:bg-white/10 transition-colors"
                                        title="删除分镜"
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  </div>
                                  <div className="rounded-xl border border-dashed border-amber-200/70 dark:border-amber-300/50 bg-slate-900/40 h-40 mb-3 flex items-center justify-center overflow-hidden">
                                    {storyboard.image_path ? (
                                      <img
                                        src={storyboard.image_path}
                                        alt={storyboard.description}
                                        className="max-h-full max-w-full object-contain"
                                      />
                                    ) : (
                                      <Image className="w-10 h-10 text-slate-500" />
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-700 dark:text-slate-200 line-clamp-3">
                                    {storyboard.description}
                                  </p>
                                </>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md mx-auto">
                <PenTool className="w-16 h-16 text-gold-600 dark:text-purple-300 mx-auto mb-4 animate-float" />
                <p className="text-gold-700 dark:text-purple-200 mb-3 text-lg">
                  请选择一颗项目星球，或先创建一个新的。
                </p>
                <p className="text-sm text-gold-600 dark:text-slate-400 mb-4">
                  左侧会展示你现有的项目星球。每一个项目，都是小王子在不同星球上的一次创作旅程。
                </p>
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="px-6 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg transition-colors card-hover"
                >
                  创建新项目星球
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建项目弹窗 */}
      {showCreateProject && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="glass dark:bg-purple-900/20 rounded-2xl p-6 md:p-7 w-full max-w-md border border-paper-300 dark:border-purple-900/60 shadow-xl">
            <h2 className="section-title text-slate-800 dark:text-slate-50 mb-4">
              创建新的项目星球
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">
                  项目名称
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-4 py-2 glass border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  placeholder="给这颗星球起一个名字"
                />
              </div>
              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">
                  项目描述
                </label>
                <textarea
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full px-4 py-2 glass border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  rows={3}
                  placeholder="简单写一下你想在这个项目里完成什么故事、什么练习"
                />
              </div>
              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">
                  所属课程
                </label>
                <select
                  value={selectedCourseId || ''}
                  onChange={(e) => setSelectedCourseId(Number(e.target.value))}
                  className="w-full px-4 py-2 glass border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                >
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={createProject}
                  className="flex-1 px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg transition-colors card-hover"
                >
                  创建星球
                </button>
                <button
                  onClick={() => setShowCreateProject(false)}
                  className="flex-1 px-4 py-2 glass text-gold dark:text-purple-200 rounded-lg hover:bg-white/30 dark:hover:bg-white/10 transition-colors"
                >
                  先不创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
