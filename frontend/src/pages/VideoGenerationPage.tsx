import { useState, useEffect, useRef } from 'react'
import { Sparkles, Image, Video, Loader2, Film } from 'lucide-react'
import { api } from '../utils/api'
import AgentCharacter from '../components/AgentCharacter'

interface VideoResult {
  id: string
  url: string
  prompt: string
  type: 'text' | 'image'
}

export default function VideoGenerationPage() {
  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text')
  const [textPrompt, setTextPrompt] = useState('')
  const [duration, setDuration] = useState(5)
  const [motionType, setMotionType] = useState('auto')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [videoResults, setVideoResults] = useState<VideoResult[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string>('')
  const [startTime, setStartTime] = useState<number | null>(null)
  const [progress, setProgress] = useState<number>(0)
  // 使用useRef存储开始时间，避免闭包问题
  const startTimeRef = useRef<number | null>(null)

  // 使用useEffect来更新进度
  useEffect(() => {
    if (!isGenerating || !startTimeRef.current) {
      // 如果不在生成中，重置进度
      if (!isGenerating) {
        setProgress(0)
      }
      return
    }
    
    // 立即更新一次进度（避免等待1秒）
    const updateProgress = () => {
      if (!startTimeRef.current || !isGenerating) {
        return 0
      }
      const elapsed = (Date.now() - startTimeRef.current) / 1000 // 已过秒数
      return Math.min(Math.floor(elapsed / 10) * 10, 90) // 每10秒增加10%，最多90%
    }
    
    // 立即设置初始进度
    setProgress(updateProgress())
    
    // 使用setInterval持续更新进度
    const interval = setInterval(() => {
      // 检查是否仍在生成中且有开始时间
      if (!startTimeRef.current || !isGenerating) {
        clearInterval(interval)
        return
      }
      
      const newProgress = updateProgress()
      setProgress(newProgress)
      
      // 如果进度达到90%，停止更新（等待任务完成时设置为100%）
      if (newProgress >= 90) {
        clearInterval(interval)
      }
    }, 1000) // 每秒更新一次
    
    // 清理函数：组件卸载或依赖变化时清除定时器
    return () => clearInterval(interval)
  }, [isGenerating, startTime]) // 添加startTime作为依赖，当startTime被设置时会重新运行

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImageFile(file)
    const reader = new FileReader()
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const generateFromText = async () => {
    if (!textPrompt.trim()) {
      alert('请输入视频描述')
      return
    }

    setIsGenerating(true)
    try {
      // 使用FormData格式，与后端API期望的Form格式一致
      const formData = new FormData()
      formData.append('engine', 'aliyun')
      formData.append('mode', 't2v')
      formData.append('prompt', textPrompt)
      formData.append('duration', String(duration))
      formData.append('resolution', '720P')
      formData.append('audio', 'true')
      formData.append('prompt_extend', 'true')

      const res = await api.post('/api/video/generate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (res.data?.job_id) {
        const jobId = res.data.job_id
        setCurrentJobId(jobId)
        setJobStatus(res.data.status || 'PENDING')
        const now = Date.now()
        setStartTime(now)
        startTimeRef.current = now // 同时更新ref
        setProgress(0)
        // 开始轮询任务状态（进度更新由useEffect自动处理）
        pollJobStatus(jobId, 'text')
      } else if (res.data?.video_url || res.data?.local_path) {
        const videoUrl = res.data.video_url || res.data.local_path
        const id = `${Date.now()}-${Math.random()}`
        setVideoResults((prev) => [
          { id, url: videoUrl, prompt: textPrompt, type: 'text' },
          ...prev
        ])
        setIsGenerating(false)
      } else {
        alert('生成失败：未返回视频地址或任务ID')
        setIsGenerating(false)
      }
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail
      const errorMsg =
        typeof errorDetail === 'object'
          ? errorDetail.message || errorDetail.error
          : errorDetail || error.message
      alert('生成失败: ' + errorMsg)
      setIsGenerating(false)
    }
  }


  const pollJobStatus = async (jobId: string, videoType: 'text' | 'image' = 'text') => {
    const maxAttempts = 120 // 最多轮询2分钟（每10秒一次）
    let attempts = 0
    
    const poll = async () => {
      if (attempts >= maxAttempts) {
        setIsGenerating(false)
        setCurrentJobId(null)
        setStartTime(null)
        alert('任务超时，请稍后手动查询状态')
        return
      }
      
      try {
        const res = await api.get(`/api/video/job/${jobId}`)
        const status = res.data.status
        
        setJobStatus(status)
        
        if (status === 'SUCCEEDED') {
          // 任务完成，先确保进度至少显示一些过渡效果
          const currentProgress = progress
          if (currentProgress < 10) {
            // 如果进度还很小，先设置到10%，然后延迟一下再设置到100%
            setProgress(10)
            setTimeout(() => {
              setProgress(100)
            }, 300) // 300ms后设置到100%
          } else {
            // 如果已经有进度，直接设置到100%
            setProgress(100)
          }
          startTimeRef.current = null // 清除ref
          
          // 任务完成，获取视频URL
          const videoUrl = res.data.video_url || res.data.local_path
          if (videoUrl) {
            // 构建完整URL
            const fullUrl = videoUrl.startsWith('http') 
              ? videoUrl 
              : `${import.meta.env.VITE_API_URL || ''}${videoUrl}`
            
            const id = `${Date.now()}-${Math.random()}`
            setVideoResults((prev) => [
              { id, url: fullUrl, prompt: textPrompt || (videoType === 'image' ? '图生视频' : '文生视频'), type: videoType },
              ...prev
            ])
          }
          setIsGenerating(false)
          setCurrentJobId(null)
          setStartTime(null)
          startTimeRef.current = null // 清除ref
        } else if (status === 'FAILED') {
          alert(`视频生成失败: ${res.data.error || '未知错误'}`)
          setIsGenerating(false)
          setCurrentJobId(null)
          setStartTime(null)
          startTimeRef.current = null // 清除ref
          setProgress(0)
        } else {
          // 继续轮询
          attempts++
          setTimeout(poll, 10000) // 每10秒轮询一次
        }
      } catch (error: any) {
        console.error('查询任务状态失败:', error)
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000)
        } else {
          setIsGenerating(false)
          setCurrentJobId(null)
          setStartTime(null)
        }
      }
    }
    
    poll()
  }

  const generateFromImage = async () => {
    if (!imageFile) {
      alert('请先选择图片')
      return
    }

    setIsGenerating(true)
    try {
      const formData = new FormData()
      formData.append('image_file', imageFile)
      formData.append('engine', 'aliyun')
      formData.append('mode', 'i2v')
      formData.append('prompt', textPrompt || '让图片动起来')
      formData.append('duration', String(duration))
      formData.append('resolution', '720P')
      formData.append('audio', 'true')
      formData.append('prompt_extend', 'true')

      const res = await api.post('/api/video/generate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (res.data?.job_id) {
        const jobId = res.data.job_id
        setCurrentJobId(jobId)
        setJobStatus(res.data.status || 'PENDING')
        const now = Date.now()
        setStartTime(now)
        startTimeRef.current = now // 同时更新ref
        setProgress(0)
        // 开始轮询任务状态（进度更新由useEffect自动处理）
        pollJobStatus(jobId, 'image')
      } else if (res.data?.video_url || res.data?.local_path) {
        const videoUrl = res.data.video_url || res.data.local_path
        const id = `${Date.now()}-${Math.random()}`
        setVideoResults((prev) => [
          { id, url: videoUrl, prompt: textPrompt || '图生视频', type: 'image' },
          ...prev
        ])
        setIsGenerating(false)
      } else {
        alert('生成失败：未返回视频地址或任务ID')
        setIsGenerating(false)
      }
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail
      const errorMsg =
        typeof errorDetail === 'object'
          ? errorDetail.message || errorDetail.error
          : errorDetail || error.message
      alert('生成失败: ' + errorMsg)
      setIsGenerating(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-paper dark:bg-transparent p-8 transition-all duration-300 relative z-10">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* 顶部：电影放映星球标题 + 角色 */}
        <header className="animate-slide-up">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="page-title bg-gradient-to-r from-amber-400 via-sky-400 to-indigo-500 bg-clip-text text-transparent">
                电影放映星球 · AI 视频生成
              </h1>
              <p className="mt-2 text-lg text-gold-700 dark:text-purple-200">
                在这颗星球上，小王子把你的文字和图片变成真正会动的画面。
              </p>
              <p className="mt-1 text-sm text-gold-600 dark:text-slate-300">
                步骤：选择生成方式 → 设置时长与运动 → 一键生成，右侧放映机星球会记录所有任务。
              </p>
            </div>
            <div className="shrink-0 flex items-center gap-3">
              <div className="hidden md:block">
            <AgentCharacter type="editor" />
              </div>
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-amber-300 to-rose-300 flex items-center justify-center shadow-[0_0_25px_rgba(251,191,36,0.6)]">
                <Film className="w-6 h-6 text-slate-900" />
              </div>
            </div>
          </div>
        </header>

        {/* 步骤指示条 */}
        <section className="glass-card p-4 md:p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-emerald-400/90 text-white flex items-center justify-center text-sm font-bold shadow-md">
              1
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
                选择生成方式
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-300">
                文生视频 / 图生视频两种模式，适合不同创作阶段。
              </p>
            </div>
          </div>
          <div className="hidden md:block h-px flex-1 bg-gradient-to-r from-emerald-300/60 via-sky-300/60 to-violet-300/60 mx-4" />
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-sky-400/90 text-white flex items-center justify-center text-sm font-bold shadow-md">
              2
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
                设置时长与运动
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-300">
                控制节奏和镜头运动，让生成结果更接近你的预期。
              </p>
            </div>
          </div>
          <div className="hidden md:block h-px flex-1 bg-gradient-to-r from-violet-300/60 via-rose-300/60 to-amber-300/60 mx-4" />
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-rose-400/90 text-white flex items-center justify-center text-sm font-bold shadow-md">
              3
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
                生成与查看
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-300">
                结果会在右侧放映机星球中排成一条时间星轨。
              </p>
            </div>
        </div>
        </section>

        {/* 主体：左控制台 + 右放映机星球 */}
        <section className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] gap-6">
          {/* 左：生成控制台 */}
          <div className="glass-card p-6 flex flex-col gap-5">
            {/* 模式切换 Tab */}
            <div className="flex gap-2 mb-2">
            <button
              onClick={() => setActiveTab('text')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all card-hover ${
                activeTab === 'text'
                  ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                  : 'glass text-gold dark:text-slate-300'
              }`}
            >
                <Sparkles
                  className={`w-4 h-4 ${
                    activeTab === 'text'
                      ? 'text-white'
                      : 'text-gold dark:text-slate-300'
                  }`}
                />
              文生视频
            </button>
            <button
              onClick={() => setActiveTab('image')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all card-hover ${
                activeTab === 'image'
                  ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                  : 'glass text-gold dark:text-slate-300'
              }`}
            >
                <Image
                  className={`w-4 h-4 ${
                    activeTab === 'image'
                      ? 'text-white'
                      : 'text-gold dark:text-slate-300'
                  }`}
                />
              图生视频
            </button>
          </div>

            {/* 公共参数：时长 +（图生时）运动类型 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
            <div>
              <label className="block text-gold dark:text-purple-200 mb-2 flex justify-between items-center">
                <span>时长（秒）</span>
                  <span className="text-sm text-primary-600 dark:text-neon-blue">
                    {duration}s
                  </span>
              </label>
              <input
                type="range"
                min={3}
                max={20}
                value={duration}
                  onChange={(e) =>
                    setDuration(
                      Math.max(
                        3,
                        Math.min(20, Number(e.target.value) || 5)
                      )
                    )
                  }
                className="w-full accent-primary-600 dark:accent-neon-blue"
              />
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  建议 3–10 秒适合作为练习或预告片段。
                </p>
            </div>

            {activeTab === 'image' && (
              <div>
                  <label className="block text-gold dark:text-purple-200 mb-2">
                    运动类型
                  </label>
                <select
                  value={motionType}
                  onChange={(e) => setMotionType(e.target.value)}
                  className="w-full px-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                >
                  <option value="auto">自动</option>
                  <option value="pan_left">向左摇移</option>
                  <option value="pan_right">向右摇移</option>
                  <option value="zoom_in">推进</option>
                  <option value="zoom_out">拉远</option>
                </select>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    模拟基础机位运动，给静态图片加一点镜头感。
                  </p>
              </div>
            )}
          </div>

            {/* 文生视频表单 */}
          {activeTab === 'text' && (
            <div className="space-y-4">
              <div>
                  <label className="block text-gold dark:text-purple-200 mb-2">
                    视频描述
                  </label>
                <textarea
                  value={textPrompt}
                  onChange={(e) => setTextPrompt(e.target.value)}
                    className="w-full px-4 py-3 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  rows={4}
                    placeholder="例如：黄昏时分，小王子站在自己的星球上，远处的夕阳缓慢落下，镜头缓慢拉远..."
                />
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    小提示：可以加入时间、地点、镜头运动和情绪氛围，会更有电影感。
                  </p>
              </div>
              <button
                onClick={generateFromText}
                disabled={isGenerating || !textPrompt.trim()}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Video className="w-5 h-5" />
                    生成视频
                  </>
                )}
              </button>
            </div>
          )}

            {/* 图生视频表单 */}
          {activeTab === 'image' && (
            <div className="space-y-4">
              <div>
                  <label className="block text-gold dark:text-purple-200 mb-2">
                    选择图片
                  </label>
                <div className="relative">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="hidden"
                    id="image-upload"
                  />
                  <label
                    htmlFor="image-upload"
                    className="flex items-center justify-center gap-2 px-4 py-3 glass rounded-lg cursor-pointer card-hover"
                  >
                    <Image className="w-5 h-5 text-primary-600 dark:text-neon-blue" />
                      <span className="text-gold dark:text-purple-200">
                        从电脑中选择一张图片
                      </span>
                  </label>
                </div>
                {imagePreview && (
                  <div className="mt-4">
                    <img
                      src={imagePreview}
                      alt="预览"
                        className="max-w-full max-h-64 rounded-xl shadow-lg border border-white/60 dark:border-slate-800/80"
                    />
                  </div>
                )}
              </div>
              <div>
                  <label className="block text-gold dark:text-purple-200 mb-2">
                    视频描述（可选）
                  </label>
                <textarea
                  value={textPrompt}
                  onChange={(e) => setTextPrompt(e.target.value)}
                    className="w-full px-4 py-3 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  rows={3}
                    placeholder="例如：镜头缓慢推进到小王子的背影，星星在天空中微微闪烁……"
                />
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    不写也可以，系统会根据图片内容自动补全。
                  </p>
              </div>
              <button
                onClick={generateFromImage}
                disabled={isGenerating || !imageFile}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Video className="w-5 h-5" />
                    生成视频
                  </>
                )}
              </button>
            </div>
          )}
        </div>

          {/* 右：放映机星球（进度环 + 时间星轨） */}
          <div className="glass-card p-6 flex flex-col gap-5">
            {/* 放映机星球 */}
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="section-title text-slate-800 dark:text-slate-50">
                  放映机星球
          </h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  所有生成任务都会在这里排队，像一条绕着星球旋转的光带。
                </p>
              </div>
              <div className="h-10 w-10 rounded-full bg-slate-900/80 border border-amber-300/60 flex items-center justify-center shadow-[0_0_20px_rgba(251,191,36,0.7)]">
                <Film className="w-5 h-5 text-amber-300" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] gap-4 items-center">
              {/* 环绕进度环 */}
              <div className="flex flex-col items-center justify-center">
                <div className="relative w-40 h-40">
                  <div className="absolute inset-0 rounded-full border-4 border-slate-600/50" />
                  <div
                    className="absolute inset-0 rounded-full border-4 border-amber-300 border-t-transparent border-l-transparent animate-spin-slow"
                    style={{ animationDuration: '6s' }}
                  />
                  <div className="absolute inset-[22%] rounded-full bg-slate-900/90 flex flex-col items-center justify-center">
                    <span className="text-xs text-slate-400">
                      当前渲染
                    </span>
                    <span className="text-2xl font-semibold text-amber-300">
                      {isGenerating ? progress : videoResults.length > 0 ? '100' : '0'}%
                    </span>
                  </div>
                </div>
                <p className="mt-3 text-xs text-slate-400 text-center">
                  当有任务生成时，星环会缓缓旋转，代表渲染正在进行。
                </p>
              </div>

              {/* 当前任务简介 */}
              <div className="space-y-3">
                <h3 className="text-base md:text-lg font-semibold text-slate-800 dark:text-slate-50">
                  当前任务
                </h3>
          {videoResults.length === 0 ? (
                  <p className="text-sm text-slate-500 dark:text-slate-300">
                    还没有生成任务。可以先在左侧选择一种方式生成一个短视频片段。
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-slate-500 dark:text-slate-300">
                      {videoResults[0]?.prompt ||
                        (videoResults[0]?.type === 'image'
                          ? '图生视频任务'
                          : '文生视频任务')}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      状态：{isGenerating ? '渲染中' : '已完成 / 等待新任务'}
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* 分割线 */}
            <div className="h-px bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200 dark:from-slate-700 dark:via-slate-800 dark:to-slate-700 my-2" />

            {/* 视频播放区 */}
            {videoResults.length > 0 && (
              <div className="space-y-3 mt-6">
                <h3 className="text-base md:text-lg font-semibold text-slate-800 dark:text-slate-50">
                  视频播放区
                </h3>
                <div className="space-y-4">
                  {videoResults.map((result) => (
                    <div
                      key={result.id}
                      className="glass-card dark:bg-slate-950/60 backdrop-blur-lg rounded-2xl p-4 border border-paper-300 dark:border-purple-900/60"
                    >
                      <div className="mb-2">
                        <p className="text-sm text-gold dark:text-purple-100 font-medium">
                          {result.prompt || (result.type === 'image' ? '图生视频' : '文生视频')}
                        </p>
                        <p className="text-xs text-gold-600 dark:text-slate-400 mt-1">
                          {result.type === 'image' ? '图生视频' : '文生视频'}
                        </p>
                      </div>
                      <div className="rounded-lg overflow-hidden bg-slate-900">
                        <video
                          src={result.url}
                          controls
                          className="w-full max-h-96"
                          preload="metadata"
                        >
                          您的浏览器不支持视频播放
                        </video>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 时间星轨 */}
            <div className="space-y-3">
              <h3 className="text-base md:text-lg font-semibold text-slate-800 dark:text-slate-50">
                任务时间星轨
              </h3>
              {videoResults.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <Film className="w-10 h-10 text-slate-400 dark:text-slate-500 mb-3" />
                  <p className="text-sm text-slate-500 dark:text-slate-300 mb-1">
                    还没有生成记录
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    每一次生成任务都会在这里留下一个小小的星点。
                  </p>
                </div>
              ) : (
                <div className="relative overflow-x-auto py-4">
                  {/* 星轨线 */}
                  <div className="absolute left-0 right-0 top-1/2 h-[2px] bg-slate-600/40" />
                  <div className="relative flex gap-10">
                    {videoResults.map((item, idx) => (
                      <div
                        key={item.id}
                        className="relative flex flex-col items-center min-w-[140px]"
                      >
                        {/* 星点 */}
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(250,204,21,0.6)] ${
                            item.url
                              ? 'bg-emerald-400'
                              : isGenerating && idx === 0
                              ? 'bg-amber-300'
                              : 'bg-slate-500'
                          }`}
                        >
                          <span className="text-[10px] text-slate-900 font-bold">
                            {idx + 1}
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-slate-400 text-center">
                          {item.prompt ||
                            (item.type === 'image' ? '图生视频' : '文生视频')}
                        </div>
                        <div className="mt-1 text-[11px] text-slate-500">
                          {item.url
                            ? '已完成'
                            : isGenerating && idx === 0
                            ? '渲染中'
                            : '排队中'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
        </div>
        </section>
      </div>
    </div>
  )
}
