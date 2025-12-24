import { useState, useEffect } from 'react'
import { Users, Star, MessageSquare, FileText, Award, Search, Image, Video, FolderOpen } from 'lucide-react'
import { api } from '../utils/api'

interface Student {
  id: number
  username: string
  full_name: string
  email: string
  avatar_url?: string
  institution?: string
}

interface MediaAsset {
  id: number
  name: string
  asset_type: string
  file_path: string
  file_size: number
  mime_type: string
  created_at: string
}

interface Project {
  id: number
  name: string
  description: string
  status: string
  created_at: string
  media_assets: MediaAsset[]
}

interface Evaluation {
  id: number
  project_id: number
  evaluation_type: string
  cinematography_score: number | null
  editing_score: number | null
  sound_score: number | null
  overall_technical_score: number | null
  narrative_score: number | null
  visual_aesthetics_score: number | null
  emotional_impact_score: number | null
  overall_artistic_score: number | null
  technical_feedback: string | null
  artistic_feedback: string | null
  overall_comment: string | null
  suggestions: string | null
  teacher_feedback_box: string | null
  created_at: string
}

export default function TeacherManagementPage() {
  const [students, setStudents] = useState<Student[]>([])
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [isEvaluating, setIsEvaluating] = useState(false)

  // 评分表单状态
  const [scores, setScores] = useState({
    cinematography_score: 0,
    editing_score: 0,
    sound_score: 0,
    overall_technical_score: 0,
    narrative_score: 0,
    visual_aesthetics_score: 0,
    emotional_impact_score: 0,
    overall_artistic_score: 0,
  })
  const [feedback, setFeedback] = useState({
    technical_feedback: '',
    artistic_feedback: '',
    overall_comment: '',
    suggestions: '',
    teacher_feedback_box: '',
  })

  useEffect(() => {
    loadStudents()
  }, [])

  useEffect(() => {
    if (selectedStudent) {
      loadStudentProjects()
      setSelectedProject(null)
      setEvaluation(null)
    }
  }, [selectedStudent])

  useEffect(() => {
    if (selectedProject) {
      loadEvaluation()
    }
  }, [selectedProject])

  const loadStudents = async () => {
    try {
      const res = await api.get('/api/auth/students')
      setStudents(res.data)
    } catch (error: any) {
      console.error('加载学生列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStudentProjects = async () => {
    if (!selectedStudent) return
    try {
      const res = await api.get(`/api/auth/students/${selectedStudent.id}/projects`)
      setProjects(res.data)
    } catch (error: any) {
      console.error('加载项目失败:', error)
    }
  }

  const loadEvaluation = async () => {
    if (!selectedProject) return
    try {
      const res = await api.get(`/api/evaluations/project/${selectedProject.id}`)
      // 查找教师评估
      const teacherEval = res.data.find((e: Evaluation) => e.evaluation_type === 'teacher')
      if (teacherEval) {
        setEvaluation(teacherEval)
        setScores({
          cinematography_score: teacherEval.cinematography_score || 0,
          editing_score: teacherEval.editing_score || 0,
          sound_score: teacherEval.sound_score || 0,
          overall_technical_score: teacherEval.overall_technical_score || 0,
          narrative_score: teacherEval.narrative_score || 0,
          visual_aesthetics_score: teacherEval.visual_aesthetics_score || 0,
          emotional_impact_score: teacherEval.emotional_impact_score || 0,
          overall_artistic_score: teacherEval.overall_artistic_score || 0,
        })
        setFeedback({
          technical_feedback: teacherEval.technical_feedback || '',
          artistic_feedback: teacherEval.artistic_feedback || '',
          overall_comment: teacherEval.overall_comment || '',
          suggestions: teacherEval.suggestions || '',
          teacher_feedback_box: teacherEval.teacher_feedback_box || '',
        })
      } else {
        setEvaluation(null)
        setScores({
          cinematography_score: 0,
          editing_score: 0,
          sound_score: 0,
          overall_technical_score: 0,
          narrative_score: 0,
          visual_aesthetics_score: 0,
          emotional_impact_score: 0,
          overall_artistic_score: 0,
        })
        setFeedback({
          technical_feedback: '',
          artistic_feedback: '',
          overall_comment: '',
          suggestions: '',
          teacher_feedback_box: '',
        })
      }
    } catch (error: any) {
      console.error('加载评估失败:', error)
    }
  }

  const handleSubmitEvaluation = async () => {
    if (!selectedProject) return

    setIsEvaluating(true)
    try {
      const evaluationData = {
        project_id: selectedProject.id,
        evaluation_type: 'teacher',
        ...scores,
        ...feedback,
      }

      if (evaluation) {
        // 更新现有评估
        await api.put(`/api/evaluations/${evaluation.id}`, evaluationData)
        alert('评估已更新！')
      } else {
        // 创建新评估
        await api.post('/api/evaluations/', evaluationData)
        alert('评估已提交！')
      }

      await loadEvaluation()
      await loadStudentProjects()
    } catch (error: any) {
      alert('提交评估失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsEvaluating(false)
    }
  }

  const filteredStudents = students.filter((student) =>
    student.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.username.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getMediaUrl = (filePath: string) => {
    if (filePath.startsWith('http')) return filePath
    if (filePath.startsWith('/')) return filePath
    return `/${filePath}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gold dark:text-white text-lg">加载中...</div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-paper dark:bg-transparent p-8 transition-all duration-300 relative z-10">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 animate-slide-up">
          <h1 className="page-title bg-gradient-to-r from-blue-400 via-purple-500 to-pink-300 bg-clip-text text-transparent mb-2">
            教师管理 · 学生作品管理
          </h1>
          <p className="text-lg text-gold-700 dark:text-purple-200">
            管理所有学生，查看学生作品，为学生项目打分和留言
          </p>
        </div>

        {/* 搜索框 */}
        <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 mb-6 border border-paper-300 dark:border-purple-900/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gold-600 dark:text-purple-300" />
            <input
              type="text"
              placeholder="搜索学生..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
            />
          </div>
        </div>

        {/* 内容区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：学生列表 */}
          <div className="lg:col-span-1">
            <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-4 border border-paper-300 dark:border-purple-900/50 max-h-[700px] overflow-y-auto">
              <h3 className="text-lg font-semibold text-gold dark:text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                学生列表 ({filteredStudents.length})
              </h3>
              {filteredStudents.length === 0 ? (
                <p className="text-gold-700 dark:text-purple-200 text-center py-8">暂无学生</p>
              ) : (
                <div className="space-y-3">
                  {filteredStudents.map((student) => (
                    <div
                      key={student.id}
                      onClick={() => setSelectedStudent(student)}
                      className={`p-4 rounded-lg cursor-pointer transition-all ${
                        selectedStudent?.id === student.id
                          ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white'
                          : 'bg-white/50 dark:bg-dark-card hover:bg-white/70 dark:hover:bg-dark-card/70 text-gold dark:text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {student.avatar_url ? (
                          <img
                            src={student.avatar_url.startsWith('/') ? student.avatar_url : `/${student.avatar_url}`}
                            alt={student.full_name || student.username}
                            className="w-10 h-10 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 flex items-center justify-center text-white">
                            {(student.full_name || student.username)[0].toUpperCase()}
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="font-semibold">{student.full_name || student.username}</div>
                          <div className="text-sm opacity-80">{student.username}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 右侧：项目列表和评估表单 */}
          <div className="lg:col-span-2 space-y-6">
            {selectedStudent ? (
              <>
                {/* 项目列表 */}
                <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 border border-paper-300 dark:border-purple-900/50">
                  <h3 className="text-lg font-semibold text-gold dark:text-white mb-4 flex items-center gap-2">
                    <FolderOpen className="w-5 h-5" />
                    {selectedStudent.full_name || selectedStudent.username} 的项目 ({projects.length})
                  </h3>
                  {projects.length === 0 ? (
                    <p className="text-gold-700 dark:text-purple-200 text-center py-8">该学生暂无项目</p>
                  ) : (
                    <div className="space-y-3">
                      {projects.map((project) => (
                        <div
                          key={project.id}
                          onClick={() => setSelectedProject(project)}
                          className={`p-4 rounded-lg cursor-pointer transition-all ${
                            selectedProject?.id === project.id
                              ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white'
                              : 'bg-white/50 dark:bg-dark-card hover:bg-white/70 dark:hover:bg-dark-card/70 text-gold dark:text-slate-300'
                          }`}
                        >
                          <div className="font-semibold mb-2">{project.name}</div>
                          <div className="text-sm opacity-80 mb-2 line-clamp-2">{project.description || '无描述'}</div>
                          <div className="flex items-center gap-4 text-xs opacity-70">
                            <span className="flex items-center gap-1">
                              <Image className="w-4 h-4" />
                              {project.media_assets.filter(a => a.asset_type === 'image').length} 图片
                            </span>
                            <span className="flex items-center gap-1">
                              <Video className="w-4 h-4" />
                              {project.media_assets.filter(a => a.asset_type === 'video').length} 视频
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 项目详情和评估表单 */}
                {selectedProject && (
                  <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 border border-paper-300 dark:border-purple-900/50">
                    <div className="mb-6">
                      <h2 className="text-2xl font-bold text-gold dark:text-white mb-2">{selectedProject.name}</h2>
                      <p className="text-gold-700 dark:text-purple-200 mb-4">{selectedProject.description || '无描述'}</p>
                      
                      {/* 媒体资产展示 */}
                      {selectedProject.media_assets.length > 0 && (
                        <div className="mb-6">
                          <h4 className="text-md font-semibold text-gold dark:text-white mb-3">生成的图片和视频</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {selectedProject.media_assets.map((asset) => (
                              <div key={asset.id} className="relative">
                                {asset.asset_type === 'image' ? (
                                  <img
                                    src={getMediaUrl(asset.file_path)}
                                    alt={asset.name}
                                    className="w-full h-32 object-cover rounded-lg border border-paper-300 dark:border-purple-900/50"
                                    onError={(e) => {
                                      e.currentTarget.style.display = 'none'
                                    }}
                                  />
                                ) : asset.asset_type === 'video' ? (
                                  <video
                                    src={getMediaUrl(asset.file_path)}
                                    className="w-full h-32 object-cover rounded-lg border border-paper-300 dark:border-purple-900/50"
                                    controls
                                  />
                                ) : null}
                                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs p-1 rounded-b-lg truncate">
                                  {asset.name}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 评估表单 */}
                    <div className="space-y-6">
                      {/* 技术指标 */}
                      <div>
                        <h3 className="text-lg font-semibold text-gold dark:text-white mb-4">技术指标评分 (0-10分)</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {[
                            { key: 'cinematography_score', label: '摄影技术' },
                            { key: 'editing_score', label: '剪辑质量' },
                            { key: 'sound_score', label: '声音质量' },
                            { key: 'overall_technical_score', label: '总体技术分' },
                          ].map(({ key, label }) => (
                            <div key={key}>
                              <label className="block text-sm text-gold-700 dark:text-purple-200 mb-1">{label}</label>
                              <input
                                type="number"
                                min="0"
                                max="10"
                                step="0.1"
                                value={scores[key as keyof typeof scores]}
                                onChange={(e) => setScores({ ...scores, [key]: parseFloat(e.target.value) || 0 })}
                                className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 艺术指标 */}
                      <div>
                        <h3 className="text-lg font-semibold text-gold dark:text-white mb-4">艺术指标评分 (0-10分)</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {[
                            { key: 'narrative_score', label: '叙事' },
                            { key: 'visual_aesthetics_score', label: '视觉美感' },
                            { key: 'emotional_impact_score', label: '情感感染力' },
                            { key: 'overall_artistic_score', label: '总体艺术分' },
                          ].map(({ key, label }) => (
                            <div key={key}>
                              <label className="block text-sm text-gold-700 dark:text-purple-200 mb-1">{label}</label>
                              <input
                                type="number"
                                min="0"
                                max="10"
                                step="0.1"
                                value={scores[key as keyof typeof scores]}
                                onChange={(e) => setScores({ ...scores, [key]: parseFloat(e.target.value) || 0 })}
                                className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 评语 */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-semibold text-gold dark:text-white mb-2">技术反馈</label>
                          <textarea
                            value={feedback.technical_feedback}
                            onChange={(e) => setFeedback({ ...feedback, technical_feedback: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                            placeholder="请输入技术层面的反馈..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gold dark:text-white mb-2">艺术反馈</label>
                          <textarea
                            value={feedback.artistic_feedback}
                            onChange={(e) => setFeedback({ ...feedback, artistic_feedback: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                            placeholder="请输入艺术层面的反馈..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gold dark:text-white mb-2">总体评语</label>
                          <textarea
                            value={feedback.overall_comment}
                            onChange={(e) => setFeedback({ ...feedback, overall_comment: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                            placeholder="请输入总体评语..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gold dark:text-white mb-2">改进建议</label>
                          <textarea
                            value={feedback.suggestions}
                            onChange={(e) => setFeedback({ ...feedback, suggestions: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                            placeholder="请输入改进建议..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gold dark:text-white mb-2">
                            <MessageSquare className="w-4 h-4 inline mr-1" />
                            留言箱
                          </label>
                          <textarea
                            value={feedback.teacher_feedback_box}
                            onChange={(e) => setFeedback({ ...feedback, teacher_feedback_box: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
                            placeholder="给学生留言..."
                          />
                        </div>
                      </div>

                      {/* 提交按钮 */}
                      <button
                        onClick={handleSubmitEvaluation}
                        disabled={isEvaluating}
                        className="w-full px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Star className="w-5 h-5" />
                        {isEvaluating ? '提交中...' : evaluation ? '更新评估' : '提交评估'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-12 text-center border border-paper-300 dark:border-purple-900/50">
                <FileText className="w-16 h-16 text-gold-600 dark:text-purple-300 mx-auto mb-4" />
                <p className="text-gold-700 dark:text-purple-200">请选择一个学生查看其项目和作品</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
