import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Film, Mail, Lock, User, Eye, EyeOff } from 'lucide-react'
import { api } from '../utils/api'
import axios from 'axios'

// 获取API基础URL（用于登录时的form-urlencoded请求）
// 在开发环境，始终使用相对路径通过Vite代理，避免CORS问题
const getApiBaseUrl = () => {
  // 开发环境：使用相对路径，通过Vite代理
  // 生产环境：如果设置了VITE_API_URL，使用它；否则使用相对路径（通过Nginx代理）
  const envUrl = import.meta.env.VITE_API_URL
  // 如果设置了环境变量且不是开发模式，使用环境变量
  // 否则使用相对路径（通过代理）
  if (envUrl && !import.meta.env.DEV) {
    return envUrl
  }
  // 开发环境或未设置环境变量时，使用相对路径
  return ''
}

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('student')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      // OAuth2PasswordRequestForm 需要 application/x-www-form-urlencoded 格式
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      
      const apiBaseUrl = getApiBaseUrl()
      const res = await axios.post(`${apiBaseUrl}/api/auth/login`, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        withCredentials: false,  // 避免CORS预检问题
      })
      
      localStorage.setItem('access_token', res.data.access_token)
      // 登录成功后跳转到首页
      navigate('/')
      setLoading(false)
    } catch (error: any) {
      console.error('登录错误:', error)
      const errorMessage = error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码'
      alert('登录失败: ' + errorMessage)
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const res = await api.post('/api/auth/register', {
        username,
        email,
        password,
        full_name: fullName,
        role
      })
      
      // 注册成功后自动登录
      localStorage.setItem('access_token', res.data.access_token)
      
      // 直接跳转到首页，不需要再登录
      navigate('/')
    } catch (error: any) {
      alert('注册失败: ' + (error.response?.data?.detail || error.message))
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-paper dark:bg-transparent flex items-center justify-center p-4 pb-8 transition-all duration-300 relative z-10 overflow-y-auto">
      <div className="w-full max-w-lg my-8">
        {/* Logo */}
        <div className="text-center mb-8 animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 shadow-lg animate-float overflow-hidden">
            <img src="/头像.jpg" alt="影视教育AI" className="w-full h-full object-cover" />
          </div>
          <h1 className="page-title bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 bg-clip-text text-transparent mb-2">
            影视制作星球智能体
          </h1>
          <p className="text-lg text-gold-700 dark:text-slate-400">
            从这里进入小王子的宇宙课堂与创作星球。
          </p>
        </div>

        {/* 表单卡片 */}
        <div className="glass rounded-2xl p-8 shadow-2xl animate-scale-in">
          {/* 切换标签 */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 rounded-lg font-medium transition-all card-hover ${
                isLogin
                  ? 'bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 text-white shadow-lg'
                  : 'glass text-gold dark:text-purple-200 hover:bg-white/20 dark:hover:bg-white/10'
              }`}
            >
              登录
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 rounded-lg font-medium transition-all card-hover ${
                !isLogin
                  ? 'bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 text-white shadow-lg'
                  : 'glass text-gold dark:text-purple-200 hover:bg-white/20 dark:hover:bg-white/10'
              }`}
            >
              注册
            </button>
          </div>

          {/* 登录表单 */}
          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">用户名</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                    placeholder="输入用户名"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-12 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                    placeholder="输入密码"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gold-600 dark:text-slate-400 hover:text-gold dark:hover:text-slate-300 transition-colors"
                    aria-label={showPassword ? "隐藏密码" : "显示密码"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 text-white rounded-lg font-semibold hover:shadow-lg hover:from-sky-500 hover:via-violet-500 hover:to-rose-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
              >
                {loading ? '登录中...' : '登录'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">用户名</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                    placeholder="输入用户名"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">邮箱</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                    placeholder="输入邮箱"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">姓名</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                  placeholder="输入真实姓名"
                  required
                />
              </div>
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">角色</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-4 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                >
                  <option value="student">学生</option>
                  <option value="teacher">教师</option>
                </select>
              </div>
              <div>
                <label className="block text-gold dark:text-slate-300 mb-2">密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-12 py-3 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-gold dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue transition-all"
                    placeholder="输入密码（至少6位）"
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gold-600 dark:text-slate-400 hover:text-gold dark:hover:text-slate-300 transition-colors"
                    aria-label={showPassword ? "隐藏密码" : "显示密码"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-sky-400 via-violet-400 to-rose-400 text-white rounded-lg font-semibold hover:shadow-lg hover:from-sky-500 hover:via-violet-500 hover:to-rose-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
              >
                {loading ? '注册中...' : '注册'}
              </button>
            </form>
          )}
        </div>

        {/* 底部信息 */}
        <p className="text-center text-gold-700 dark:text-slate-400 text-sm mt-6 mb-4">
          登录即表示您同意我们的服务条款和隐私政策
        </p>
      </div>
    </div>
  )
}

