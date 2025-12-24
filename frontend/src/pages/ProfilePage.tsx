import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Camera, Save, LogOut, ArrowLeft } from 'lucide-react'
import { api } from '../utils/api'

interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string
  avatar_url?: string
  role: string
  institution?: string
}

export default function ProfilePage() {
  const navigate = useNavigate()
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [username, setUsername] = useState('')
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)

  useEffect(() => {
    loadUserInfo()
  }, [])

  const loadUserInfo = async () => {
    try {
      const res = await api.get('/api/auth/me')
      setUserInfo(res.data)
      setUsername(res.data.username || '')
      if (res.data.avatar_url) {
        // 确保头像URL使用相对路径（本地部署）
        const avatarUrl = res.data.avatar_url
        const normalizedUrl = avatarUrl.startsWith('http') 
          ? avatarUrl.replace(/^https?:\/\/[^/]+/, '') 
          : avatarUrl.startsWith('/') 
            ? avatarUrl 
            : `/${avatarUrl}`
        setAvatarPreview(normalizedUrl)
      }
    } catch (error: any) {
      console.error('加载用户信息失败:', error)
      if (error.response?.status === 401) {
        navigate('/login')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 检查文件大小（限制5MB）
    if (file.size > 5 * 1024 * 1024) {
      alert('头像文件大小不能超过5MB')
      return
    }

    // 预览图片
    const reader = new FileReader()
    reader.onload = (event) => {
      setAvatarPreview(event.target?.result as string)
    }
    reader.readAsDataURL(file)

    // 上传头像
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const res = await api.post('/api/auth/me/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      if (res.data.avatar_url) {
        const avatarUrl = res.data.avatar_url
        // 确保使用相对路径（本地部署）
        const normalizedUrl = avatarUrl.startsWith('http') 
          ? avatarUrl.replace(/^https?:\/\/[^/]+/, '') 
          : avatarUrl.startsWith('/') 
            ? avatarUrl 
            : `/${avatarUrl}`
        setAvatarPreview(normalizedUrl)
        if (userInfo) {
          setUserInfo({ ...userInfo, avatar_url: normalizedUrl })
        }
        await loadUserInfo()
        alert('头像上传成功！')
      }
    } catch (error: any) {
      alert('头像上传失败: ' + (error.response?.data?.detail || error.message))
      if (userInfo?.avatar_url) {
        setAvatarPreview(userInfo.avatar_url)
      } else {
        setAvatarPreview(null)
      }
    }
  }

  const handleSave = async () => {
    if (!userInfo) return

    setSaving(true)
    try {
      const res = await api.put('/api/auth/me', {
        username: username
      })
      setUserInfo(res.data)
      setUsername(res.data.username || '')
      await loadUserInfo()
      alert('保存成功！')
    } catch (error: any) {
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      localStorage.removeItem('access_token')
      navigate('/login')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gold dark:text-white text-lg animate-pulse">加载中...</div>
      </div>
    )
  }

  if (!userInfo) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gold-700 dark:text-slate-400 mb-4">无法加载用户信息</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg card-hover"
          >
            返回首页
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-paper dark:bg-transparent p-8 transition-all duration-300 relative z-10">
      <div className="max-w-4xl mx-auto">
        {/* 返回按钮 */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gold-700 dark:text-slate-400 hover:text-gold dark:hover:text-slate-300 mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回主星球</span>
        </button>

        {/* 标题：个人星球 */}
        <div className="mb-8 animate-slide-up">
          <h1 className="page-title bg-gradient-to-r from-amber-400 via-sky-400 to-violet-500 bg-clip-text text-transparent mb-2">
            个人星球 · 个人中心
          </h1>
          <p className="text-lg text-gold-700 dark:text-purple-200">
            在这颗小小的行星上，保存你的名字、头像和身份信息。
          </p>
        </div>

        {/* 个人信息卡片 */}
        <div className="glass-card dark:bg-purple-900/10 p-8 animate-slide-up">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* 左侧：头像区域 */}
            <div className="flex flex-col items-center">
              <div className="relative mb-4">
                <div className="w-32 h-32 rounded-full bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 flex items-center justify-center overflow-hidden shadow-lg">
                  {avatarPreview ? (
                    <img
                      src={avatarPreview.startsWith('http') || avatarPreview.startsWith('data:') 
                        ? avatarPreview 
                        : avatarPreview.startsWith('/') 
                          ? avatarPreview 
                          : `/${avatarPreview}`}
                      alt="头像"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const parent = e.currentTarget.parentElement
                        if (parent) {
                          parent.innerHTML = '<div class="w-full h-full flex items-center justify-center"><svg class="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg></div>'
                        }
                      }}
                    />
                  ) : (
                    <User className="w-16 h-16 text-white" />
                  )}
                </div>
                <label className="absolute bottom-0 right-0 w-10 h-10 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-full flex items-center justify-center cursor-pointer hover:shadow-lg transition-all card-hover">
                  <Camera className="w-5 h-5 text-white" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    className="hidden"
                  />
                </label>
              </div>
              <p className="text-sm text-gold-700 dark:text-slate-400 text-center">
                点击相机图标上传头像
              </p>
            </div>

            {/* 右侧：信息编辑 */}
            <div className="md:col-span-2 space-y-6">
              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">用户名</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  placeholder="输入用户名"
                />
                <p className="text-xs text-gold-600 dark:text-slate-500 mt-1">用户名可以修改</p>
              </div>

              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">邮箱</label>
                <input
                  type="email"
                  value={userInfo.email}
                  disabled
                  className="w-full px-4 py-3 bg-white/30 dark:bg-dark-card/50 border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white cursor-not-allowed opacity-60"
                />
                <p className="text-xs text-gold-600 dark:text-slate-500 mt-1">邮箱不可修改</p>
              </div>

              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">姓名</label>
                <input
                  type="text"
                  value={userInfo.full_name || ''}
                  disabled
                  className="w-full px-4 py-3 bg-white/30 dark:bg-dark-card/50 border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white cursor-not-allowed opacity-60"
                />
                <p className="text-xs text-gold-600 dark:text-slate-500 mt-1">姓名不可修改</p>
              </div>

              <div>
                <label className="block text-gold dark:text-purple-200 mb-2">角色</label>
                <div className="px-4 py-3 bg-white/30 dark:bg-dark-card/50 border border-paper-300 dark:border-dark-border rounded-lg">
                  <span className="inline-block px-3 py-1 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white text-sm rounded">
                    {userInfo.role === 'student' ? '学生' : userInfo.role === 'teacher' ? '教师' : '管理员'}
                  </span>
                </div>
              </div>

              {userInfo.institution && (
                <div>
                  <label className="block text-gold dark:text-purple-200 mb-2">所属机构</label>
                  <input
                    type="text"
                    value={userInfo.institution}
                    disabled
                    className="w-full px-4 py-3 bg-white/30 dark:bg-dark-card/50 border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white cursor-not-allowed opacity-60"
                  />
                </div>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="mt-8 flex gap-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
            >
              {saving ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  保存中...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  保存修改
                </>
              )}
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-6 py-3 glass text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-all card-hover"
            >
              <LogOut className="w-5 h-5" />
              退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
