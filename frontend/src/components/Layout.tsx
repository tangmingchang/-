import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { User, ChevronDown, ChevronRight } from 'lucide-react'
import { api } from '../utils/api'
import ThemeToggle from './ThemeToggle'
import Breadcrumb from './Breadcrumb'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    learning: true,
    creation: true,
    collaboration: true,
    management: false,
  })

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
      loadUserInfo()
    }
  }, [location.pathname]) // 当路由变化时重新加载用户信息（用于头像更新后刷新）

  const loadUserInfo = async () => {
    try {
      const res = await api.get('/api/auth/me')
      setUserInfo(res.data)
      setIsLoggedIn(true)
    } catch (error: any) {
      console.error('加载用户信息失败:', error)
      // 如果是401错误，响应拦截器会处理跳转，这里只更新状态
      if (error.response?.status === 401) {
        setIsLoggedIn(false)
        localStorage.removeItem('access_token')
        // 不在这里跳转，让响应拦截器处理
      } else {
        // 其他错误（如网络错误），不清除登录状态，允许离线使用
        console.warn('用户信息加载失败，但保持登录状态:', error.message)
      }
    }
  }

  // 根据用户角色过滤导航菜单
  const getNavGroups = () => {
    const userRole = userInfo?.role || 'student'
    const isAdmin = userRole === 'admin'
    
    const baseGroups = [
      {
        id: 'home',
        items: [{ path: '/', icon: '/星球.png', label: '首页', iconType: 'image' }],
      },
      {
        id: 'learning',
        title: '学习相关',
        items: [
          { path: '/learning', icon: '/1.png', label: '学习空间', iconType: 'image' },
          { path: '/knowledge', icon: '/5.png', label: '知识库', iconType: 'image' },
        ],
      },
      {
        id: 'creation',
        title: '创作相关',
        items: [
          { path: '/creation', icon: '/2.png', label: '创作空间', iconType: 'image' },
          { path: '/script-analysis', icon: '/3.png', label: '剧本分析', iconType: 'image' },
          { path: '/video-generation', icon: '/4.png', label: '视频生成', iconType: 'image' },
          // 学生显示评估页，教师显示管理页面
          ...(userRole === 'teacher' || userRole === 'admin'
            ? [{ path: '/teacher-management', icon: '/6.png', label: '班级管理', iconType: 'image' }]
            : [{ path: '/evaluation', icon: '/6.png', label: '评估页', iconType: 'image' }]),
        ],
      },
      {
        id: 'collaboration',
        title: '交流协作',
        items: [
          { path: '/chat', icon: '/玫瑰1.png', label: '智能对话', iconType: 'image' },
          { path: '/history', icon: '/玫瑰2.png', label: '对话历史', iconType: 'image' },
        ],
      },
    ]
    
    // 只有管理员可以看到后台管理
    if (isAdmin) {
      baseGroups.push({
        id: 'management',
        title: '管理',
        items: [
          { path: '/admin', icon: '/玫瑰6.png', label: '后台管理', iconType: 'image' },
        ],
      })
    }
    
    return baseGroups
  }
  
  const navGroups = getNavGroups()

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId],
    }))
  }

  return (
    <div className="flex h-screen bg-transparent transition-all duration-300 relative z-10">
      {/* 侧边栏 - 星球航行框架 */}
      <aside className="w-64 glass dark:bg-black/30 border-r-2 border-paper-300 dark:border-purple-900/50 flex flex-col shadow-lg relative">
        {/* 细金色亮边 - 模拟星球轨道 */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 border-2 border-transparent bg-gradient-to-r from-transparent via-yellow-400/20 to-transparent opacity-50 dark:via-yellow-300/30"></div>
        </div>
        {/* Logo */}
        <div className="p-6 border-b border-paper-300 dark:border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center shadow-lg animate-float overflow-hidden">
              <img src="/头像.jpg" alt="影视教育AI" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="text-gold dark:text-white font-bold text-lg gradient-text">影视教育AI</h1>
              <p className="text-gold-700 dark:text-slate-400 text-xs">智能助手平台</p>
            </div>
          </div>
        </div>

        {/* 分组导航菜单 */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto scrollbar-hide">
          {navGroups.map((group) => {
            // 首页单独显示，不分组
            if (group.id === 'home') {
              const item = group.items[0]
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-primary-500 dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                      : 'text-gold dark:text-slate-300 hover:bg-white/50 dark:hover:bg-white/10'
                  }`}
                >
                  {item.iconType === 'image' ? (
                    <img src={item.icon as string} alt={item.label} className="w-5 h-5 object-contain" />
                  ) : null}
                  <span className="font-medium">{item.label}</span>
                </Link>
              )
            }

            // 分组菜单
            const isExpanded = expandedGroups[group.id]
            const hasActiveItem = group.items.some(item => location.pathname === item.path)

            return (
              <div key={group.id} className="mb-2">
                <button
                  onClick={() => toggleGroup(group.id)}
                  className={`w-full flex items-center justify-between px-4 py-2 rounded-lg transition-all duration-200 ${
                    hasActiveItem
                      ? 'bg-primary-100 dark:bg-purple-900/20 text-primary-700 dark:text-purple-300'
                      : 'text-gold-700 dark:text-slate-400 hover:bg-white/30 dark:hover:bg-white/5'
                  }`}
                >
                  <span className="text-xs font-semibold uppercase tracking-wide">{group.title}</span>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 transition-transform duration-200" />
                  ) : (
                    <ChevronRight className="w-4 h-4 transition-transform duration-200" />
                  )}
                </button>
                {isExpanded && (
                  <div className="mt-1 space-y-1 pl-2">
                    {group.items.map((item) => {
                      const iconSrc = item.iconType === 'image' ? item.icon : null
                      const isActive = location.pathname === item.path
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${
                            isActive
                              ? 'bg-primary-500 dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-md'
                              : 'text-gold dark:text-slate-300 hover:bg-white/50 dark:hover:bg-white/10'
                          }`}
                        >
                          {item.iconType === 'image' && iconSrc ? (
                            <img src={iconSrc as string} alt={item.label} className="w-4 h-4 object-contain" />
                          ) : null}
                          <span className="text-sm font-medium">{item.label}</span>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* 底部信息 */}
        <div className="p-4 border-t border-paper-300 dark:border-dark-border">
          <div className="text-xs text-gold-700 dark:text-slate-400 text-center">
            <p>版本 1.0.0</p>
            <p className="mt-1">原创：王霸队</p>
          </div>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部导航栏 - 细长星轨 */}
        <div className="glass border-b border-paper-300 dark:border-dark-border px-6 py-4 flex items-center justify-between relative">
          {/* 星轨装饰 - 两侧缓慢移动的小星点 */}
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-px pointer-events-none">
            <div className="absolute left-0 top-0 w-2 h-2 bg-yellow-400/60 rounded-full animate-pulse" style={{ animationDelay: '0s' }}></div>
            <div className="absolute left-1/4 top-0 w-1 h-1 bg-yellow-300/40 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }}></div>
            <div className="absolute right-1/4 top-0 w-1 h-1 bg-yellow-300/40 rounded-full animate-pulse" style={{ animationDelay: '1s' }}></div>
            <div className="absolute right-0 top-0 w-2 h-2 bg-yellow-400/60 rounded-full animate-pulse" style={{ animationDelay: '1.5s' }}></div>
          </div>
          <div className="flex-1 relative z-10">
            <Breadcrumb />
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            {isLoggedIn ? (
              <Link
                to="/profile"
                className="flex items-center gap-2 px-4 py-2 glass hover:bg-white/20 dark:hover:bg-white/10 rounded-lg transition-all card-hover"
              >
                {userInfo?.avatar_url ? (
                  <img
                    src={(() => {
                      const url = userInfo.avatar_url
                      if (url.startsWith('http://localhost:8000') || url.startsWith('http://127.0.0.1:8000')) {
                        // 如果是localhost:8000，提取路径部分
                        try {
                          const urlObj = new URL(url)
                          return urlObj.pathname
                        } catch {
                          return url.replace(/^https?:\/\/[^/]+/, '')
                        }
                      }
                      if (url.startsWith('http://') || url.startsWith('https://')) {
                        // 如果是其他完整URL，提取路径部分
                        try {
                          const urlObj = new URL(url)
                          return urlObj.pathname
                        } catch {
                          return url
                        }
                      }
                      // 相对路径，确保以 / 开头
                      return url.startsWith('/') ? url : `/${url}`
                    })()}
                    alt="头像"
                    className="w-8 h-8 rounded-full object-cover border-2 border-white/20"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                      const parent = e.currentTarget.parentElement
                      if (parent && !parent.querySelector('div')) {
                        const fallback = document.createElement('div')
                        fallback.className = 'w-8 h-8 rounded-full bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 flex items-center justify-center'
                        fallback.innerHTML = '<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>'
                        parent.appendChild(fallback)
                      }
                    }}
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
                <span className="text-gold dark:text-slate-300 text-sm">{userInfo?.username || '用户'}</span>
              </Link>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-gold dark:text-slate-300 hover:text-blue-600 dark:hover:text-neon-blue transition-colors"
                >
                  登录
                </Link>
                <Link
                  to="/login"
                  className="px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all card-hover"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </main>
    </div>
  )
}

