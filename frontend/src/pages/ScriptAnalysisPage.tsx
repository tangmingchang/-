import { useState, useEffect } from 'react'
import { Upload, FileText, Sparkles, Download, Loader2, Plus, X, Copy, Check } from 'lucide-react'
import { api } from '../utils/api'
import AgentCharacter from '../components/AgentCharacter'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

interface AnalysisResult {
  structure_analysis?: any
  character_analysis?: any
  dialogue_quality?: any
  narrative_flow?: any
  strengths?: string[]
  weaknesses?: string[]
  suggestions?: string[]
  analysis?: string
  // 后端返回的原始数据
  parsed_structure?: any
  statistics?: any
}

interface ScriptNode {
  id: string
  character: string
  location: string
  action: string
  emotion?: string
  time?: string
  additional_context?: string
  script_node?: string
  scene_title?: string
}

interface ScriptTags {
  characters: string[]
  locations: string[]
  actions: string[]
  emotions: string[]
  times: string[]
}

export default function ScriptAnalysisPage() {
  const [scriptContent, setScriptContent] = useState('')
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  
  // 节点生成相关状态
  const [mode, setMode] = useState<'full' | 'node'>('full') // full: 完整文本, node: 节点生成
  const [tags, setTags] = useState<ScriptTags | null>(null)
  const [nodes, setNodes] = useState<ScriptNode[]>([])
  const [currentNode, setCurrentNode] = useState<Partial<ScriptNode>>({
    character: '',
    location: '',
    action: '',
    emotion: '',
    time: '',
    additional_context: ''
  })
  const [isGenerating, setIsGenerating] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  useEffect(() => {
    loadTags()
  }, [])

  const loadTags = async () => {
    try {
      const res = await api.get('/api/script/tags')
      setTags(res.data)
    } catch (error: any) {
      console.error('加载标签失败:', error)
    }
  }

  const generateNode = async () => {
    if (!currentNode.character || !currentNode.location || !currentNode.action) {
      alert('请至少选择人物、地点和事件')
      return
    }

    setIsGenerating(true)
    try {
      const res = await api.post('/api/script/generate-node', currentNode)
      const newNode: ScriptNode = {
        id: Date.now().toString(),
        ...currentNode,
        ...res.data
      }
      setNodes([...nodes, newNode])
      setCurrentNode({
        character: '',
        location: '',
        action: '',
        emotion: '',
        time: '',
        additional_context: ''
      })
    } catch (error: any) {
      alert('生成节点失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsGenerating(false)
    }
  }

  const deleteNode = (id: string) => {
    setNodes(nodes.filter(n => n.id !== id))
  }

  const copyNode = (node: ScriptNode) => {
    if (node.script_node) {
      navigator.clipboard.writeText(node.script_node)
      setCopiedId(node.id)
      setTimeout(() => setCopiedId(null), 2000)
    }
  }

  const combineNodes = () => {
    const combined = nodes.map(n => n.script_node || '').join('\n\n')
    setScriptContent(combined)
    setMode('full')
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const content = event.target?.result as string
      setScriptContent(content)
    }
    reader.readAsText(file)
  }

  const analyzeScript = async () => {
    if (!scriptContent.trim()) {
      alert('请先输入或上传剧本内容')
      return
    }

    setIsAnalyzing(true)
    setAnalysisResult(null)
    try {
      const res = await api.post('/api/ai/analyze-script', {
        script_content: scriptContent
      })
      
      // 后端是同步返回结果的，直接使用
      if (res.data.success && res.data.result) {
        const result = res.data.result
        console.log('原始分析结果:', result) // 调试用
        
        // 适配后端返回的数据结构
        // 后端返回: { parsed_structure, deep_analysis: { structure: {description}, characters: {description}, dialogue: {description}, suggestions }, statistics }
        const deepAnalysis = result.deep_analysis || {}
        
        // 提取各个分析字段，支持多种格式
        const getStructureText = () => {
          if (deepAnalysis.structure) {
            if (typeof deepAnalysis.structure === 'string') {
              return deepAnalysis.structure
            } else if (typeof deepAnalysis.structure === 'object' && deepAnalysis.structure.description) {
              return deepAnalysis.structure.description
            }
          }
          // 如果没有结构分析，尝试从parsed_structure生成简单描述
          if (result.parsed_structure && Object.keys(result.parsed_structure).length > 0) {
            const scenes = result.parsed_structure.scenes || []
            const characters = result.parsed_structure.characters || []
            return `检测到 ${scenes.length} 个场景，${characters.length} 个角色。${scenes.length > 0 ? '建议按照标准剧本格式(如:INT./EXT. 场景名)来组织场景结构。' : ''}`
          }
          return null
        }
        
        const getCharacterText = () => {
          if (deepAnalysis.characters) {
            if (typeof deepAnalysis.characters === 'string') {
              return deepAnalysis.characters
            } else if (typeof deepAnalysis.characters === 'object' && deepAnalysis.characters.description) {
              return deepAnalysis.characters.description
            }
          }
          // 如果没有人物分析，尝试从parsed_structure生成简单描述
          if (result.parsed_structure && result.parsed_structure.characters) {
            const chars = result.parsed_structure.characters || []
            return chars.length > 0 
              ? `检测到 ${chars.length} 个角色：${chars.slice(0, 3).join('、')}${chars.length > 3 ? '等' : ''}。建议按照标准剧本格式，将角色名单独成行(通常全大写)，以便系统识别和分析。`
              : '未检测到明确的角色信息。建议按照标准剧本格式，将角色名单独成行(通常全大写)，以便系统识别和分析。'
          }
          return null
        }
        
        const getDialogueText = () => {
          if (deepAnalysis.dialogue) {
            if (typeof deepAnalysis.dialogue === 'string') {
              return deepAnalysis.dialogue
            } else if (typeof deepAnalysis.dialogue === 'object' && deepAnalysis.dialogue.description) {
              return deepAnalysis.dialogue.description
            }
          }
          // 如果没有对白分析，尝试从统计信息生成简单描述
          if (result.statistics) {
            const dialogueRatio = result.statistics.dialogue_ratio || 0
            return `对话占比约为${(dialogueRatio * 100).toFixed(1)}%，${dialogueRatio < 0.1 ? '对话比例较低。剧本可能更侧重于场景描述和动作说明，适合视觉叙事较强的作品。' : '对话比例适中。'}`
          }
          return null
        }
        
        const adaptedResult: AnalysisResult = {
          structure_analysis: getStructureText(),
          character_analysis: getCharacterText(),
          dialogue_quality: getDialogueText(),
          narrative_flow: deepAnalysis.narrative_flow,
          strengths: deepAnalysis.strengths || [],
          weaknesses: deepAnalysis.weaknesses || [],
          suggestions: deepAnalysis.suggestions || [],
          analysis: undefined, // 不再显示完整JSON
          // 保留原始数据以便调试
          parsed_structure: result.parsed_structure,
          statistics: result.statistics
        }
        
        console.log('原始结果:', result)
        console.log('deep_analysis:', deepAnalysis)
        console.log('适配后的分析结果:', adaptedResult) // 调试用
        setAnalysisResult(adaptedResult)
      } else if (res.data.task_id) {
        // 如果返回了task_id，说明是异步任务，需要轮询
        setTaskId(res.data.task_id)
      pollTaskStatus(res.data.task_id)
        return
      } else {
        console.error('未返回有效结果:', res.data)
        alert('分析失败: 未返回有效结果')
      }
    } catch (error: any) {
      console.error('分析失败:', error)
      alert('分析失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsAnalyzing(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    if (!taskId || taskId === 'undefined') {
      console.error('无效的task_id:', taskId)
      setIsAnalyzing(false)
      return
    }

    const maxAttempts = 60
    let attempts = 0

    const poll = async () => {
      try {
        const res = await api.get(`/api/ai/task/${taskId}`)
        const { status, result } = res.data

        if (status === 'completed') {
          setAnalysisResult(result)
          setIsAnalyzing(false)
        } else if (status === 'failed') {
          alert('分析失败: ' + (res.data.error || '未知错误'))
          setIsAnalyzing(false)
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 2000)
        } else {
          alert('分析超时，请稍后查看结果')
          setIsAnalyzing(false)
        }
      } catch (error: any) {
        console.error('查询任务状态失败:', error)
        // 如果是404或CORS错误，可能是后端路由问题
        if (error.response?.status === 404) {
          alert('任务查询失败: 后端路由不存在，请检查后端服务')
        } else if (error.code === 'ERR_NETWORK' || error.message?.includes('CORS')) {
          alert('网络错误: 请检查后端服务是否运行，以及CORS配置是否正确')
        }
        setIsAnalyzing(false)
      }
    }

    poll()
  }

  const exportReport = async () => {
    if (!analysisResult) return

    try {
      // 创建一个隐藏的div来渲染内容
      const reportDiv = document.createElement('div')
      reportDiv.style.position = 'absolute'
      reportDiv.style.left = '-9999px'
      reportDiv.style.width = '800px'
      reportDiv.style.padding = '40px'
      reportDiv.style.backgroundColor = 'white'
      reportDiv.style.color = 'black'
      reportDiv.style.fontFamily = 'Arial, "Microsoft YaHei", sans-serif'
      
      // 构建HTML内容
      let htmlContent = `
        <div style="font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6;">
          <h1 style="font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center;">剧本分析报告</h1>
          <hr style="border: 1px solid #ccc; margin-bottom: 30px;">
          
          <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px; margin-bottom: 15px;">一、剧本内容</h2>
          <div style="white-space: pre-wrap; font-size: 12px; margin-bottom: 30px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">${scriptContent}</div>
          
          <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px; margin-bottom: 15px;">二、分析结果</h2>
      `
      
      // 添加各个分析部分
      if (analysisResult.structure_analysis) {
        const structureText = typeof analysisResult.structure_analysis === 'string'
          ? analysisResult.structure_analysis
          : JSON.stringify(analysisResult.structure_analysis, null, 2)
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #2563eb;">1. 结构分析</h3>
          <div style="white-space: pre-wrap; font-size: 12px; margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; border-left: 4px solid #2563eb;">${structureText}</div>
        `
      }
      
      if (analysisResult.character_analysis) {
        const characterText = typeof analysisResult.character_analysis === 'string'
          ? analysisResult.character_analysis
          : JSON.stringify(analysisResult.character_analysis, null, 2)
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #3b82f6;">2. 人物分析</h3>
          <div style="white-space: pre-wrap; font-size: 12px; margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; border-left: 4px solid #3b82f6;">${characterText}</div>
        `
      }
      
      if (analysisResult.dialogue_quality) {
        const dialogueText = typeof analysisResult.dialogue_quality === 'string'
          ? analysisResult.dialogue_quality
          : JSON.stringify(analysisResult.dialogue_quality, null, 2)
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #10b981;">3. 对白质量</h3>
          <div style="white-space: pre-wrap; font-size: 12px; margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; border-left: 4px solid #10b981;">${dialogueText}</div>
        `
      }
      
      if (analysisResult.strengths && analysisResult.strengths.length > 0) {
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #059669;">4. 优点</h3>
          <ul style="font-size: 12px; margin-bottom: 20px; padding-left: 30px;">
            ${analysisResult.strengths.map((s: string) => `<li style="margin-bottom: 8px;">${s}</li>`).join('')}
          </ul>
        `
      }
      
      if (analysisResult.weaknesses && analysisResult.weaknesses.length > 0) {
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #dc2626;">5. 不足</h3>
          <ul style="font-size: 12px; margin-bottom: 20px; padding-left: 30px;">
            ${analysisResult.weaknesses.map((w: string) => `<li style="margin-bottom: 8px;">${w}</li>`).join('')}
          </ul>
        `
      }
      
      if (analysisResult.suggestions && analysisResult.suggestions.length > 0) {
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; color: #d97706;">6. 改进建议</h3>
          <ul style="font-size: 12px; margin-bottom: 20px; padding-left: 30px;">
            ${analysisResult.suggestions.map((s: string) => `<li style="margin-bottom: 8px;">${s}</li>`).join('')}
          </ul>
        `
      }
      
      if (analysisResult.analysis) {
        htmlContent += `
          <h3 style="font-size: 16px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">7. 完整分析</h3>
          <div style="white-space: pre-wrap; font-size: 12px; margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">${analysisResult.analysis}</div>
        `
      }
      
      htmlContent += '</div>'
      reportDiv.innerHTML = htmlContent
      document.body.appendChild(reportDiv)
      
      // 使用html2canvas转换为图片
      const canvas = await html2canvas(reportDiv, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      })
      
      // 从DOM中移除临时div
      document.body.removeChild(reportDiv)
      
      // 创建PDF
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      })
      
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = canvas.width
      const imgHeight = canvas.height
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)
      const imgScaledWidth = imgWidth * ratio
      const imgScaledHeight = imgHeight * ratio
      
      // 如果内容超过一页，需要分页
      const pageCount = Math.ceil(imgScaledHeight / pdfHeight)
      
      for (let i = 0; i < pageCount; i++) {
        if (i > 0) {
          pdf.addPage()
        }
        pdf.addImage(
          imgData,
          'PNG',
          0,
          -i * pdfHeight,
          imgScaledWidth,
          imgScaledHeight
        )
      }
      
      pdf.save('剧本分析报告.pdf')
    } catch (error) {
      console.error('生成PDF失败:', error)
      alert('生成PDF失败，请重试')
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-paper dark:bg-transparent p-8 transition-all duration-300 relative z-10">
      <div className="max-w-6xl mx-auto">
        {/* 顶部：文字星球标题 */}
        <div className="mb-8 animate-slide-up">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="page-title bg-gradient-to-r from-rose-400 via-amber-300 to-sky-400 bg-clip-text text-transparent">
                文字星球 · 剧本分析
              </h1>
              <p className="mt-2 text-lg text-slate-600 dark:text-slate-200">
                把剧本放到实验台上，交给智能体帮你拆解结构、角色与情绪。
              </p>
              <p className="mt-1 text-gold-700 dark:text-purple-200">
                使用 AI 智能分析剧本结构、人物、对白等要素。
              </p>
            </div>
            <div className="shrink-0">
              <AgentCharacter type="script" />
            </div>
          </div>
        </div>

        {/* 模式切换 */}
        <div className="mb-6 flex gap-4">
          <button
            onClick={() => setMode('full')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              mode === 'full'
                ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                : 'glass text-gold dark:text-slate-300 hover:bg-white/20 dark:hover:bg-white/10'
            }`}
          >
            完整文本输入
          </button>
          <button
            onClick={() => setMode('node')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              mode === 'node'
                ? 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white shadow-lg'
                : 'glass text-gold dark:text-slate-300 hover:bg-white/20 dark:hover:bg-white/10'
            }`}
          >
            节点式快捷生成
          </button>
        </div>

        {mode === 'node' ? (
          <section className="space-y-6">
            {/* 上半部分：节点星球控制台 + 当前节点预览 */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* 左：节点星球控制台（标签选择） */}
              <div className="xl:col-span-2 glass-card p-4 md:p-6 flex flex-col gap-5 relative overflow-hidden">
                <div className="absolute -right-16 -top-16 w-40 h-40 rounded-full bg-gradient-to-br from-rose-300/30 via-amber-200/40 to-sky-300/30 blur-3xl pointer-events-none" />
                <div className="flex items-center justify-between gap-3 relative">
                  <div>
                    <h2 className="section-title text-slate-800 dark:text-slate-50">
                      节点星球 · 片段控制台
                    </h2>
                    <p className="mt-1 text-sm md:text-base text-slate-600 dark:text-slate-300">
                      选择人物、地点和事件，节点星球会自动帮你生成一个小片段，
                      再把这些片段拼成完整的剧本。
                    </p>
                  </div>
                  <div className="hidden md:flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-rose-400 to-amber-300 text-white shadow-lg">
                    <Sparkles className="w-5 h-5" />
                  </div>
                </div>

                {tags ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
                    {/* 人物 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        人物（必选）
                      </label>
                      <select
                        value={currentNode.character || ''}
                        onChange={(e) =>
                          setCurrentNode({ ...currentNode, character: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                      >
                        <option value="">请选择人物</option>
                        {tags.characters.map((char, idx) => (
                          <option key={idx} value={char}>
                            {char}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 地点 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        地点（必选）
                      </label>
                      <select
                        value={currentNode.location || ''}
                        onChange={(e) =>
                          setCurrentNode({ ...currentNode, location: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                      >
                        <option value="">请选择地点</option>
                        {tags.locations.map((loc, idx) => (
                          <option key={idx} value={loc}>
                            {loc}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 事件/动作 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        事件 / 动作（必选）
                      </label>
                      <select
                        value={currentNode.action || ''}
                        onChange={(e) =>
                          setCurrentNode({ ...currentNode, action: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                      >
                        <option value="">请选择事件 / 动作</option>
                        {tags.actions.map((act, idx) => (
                          <option key={idx} value={act}>
                            {act}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 情绪 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        情绪（可选）
                      </label>
                      <select
                        value={currentNode.emotion || ''}
                        onChange={(e) =>
                          setCurrentNode({ ...currentNode, emotion: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                      >
                        <option value="">请选择情绪</option>
                        {tags.emotions.map((emo, idx) => (
                          <option key={idx} value={emo}>
                            {emo}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 时间 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60 md:col-span-2">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        时间（可选）
                      </label>
                      <select
                        value={currentNode.time || ''}
                        onChange={(e) =>
                          setCurrentNode({ ...currentNode, time: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                      >
                        <option value="">请选择时间</option>
                        {tags.times.map((t, idx) => (
                          <option key={idx} value={t}>
                            {t}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 额外上下文 */}
                    <div className="glass rounded-2xl p-3 border border-amber-200/60 dark:border-purple-900/60 md:col-span-2">
                      <label className="block text-xs font-semibold text-gold dark:text-purple-200 mb-1.5">
                        额外上下文（可选）
                      </label>
                      <textarea
                        value={currentNode.additional_context || ''}
                        onChange={(e) =>
                          setCurrentNode({
                            ...currentNode,
                            additional_context: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 bg-white/70 dark:bg-dark-card border border-paper-300 dark:border-dark-border rounded-lg text-sm text-gold dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-neon-blue"
                        rows={3}
                        placeholder="例如：这是他们第一次重逢 / 氛围偏安静 / 需要埋一个小伏笔..."
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-40 text-sm text-gold-700 dark:text-slate-300">
                    标签加载中或加载失败，请检查 /api/script/tags 接口
                  </div>
                )}

                {/* 控制按钮 */}
                <div className="flex flex-col md:flex-row gap-3 pt-1 relative">
                  <button
                    onClick={generateNode}
                    disabled={
                      isGenerating ||
                      !currentNode.character ||
                      !currentNode.location ||
                      !currentNode.action
                    }
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        节点生成中...
                      </>
                    ) : (
                      <>
                        <Plus className="w-5 h-5" />
                        生成一个新的节点片段
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setCurrentNode({
                        character: '',
                        location: '',
                        action: '',
                        emotion: '',
                        time: '',
                        additional_context: '',
                      })
                    }
                    className="md:w-40 px-4 py-3 glass rounded-lg text-sm text-gold dark:text-slate-200 hover:bg-white/30 dark:hover:bg-white/10 transition-all card-hover"
                  >
                    重置当前节点
                  </button>
                </div>
              </div>

              {/* 右：当前节点预览 */}
              <div className="glass-card p-4 md:p-6 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute -left-12 -bottom-16 w-36 h-36 rounded-full bg-gradient-to-tr from-sky-300/30 via-violet-300/30 to-rose-300/30 blur-3xl pointer-events-none" />
                <div className="relative">
                  <h3 className="card-title text-slate-800 dark:text-slate-50 mb-2">
                    当前节点 · 画面预览
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    {[
                      currentNode.time,
                      currentNode.location,
                      currentNode.character,
                      currentNode.action,
                    ]
                      .filter(Boolean)
                      .join(' · ') ||
                      '当你在左侧选择了人物、地点和事件后，这里会自动拼出一句"节点概览"，帮助你在脑海里先看到画面。'}
                  </p>

                  {currentNode.emotion && (
                    <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">
                      情绪走向：{currentNode.emotion}
                    </p>
                  )}
                  {currentNode.additional_context && (
                    <p className="mt-2 text-xs text-gold-700 dark:text-slate-200 line-clamp-4">
                      补充说明：{currentNode.additional_context}
                    </p>
                  )}
                </div>
                <p className="mt-4 text-[11px] text-gold-600 dark:text-slate-400 relative">
                  小提示：可以先用节点星球把一个场景拆成多个「微节点」，再用下方的「组合成完整剧本」一键合并。
                </p>
              </div>
            </div>

            {/* 下半部分：节点星带（已生成节点列表） */}
            <div className="glass-card p-4 md:p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="section-title text-slate-800 dark:text-slate-50">
                    节点星带 · 片段列表
                  </h2>
                  <p className="mt-1 text-sm text-gold-700 dark:text-slate-300">
                    已生成的节点会像一圈星带排在这里，你可以复制、删除，也可以一键拼成完整剧本。
                  </p>
                </div>
                {nodes.length > 0 && (
                  <button
                    onClick={combineNodes}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg card-hover text-sm"
                  >
                    <FileText className="w-4 h-4" />
                    组合成完整剧本
                  </button>
                )}
              </div>

              {nodes.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <FileText className="w-14 h-14 text-gold-600 dark:text-slate-500 mb-4 animate-float" />
                  <p className="text-gold-700 dark:text-slate-300 mb-1">
                    还没有任何节点片段
                  </p>
                  <p className="text-xs text-gold-600 dark:text-slate-500">
                    从上面的控制台选择标签并点击「生成一个新的节点片段」开始吧。
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
                  {nodes.map((node) => (
                    <div
                      key={node.id}
                      className="glass rounded-2xl p-3 md:p-4 card-hover border-l-4 border-primary-500/70 dark:border-neon-blue/70 relative overflow-hidden"
                    >
                      <div className="absolute -right-10 -top-10 w-24 h-24 rounded-full bg-gradient-to-br from-amber-200/40 via-rose-200/40 to-sky-200/40 blur-3xl pointer-events-none" />
                      <div className="flex items-start justify-between gap-3 relative">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm md:text-base font-semibold text-gold dark:text-white mb-1 line-clamp-1">
                            {node.scene_title || '未命名节点'}
                          </h3>
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {node.character && (
                              <span className="px-2 py-0.5 text-[11px] rounded-full bg-primary-100 dark:bg-purple-900/40 text-primary-700 dark:text-purple-200">
                                {node.character}
                              </span>
                            )}
                            {node.location && (
                              <span className="px-2 py-0.5 text-[11px] rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-200">
                                {node.location}
                              </span>
                            )}
                            {node.emotion && (
                              <span className="px-2 py-0.5 text-[11px] rounded-full bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-200">
                                情绪：{node.emotion}
                              </span>
                            )}
                            {node.time && (
                              <span className="px-2 py-0.5 text-[11px] rounded-full bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-200">
                                {node.time}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col gap-1 shrink-0">
                          <button
                            onClick={() => copyNode(node)}
                            className="p-2 glass rounded-lg hover:bg-white/20 dark:hover:bg-white/10 transition-all"
                            title="复制节点文本"
                          >
                            {copiedId === node.id ? (
                              <Check className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <Copy className="w-4 h-4 text-gold-600 dark:text-slate-300" />
                            )}
                          </button>
                          <button
                            onClick={() => deleteNode(node.id)}
                            className="p-2 glass rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-all"
                            title="删除节点"
                          >
                            <X className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>

                      {node.script_node && (
                        <pre className="mt-2 text-xs md:text-sm text-gold-700 dark:text-slate-200 whitespace-pre-wrap bg-white/40 dark:bg-black/25 rounded-xl p-3 max-h-40 overflow-auto">
                          {node.script_node}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        ) : (
          <>
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 左：大玻璃工作台 */}
            <div className="glass-card p-4 md:p-6 flex flex-col gap-4">
              <h2 className="section-title text-slate-800 dark:text-slate-50">
                剧本上传 · 实验台
              </h2>
              
              {/* 上传区 */}
              <div className="border-2 border-dashed border-amber-300/70 rounded-2xl p-6 text-center text-sm text-slate-500 dark:text-slate-300">
                <input
                  type="file"
                  accept=".txt,.md"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer"
                >
                  拖拽剧本文件到这里，或点击上传。
                </label>
              </div>

              {/* 剧本文本区域 */}
              <div className="flex-1 rounded-2xl bg-slate-50/80 dark:bg-slate-950/60 p-4 overflow-auto">
                <textarea
                  value={scriptContent}
                  onChange={(e) => setScriptContent(e.target.value)}
                  className="w-full h-full px-2 py-2 bg-transparent border-none text-slate-700 dark:text-slate-300 font-mono text-sm focus:outline-none resize-none"
                  placeholder="这里显示剧本文本、选中高亮、情绪色条等..."
                />
              </div>

              <button
                onClick={analyzeScript}
                disabled={isAnalyzing || !scriptContent.trim()}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed card-hover"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    开始分析
                  </>
                )}
              </button>
            </div>

            {/* 右：分析结果卡片堆叠 */}
            <div className="space-y-4">
              <h2 className="section-title text-slate-800 dark:text-slate-50 mb-4">分析结果</h2>
              {analysisResult && (
                <button
                  onClick={exportReport}
                  className="flex items-center gap-2 px-4 py-2 glass rounded-lg card-hover mb-4"
                >
                  <Download className="w-4 h-4 text-primary-600 dark:text-neon-blue" />
                  <span className="text-gold dark:text-purple-200 text-sm">导出报告</span>
                </button>
              )}

              {isAnalyzing ? (
              <div className="flex flex-col items-center justify-center h-96">
                <AgentCharacter type="script" message="我正在阅读你的剧本，马上给出分析哦！" isAnimating />
                <Loader2 className="w-16 h-16 text-primary-500 dark:text-neon-blue animate-spin mt-4" />
                {taskId && (
                  <p className="text-sm text-gold-700 dark:text-purple-200 mt-2">任务ID: {taskId}</p>
                )}
              </div>
            ) : analysisResult ? (
              <>
                {analysisResult.structure_analysis && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(0px)' }}
                  >
                    {/* 金色页角 */}
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">
                      结构分析
                    </h3>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative">
                      {typeof analysisResult.structure_analysis === 'string'
                        ? analysisResult.structure_analysis
                        : (analysisResult.structure_analysis.description || JSON.stringify(analysisResult.structure_analysis, null, 2))}
                    </p>
                  </div>
                )}

                {analysisResult.character_analysis && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(6px)' }}
                  >
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">
                      角色出场与关系
                    </h3>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative">
                      {typeof analysisResult.character_analysis === 'string'
                        ? analysisResult.character_analysis
                        : (analysisResult.character_analysis.description || JSON.stringify(analysisResult.character_analysis, null, 2))}
                    </p>
                  </div>
                )}

                {analysisResult.dialogue_quality && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(12px)' }}
                  >
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">
                      情绪曲线摘要
                    </h3>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative">
                      {typeof analysisResult.dialogue_quality === 'string'
                        ? analysisResult.dialogue_quality
                        : (analysisResult.dialogue_quality.description || JSON.stringify(analysisResult.dialogue_quality, null, 2))}
                    </p>
                  </div>
                )}

                {analysisResult.strengths && analysisResult.strengths.length > 0 && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(18px)' }}
                  >
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">优点</h3>
                    <ul className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative list-disc list-inside space-y-1">
                      {analysisResult.strengths.map((strength, idx) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysisResult.weaknesses && analysisResult.weaknesses.length > 0 && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(24px)' }}
                  >
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">不足</h3>
                    <ul className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative list-disc list-inside space-y-1">
                      {analysisResult.weaknesses.map((weakness, idx) => (
                        <li key={idx}>{weakness}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysisResult.suggestions && analysisResult.suggestions.length > 0 && (
                  <div
                    className="relative glass-card p-4 md:p-5 overflow-hidden"
                    style={{ transform: 'translateY(30px)' }}
                  >
                    <div className="absolute -top-3 -right-6 h-10 w-16 bg-gradient-to-br from-amber-300 to-rose-300 rotate-12" />
                    <h3 className="card-title text-slate-800 dark:text-slate-50 relative">改进建议</h3>
                    <ul className="mt-2 text-sm text-slate-500 dark:text-slate-300 relative list-disc list-inside space-y-1">
                      {analysisResult.suggestions.map((suggestion, idx) => (
                        <li key={idx}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-96 text-center">
                <AgentCharacter type="script" message="分析结果将显示在这里" />
                <FileText className="w-16 h-16 text-gold-600 dark:text-slate-500 mb-4 mt-4 animate-float" />
              </div>
              )}
            </div>
          </section>
          </>
        )}
      </div>
    </div>
  )
}
