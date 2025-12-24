import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, BookOpen, Settings, BarChart3, Shield, Trash2, Edit } from 'lucide-react'
import { api } from '../utils/api'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
}

interface Course {
  id: number
  name: string
  description: string
  teacher_id: number
}

export default function AdminPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'users' | 'courses' | 'settings'>('users')
  const [users, setUsers] = useState<User[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [userInfo, setUserInfo] = useState<any>(null)
  
  useEffect(() => {
    loadUserInfo()
  }, [])
  
  const loadUserInfo = async () => {
    try {
      const res = await api.get('/api/auth/me')
      setUserInfo(res.data)
      // 检查是否是管理员
      if (res.data.role !== 'admin') {
        alert('您没有权限访问此页面')
        navigate('/')
      }
    } catch (error) {
      console.error('加载用户信息失败:', error)
      navigate('/login')
    }
  }

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers()
    } else if (activeTab === 'courses') {
      loadCourses()
    }
  }, [activeTab])

  const loadUsers = async () => {
    try {
      const res = await api.get('/api/admin/users')
      setUsers(res.data)
    } catch (error: any) {
      console.error('加载用户失败:', error)
      if (error.response?.status === 403) {
        alert('您没有权限访问此功能')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadCourses = async () => {
    try {
      const res = await api.get('/api/courses/')
      setCourses(res.data)
    } catch (error) {
      console.error('加载课程失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleUserStatus = async (userId: number, isActive: boolean) => {
    try {
      const res = await api.put(`/api/admin/users/${userId}`, {
        is_active: !isActive
      })
      setUsers(users.map(u => u.id === userId ? { ...u, is_active: res.data.is_active } : u))
      alert('用户状态已更新')
    } catch (error: any) {
      alert('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const deleteUser = async (userId: number) => {
    if (!confirm('确定要删除此用户吗？此操作不可恢复！')) return
    try {
      await api.delete(`/api/admin/users/${userId}`)
      setUsers(users.filter(u => u.id !== userId))
      alert('用户已删除')
    } catch (error: any) {
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      student: '学生',
      teacher: '教师',
      admin: '管理员'
    }
    return labels[role] || role
  }

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      student: 'bg-blue-600',
      teacher: 'bg-green-600',
      admin: 'bg-purple-600'
    }
    return colors[role] || 'bg-slate-600'
  }

  return (
    <div className="h-full flex flex-col bg-gradient-paper dark:bg-transparent transition-all duration-300 relative z-10">
      {/* 顶部导航 */}
      <div className="glass border-b border-paper-300 dark:border-dark-border p-4 flex items-center justify-between">
        <div>
          <h1 className="page-title bg-gradient-to-r from-amber-400 via-sky-400 to-violet-500 bg-clip-text text-transparent">
            管理星球 · 后台管理
          </h1>
          <p className="mt-1 text-sm md:text-base text-slate-600 dark:text-slate-300">
            在这里管理整颗小王子学习宇宙里的用户、课程与系统参数。
          </p>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧菜单 */}
        <div className="w-64 glass border-r border-paper-300 dark:border-dark-border">
          <div className="p-4 space-y-2">
            <button
              onClick={() => setActiveTab('users')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all card-hover ${
                activeTab === 'users'
                  ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                  : 'text-gold dark:text-slate-300 hover:bg-white/20 dark:hover:bg-white/10'
              }`}
            >
              <Users className={`w-5 h-5 ${activeTab === 'users' ? 'text-white' : 'text-gold dark:text-slate-300'}`} />
              用户管理
            </button>
            <button
              onClick={() => setActiveTab('courses')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all card-hover ${
                activeTab === 'courses'
                  ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                  : 'text-gold dark:text-slate-300 hover:bg-white/20 dark:hover:bg-white/10'
              }`}
            >
              <BookOpen className={`w-5 h-5 ${activeTab === 'courses' ? 'text-white' : 'text-gold dark:text-slate-300'}`} />
              课程管理
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all card-hover ${
                activeTab === 'settings'
                  ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                  : 'text-gold dark:text-slate-300 hover:bg-white/20 dark:hover:bg-white/10'
              }`}
            >
              <Settings className={`w-5 h-5 ${activeTab === 'settings' ? 'text-white' : 'text-gold dark:text-slate-300'}`} />
              系统设置
            </button>
          </div>
        </div>

        {/* 右侧内容区 */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'users' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="section-title text-slate-800 dark:text-slate-50">
                  用户星球 · 用户管理
                </h2>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-gold-600 dark:text-purple-300" />
                  <span className="text-gold-700 dark:text-purple-200">共 {users.length} 个用户</span>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="text-gold dark:text-white text-lg">加载中...</div>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-12 glass dark:bg-purple-900/10 rounded-xl border border-paper-300 dark:border-purple-900/50">
                  <Users className="w-16 h-16 text-gold-600 dark:text-purple-300 mx-auto mb-4" />
                  <p className="text-gold-700 dark:text-purple-200">暂无用户数据</p>
                  <p className="text-gold-600 dark:text-purple-300 text-sm mt-2">需要后端提供管理员用户列表API</p>
                </div>
              ) : (
                <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl overflow-hidden border border-paper-300 dark:border-purple-900/50">
                  <table className="w-full">
                    <thead className="bg-white/20 dark:bg-purple-900/40">
                      <tr>
                        <th className="px-6 py-3 text-left text-gold dark:text-purple-200 font-semibold">用户名</th>
                        <th className="px-6 py-3 text-left text-gold dark:text-purple-200 font-semibold">邮箱</th>
                        <th className="px-6 py-3 text-left text-gold dark:text-purple-200 font-semibold">角色</th>
                        <th className="px-6 py-3 text-left text-gold dark:text-purple-200 font-semibold">状态</th>
                        <th className="px-6 py-3 text-left text-gold dark:text-purple-200 font-semibold">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-t border-paper-300 dark:border-purple-900/50 hover:bg-white/20 dark:hover:bg-purple-900/30">
                          <td className="px-6 py-4 text-gold dark:text-white">{user.username}</td>
                          <td className="px-6 py-4 text-gold-700 dark:text-purple-200">{user.email}</td>
                          <td className="px-6 py-4">
                            <span
                              className={`px-2 py-1 rounded text-xs text-white ${getRoleColor(user.role)}`}
                            >
                              {getRoleLabel(user.role)}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span
                              className={`px-2 py-1 rounded text-xs ${
                                user.is_active
                                  ? 'bg-green-600 text-white'
                                  : 'bg-red-600 text-white'
                              }`}
                            >
                              {user.is_active ? '活跃' : '禁用'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex gap-2">
                              <button
                                onClick={() => toggleUserStatus(user.id, !user.is_active)}
                                className="p-2 text-gold-600 dark:text-purple-300 hover:text-gold dark:hover:text-white"
                                title={user.is_active ? '禁用用户' : '启用用户'}
                              >
                                <Shield className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteUser(user.id)}
                                className="p-2 text-slate-400 hover:text-red-400"
                                title="删除用户"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'courses' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="section-title text-slate-800 dark:text-slate-50">
                  书本星球 · 课程管理
                </h2>
                <span className="text-gold-700 dark:text-purple-200">共 {courses.length} 门课程</span>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="text-gold dark:text-white text-lg">加载中...</div>
                </div>
              ) : courses.length === 0 ? (
                <div className="text-center py-12 glass dark:bg-purple-900/10 rounded-xl border border-paper-300 dark:border-purple-900/50">
                  <BookOpen className="w-16 h-16 text-gold-600 dark:text-purple-300 mx-auto mb-4" />
                  <p className="text-gold-700 dark:text-purple-200">暂无课程</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {courses.map((course) => (
                    <div
                      key={course.id}
                      className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 border border-paper-300 dark:border-purple-900/50 hover:bg-white/20 dark:hover:bg-purple-900/30 transition-colors"
                    >
                      <h3 className="text-xl font-semibold text-gold dark:text-white mb-2">{course.name}</h3>
                      <p className="text-gold-700 dark:text-purple-200 text-sm mb-4 line-clamp-2">{course.description}</p>
                      <div className="flex gap-2">
                        <button className="flex-1 px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-colors">
                          查看详情
                        </button>
                        <button className="px-4 py-2 bg-gradient-creative dark:bg-purple-800 text-white dark:text-purple-100 rounded-lg hover:shadow-lg dark:hover:bg-purple-700 transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div>
                  <h2 className="section-title text-slate-800 dark:text-slate-50 mb-6">
                    管理星球 · 系统设置
                  </h2>
              <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 border border-paper-300 dark:border-purple-900/50 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gold dark:text-white mb-4">AI模型配置</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-gold dark:text-purple-200 mb-2">OpenAI API Key</label>
                      <input
                        type="password"
                        className="w-full px-4 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                        placeholder="配置OpenAI API密钥"
                      />
                    </div>
                    <div>
                      <label className="block text-gold dark:text-purple-200 mb-2">Stable Diffusion API URL</label>
                      <input
                        type="text"
                        className="w-full px-4 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                        placeholder="配置Stable Diffusion API地址"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gold dark:text-white mb-4">系统参数</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-gold dark:text-purple-200 mb-2">最大文件上传大小 (MB)</label>
                      <input
                        type="number"
                        className="w-full px-4 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                        defaultValue={500}
                      />
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button className="px-6 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-colors">
                    保存设置
                  </button>
                  <button className="px-6 py-2 bg-gradient-creative dark:bg-purple-800 text-white dark:text-purple-100 rounded-lg hover:shadow-lg dark:hover:bg-purple-700 transition-colors">
                    重置
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

