import { useEffect, useState } from 'react'
import { FileText, Star, TrendingUp, Download, Sparkles, MessageSquare } from 'lucide-react'
import { api } from '../utils/api'

interface Evaluation {
  id: number
  project_id: number
  evaluator_user_id: number | null
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

interface Project {
  id: number
  name: string
  status: string
}

export default function EvaluationPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (selectedProjectId) {
      loadEvaluations(selectedProjectId)
    }
  }, [selectedProjectId])

  const loadProjects = async () => {
    try {
      const res = await api.get('/api/projects/')
      setProjects(res.data)
      if (res.data.length > 0) {
        setSelectedProjectId(res.data[0].id)
      }
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载项目失败:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadEvaluations = async (projectId: number) => {
    try {
      const res = await api.get(`/api/evaluations/project/${projectId}`)
      setEvaluations(res.data)
    } catch (error: any) {
      if (error.code !== 'ERR_NETWORK') {
        console.error('加载评估失败:', error)
      }
    }
  }

  const requestAIEvaluation = async () => {
    if (!selectedProjectId) return

    setIsEvaluating(true)
    try {
      const res = await api.post(`/api/evaluations/project/${selectedProjectId}/ai-evaluate`)
      // 评估完成后立即刷新评估列表，在页面内显示结果
      await loadEvaluations(selectedProjectId)
      setIsEvaluating(false)
    } catch (error: any) {
      console.error('请求评估失败:', error)
      setError(error.response?.data?.detail || error.message || '请求评估失败，请稍后重试')
      setIsEvaluating(false)
      // 3秒后清除错误提示
      setTimeout(() => setError(null), 3000)
    }
  }

  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-slate-400'
    if (score >= 8) return 'text-green-400'
    if (score >= 6) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getEvaluationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      ai_auto: 'AI自动评估',
      teacher: '教师评估',
      peer: '同伴互评',
      self: '自评'
    }
    return labels[type] || type
  }

  const getEvaluationTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      ai_auto: 'bg-purple-600',
      teacher: 'bg-blue-600',
      peer: 'bg-green-600',
      self: 'bg-yellow-600'
    }
    return colors[type] || 'bg-slate-600'
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
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 animate-slide-up">
          <h1 className="page-title bg-gradient-to-r from-indigo-400 via-violet-500 to-amber-300 bg-clip-text text-transparent mb-2">
            评审星球 · 作品评估
          </h1>
          <p className="text-lg text-gold-700 dark:text-purple-200">
            在评审星球上，小王子与裁判一起，从技术和艺术两个维度为你的作品照亮星光。
          </p>
        </div>

        {/* 项目选择 */}
        <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 mb-6 border border-paper-300 dark:border-purple-900/50">
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-gold dark:text-purple-200 mb-2">选择项目</label>
              <select
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                className="px-4 py-2 bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-purple-900/50 rounded-lg text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-purple-500"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={requestAIEvaluation}
              disabled={isEvaluating || !selectedProjectId}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-5 h-5" />
              {isEvaluating ? '评估中...' : '请求AI评估'}
            </button>
          </div>
          {/* 错误提示（在页面内显示，不用弹窗） */}
          {error && (
            <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* 评估列表 */}
        {evaluations.length === 0 ? (
          <div className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-12 text-center border border-paper-300 dark:border-purple-900/50">
            <FileText className="w-16 h-16 text-gold-600 dark:text-purple-300 mx-auto mb-4" />
            <p className="text-gold-700 dark:text-purple-200 mb-4">该项目还没有评估记录</p>
            <button
              onClick={requestAIEvaluation}
              className="px-6 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-colors"
            >
              请求AI评估
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {evaluations.map((evaluation) => (
              <div
                key={evaluation.id}
                className="glass dark:bg-purple-900/10 backdrop-blur-lg rounded-xl p-6 border border-paper-300 dark:border-purple-900/50"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-sm text-white ${getEvaluationTypeColor(
                        evaluation.evaluation_type
                      )}`}
                    >
                      {getEvaluationTypeLabel(evaluation.evaluation_type)}
                    </span>
                    <span className="text-gold-700 dark:text-purple-200 text-sm">
                      {new Date(evaluation.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <button className="p-2 text-gold-600 dark:text-purple-300 hover:text-gold dark:hover:text-white">
                    <Download className="w-4 h-4" />
                  </button>
                </div>

                {/* 技术指标评分 */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gold dark:text-white mb-3">技术指标</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">摄影技术</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.cinematography_score)}`}>
                        {evaluation.cinematography_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">剪辑质量</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.editing_score)}`}>
                        {evaluation.editing_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">声音质量</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.sound_score)}`}>
                        {evaluation.sound_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-primary-500/30 dark:bg-purple-800/40 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">总体技术分</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.overall_technical_score)}`}>
                        {evaluation.overall_technical_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 艺术指标评分 */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gold dark:text-white mb-3">艺术指标</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">叙事</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.narrative_score)}`}>
                        {evaluation.narrative_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">视觉美感</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.visual_aesthetics_score)}`}>
                        {evaluation.visual_aesthetics_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">情感感染力</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.emotional_impact_score)}`}>
                        {evaluation.emotional_impact_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                    <div className="bg-accent-500/30 dark:bg-purple-800/40 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <div className="text-gold-700 dark:text-purple-200 text-sm mb-1">总体艺术分</div>
                      <div className={`text-2xl font-bold ${getScoreColor(evaluation.overall_artistic_score)}`}>
                        {evaluation.overall_artistic_score?.toFixed(1) || '-'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 评语和建议 */}
                <div className="space-y-4">
                  {evaluation.technical_feedback && (
                    <div className="bg-primary-500/30 dark:bg-purple-900/40 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <h4 className="text-gold dark:text-purple-200 font-semibold mb-2">技术反馈</h4>
                      <p className="text-gold dark:text-purple-100">{evaluation.technical_feedback}</p>
                    </div>
                  )}
                  {evaluation.artistic_feedback && (
                    <div className="bg-primary-600/30 dark:bg-purple-900/40 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <h4 className="text-gold dark:text-purple-200 font-semibold mb-2">艺术反馈</h4>
                      <p className="text-gold dark:text-purple-100">{evaluation.artistic_feedback}</p>
                    </div>
                  )}
                  {evaluation.overall_comment && (
                    <div className="bg-white/30 dark:bg-purple-900/30 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <h4 className="text-gold dark:text-white font-semibold mb-2">总体评语</h4>
                      <p className="text-gold dark:text-purple-100">{evaluation.overall_comment}</p>
                    </div>
                  )}
                  {evaluation.suggestions && (
                    <div className="bg-accent-500/30 dark:bg-purple-800/40 rounded-lg p-4 border border-paper-300 dark:border-purple-800/50">
                      <h4 className="text-gold dark:text-purple-200 font-semibold mb-2">改进建议</h4>
                      <p className="text-gold dark:text-purple-100">{evaluation.suggestions}</p>
                    </div>
                  )}
                  {/* 教师留言箱（仅显示教师评估的留言） */}
                  {evaluation.evaluation_type === 'teacher' && evaluation.teacher_feedback_box && (
                    <div className="bg-blue-500/30 dark:bg-blue-900/40 rounded-lg p-4 border border-blue-300 dark:border-blue-800/50">
                      <h4 className="text-gold dark:text-blue-200 font-semibold mb-2 flex items-center gap-2">
                        <MessageSquare className="w-5 h-5" />
                        教师留言
                      </h4>
                      <p className="text-gold dark:text-blue-100">{evaluation.teacher_feedback_box}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

