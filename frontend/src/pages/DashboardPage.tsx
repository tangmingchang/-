import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, PenTool, FileText, Video, TrendingUp } from 'lucide-react'
import { api } from '../utils/api'
import AgentCharacter from '../components/AgentCharacter'
import WordCloud from '../components/WordCloud'

interface Course {
  id: number
  name: string
  description: string
  created_at: string
}

interface Project {
  id: number
  name: string
  status: string
  course_id: number
}

export default function DashboardPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    
    try {
      const [coursesRes, projectsRes] = await Promise.all([
        api.get('/api/courses/'),
        api.get('/api/projects/')
      ])
      setCourses(coursesRes.data)
      setProjects(projectsRes.data)
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载数据失败:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  const isLoggedIn = !!localStorage.getItem('access_token')

  if (loading && isLoggedIn) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gold dark:text-white text-lg animate-pulse">加载中...</div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-paper dark:bg-transparent p-8 transition-all duration-300 relative z-10">
      <div className="max-w-7xl mx-auto">

        {/* 顶部：主星球视图 */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center mb-10">
          {/* 左：欢迎文案 + 当前星球 */}
          <div className="space-y-4">
            <h1 className="page-title bg-gradient-to-r from-sky-400 via-emerald-400 to-amber-300 bg-clip-text text-transparent">
              {isLoggedIn ? '欢迎回到主星球' : '欢迎来到主星球'}
            </h1>
            <p className="text-3xl md:text-4xl text-slate-600 dark:text-slate-200 font-heading">
              你现在停留在
              <span className="font-semibold text-amber-500 dark:text-amber-300">
                {" "}主星球
              </span>
              ，这里可以一眼望见学习星球、画板星球和电影星球。
            </p>
          </div>

          {/* 右：小王子玻璃卡片 */}
          <div className="bg-transparent backdrop-blur-sm border border-white/20 dark:border-slate-700/30 rounded-3xl planet-glow flex flex-col items-center justify-center p-6">
            <img
              src="/小王子.png"
              alt="小王子"
              className="h-40 md:h-52 floating drop-shadow-[0_0_25px_rgba(250,250,250,0.7)]"
            />
            <p className="mt-4 text-2xl md:text-3xl text-slate-700/90 dark:text-slate-100/90 text-center font-heading">
                  真正重要的东西，用眼睛是看不见的。
            </p>
          </div>
        </section>

        {/* 中间：星球功能卡片 */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <Link
            to="/learning"
            className="group glass-card p-6 card-hover animate-slide-up relative overflow-hidden"
            style={{ animationDelay: '0.1s' }}
          >
            <div className="absolute top-2 right-2 w-1 h-1 bg-yellow-400 rounded-full animate-twinkle"></div>
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <img src="/1.png" alt="学习空间" className="w-6 h-6 object-contain" />
            </div>
            <h3 className="card-title text-slate-800 dark:text-slate-50 mb-1">学习空间</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm">浏览课程和教学资源</p>
          </Link>

          <Link
            to="/creation"
            className="group glass-card p-6 card-hover animate-slide-up relative overflow-hidden"
            style={{ animationDelay: '0.2s' }}
          >
            <div className="absolute top-2 right-2 w-1 h-1 bg-purple-400 rounded-full animate-twinkle"></div>
            <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <img src="/2.png" alt="创作空间" className="w-6 h-6 object-contain" />
            </div>
            <h3 className="card-title text-slate-800 dark:text-slate-50 mb-1">创作空间</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm">开始新的创作项目</p>
          </Link>

          <Link
            to="/script-analysis"
            className="group glass-card p-6 card-hover animate-slide-up relative overflow-hidden"
            style={{ animationDelay: '0.3s' }}
          >
            <div className="absolute top-2 right-2 w-1 h-1 bg-green-400 rounded-full animate-twinkle"></div>
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <img src="/3.png" alt="剧本分析" className="w-6 h-6 object-contain" />
            </div>
            <h3 className="card-title text-slate-800 dark:text-slate-50 mb-1">剧本分析</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm">AI智能分析剧本</p>
          </Link>

          <Link
            to="/video-generation"
            className="group glass-card p-6 card-hover animate-slide-up relative overflow-hidden"
            style={{ animationDelay: '0.4s' }}
          >
            <div className="absolute top-2 right-2 w-1 h-1 bg-pink-400 rounded-full animate-twinkle"></div>
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <img src="/4.png" alt="视频生成" className="w-6 h-6 object-contain" />
            </div>
            <h3 className="card-title text-slate-800 dark:text-slate-50 mb-1">视频生成</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm">AI生成视频素材</p>
          </Link>
        </section>

        {/* 下半部分：词云 + 玫瑰小王子 */}
        <section className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-stretch mb-10">
          {/* 左：3/5 词云区域 */}
          <div className="lg:col-span-3 glass-card p-4 md:p-6">
            <h2 className="section-title mb-4 text-slate-800 dark:text-slate-50">
              词云星球 · 今日灵感
            </h2>
              <WordCloud
                words={[
                  { text: '影视制作', value: 100 },
                  { text: '剧本创作', value: 95 },
                  { text: '镜头语言', value: 90 },
                  { text: '剪辑技巧', value: 85 },
                  { text: '色彩调色', value: 80 },
                  { text: '音效设计', value: 75 },
                  { text: '导演思维', value: 70 },
                  { text: '摄影构图', value: 68 },
                  { text: '场景设计', value: 65 },
                  { text: '角色塑造', value: 63 },
                  { text: '叙事结构', value: 60 },
                  { text: '视觉特效', value: 58 },
                  { text: '后期制作', value: 55 },
                  { text: '分镜脚本', value: 53 },
                  { text: '灯光设计', value: 50 },
                  { text: '配乐创作', value: 48 },
                  { text: '演员指导', value: 45 },
                  { text: '制片管理', value: 43 },
                  { text: '创意策划', value: 40 },
                  { text: '故事板', value: 38 },
                  { text: '蒙太奇', value: 35 },
                  { text: '节奏控制', value: 33 },
                  { text: '情绪表达', value: 30 },
                  { text: '视觉风格', value: 28 },
                  { text: '镜头运动', value: 26 },
                  { text: '画面构图', value: 25 },
                  { text: '色彩搭配', value: 23 },
                  { text: '光影效果', value: 22 },
                  { text: '音画同步', value: 20 },
                  { text: '转场技巧', value: 19 },
                  { text: '镜头切换', value: 18 },
                  { text: '画面节奏', value: 17 },
                  { text: '视觉冲击', value: 16 },
                  { text: '情感渲染', value: 15 },
                  { text: '氛围营造', value: 14 },
                  { text: '细节把控', value: 13 },
                  { text: '创意构思', value: 12 },
                  { text: '艺术表现', value: 11 },
                  { text: '技术实现', value: 10 },
                  { text: '团队协作', value: 9 },
                  { text: '项目管理', value: 8 },
                  { text: '预算控制', value: 7 },
                  { text: '时间管理', value: 6 },
                  { text: '资源整合', value: 5 },
                  { text: '市场分析', value: 4 },
                  { text: '观众定位', value: 3 },
                  { text: '传播策略', value: 2 },
                  { text: '品牌塑造', value: 1 },
                ]}
                width={typeof window !== 'undefined' ? Math.min((window.innerWidth - 64) * 0.6, 600) : 600}
                height={500}
                colors={[
                  '#3b82f6', // blue
                  '#8b5cf6', // purple
                  '#ec4899', // pink
                  '#f59e0b', // amber
                  '#10b981', // emerald
                  '#ef4444', // red
                  '#06b6d4', // cyan
                  '#f97316', // orange
                ]}
              />
          </div>
          {/* 右：2/5 玫瑰小王子装饰 */}
          <div className="lg:col-span-2 bg-transparent backdrop-blur-sm border border-white/20 dark:border-slate-700/30 rounded-3xl flex flex-col items-center justify-center overflow-hidden p-6">
            <img
              src="/玫瑰小王子.png"
              alt="玫瑰小王子"
              className="h-72 md:h-80 floating"
            />
            <p className="mt-3 text-2xl md:text-3xl text-rose-500 dark:text-rose-300 text-center font-heading">
              这里是你的「知识玫瑰园」，每一朵都是你浇灌出来的。
            </p>
          </div>
        </section>

        {/* 下半部分：项目列表 + 月亮小王子 */}
        <section className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-stretch">
          {/* 左：2/5 月亮小王子 */}
          <div className="lg:col-span-2 bg-transparent backdrop-blur-sm border border-white/20 dark:border-slate-700/30 rounded-3xl flex flex-col items-center justify-center p-6">
            <img
              src="/月亮小王子.png"
              alt="月亮小王子"
              className="h-64 md:h-72 floating"
            />
            <p className="mt-3 text-2xl md:text-3xl text-sky-400 dark:text-sky-300 text-center font-heading">
              在月亮星球上，独自完成一部作品，也是很浪漫的事情。
            </p>
          </div>
          {/* 右：3/5 项目列表 */}
          <div className="lg:col-span-3 glass-card p-4 md:p-6">
            <h2 className="section-title mb-4 text-slate-800 dark:text-slate-50">
              项目星轨
            </h2>
            <div>
              {!isLoggedIn ? (
                <div className="text-center py-12">
                  <PenTool className="w-16 h-16 text-slate-400 dark:text-purple-300 mx-auto mb-4 animate-float" />
                  <p className="text-gold-700 dark:text-purple-200 mb-4">请先登录以查看项目</p>
                  <Link
                    to="/login"
                    className="inline-block px-6 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all card-hover"
                  >
                    立即登录
                  </Link>
                </div>
              ) : projects.length === 0 ? (
                <div className="text-center py-12">
                  <AgentCharacter type="editor" message="还没有创建任何项目，让我们开始创作吧！" isAnimating />
                </div>
              ) : (
                <div className="space-y-3">
                  {projects.map((project, index) => (
                    <div
                      key={project.id}
                      className="glass p-4 rounded-lg card-hover animate-slide-up flex items-center justify-between"
                      style={{ animationDelay: `${0.8 + index * 0.1}s` }}
                    >
                      <div>
                        <h3 className="text-gold dark:text-white font-semibold mb-1">{project.name}</h3>
                        <span className="text-xs text-gold-700 dark:text-purple-200">
                          状态: {project.status === 'draft' ? '草稿' : project.status === 'in_progress' ? '进行中' : '已完成'}
                        </span>
                      </div>
                      <TrendingUp className="w-5 h-5 text-primary-500 dark:text-neon-blue" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
