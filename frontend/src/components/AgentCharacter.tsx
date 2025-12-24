import { Sparkles, Music, Wand2, Camera, BookOpen, FileText } from 'lucide-react'

interface AgentCharacterProps {
  type: 'script' | 'audio' | 'editor' | 'camera' | 'tutor' | 'judge'
  message?: string
  isAnimating?: boolean
  className?: string
}

const typeStyles: Record<string, { badge: string; card: string; label: string }> = {
  script: {
    badge: "bg-gradient-to-r from-rose-400 to-pink-500 text-white",
    card: "border-pink-300/70 shadow-[0_0_25px_rgba(251,113,133,0.5)]",
    label: "文字星球守护者",
  },
  audio: {
    badge: "bg-gradient-to-r from-sky-400 to-orange-400 text-slate-900",
    card: "border-sky-300/70 shadow-[0_0_25px_rgba(56,189,248,0.5)]",
    label: "旋律星球的猫",
  },
  editor: {
    badge: "bg-gradient-to-r from-amber-300 to-rose-400 text-slate-900",
    card: "border-amber-300/70 shadow-[0_0_25px_rgba(251,191,36,0.5)]",
    label: "时间沙漏星球居民",
  },
  camera: {
    badge: "bg-gradient-to-r from-sky-500 to-indigo-500 text-white",
    card: "border-sky-400/70 shadow-[0_0_25px_rgba(59,130,246,0.5)]",
    label: "望远镜星球访客",
  },
  tutor: {
    badge: "bg-gradient-to-r from-orange-400 to-amber-400 text-slate-900",
    card: "border-orange-300/70 shadow-[0_0_25px_rgba(251,146,60,0.5)]",
    label: "狐狸导师",
  },
  judge: {
    badge: "bg-gradient-to-r from-indigo-400 to-violet-500 text-white",
    card: "border-indigo-300/70 shadow-[0_0_25px_rgba(129,140,248,0.5)]",
    label: "评审星球裁判",
  },
}

const agentConfig = {
  script: {
    icon: FileText,
    name: '剧本精灵',
    planetName: '文字星球守护者',
    color: 'text-rose-500',
    bgColor: 'bg-rose-500/10',
    borderColor: 'border-rose-500/40',
    emoji: '✨',
    style: typeStyles.script,
  },
  audio: {
    icon: Music,
    name: '混音小猫',
    planetName: '旋律星球的猫',
    color: 'text-blue-400',
    bgColor: 'bg-gradient-to-br from-blue-400/20 to-orange-500/20',
    borderColor: 'border-blue-400/40',
    emoji: '🎵',
    style: typeStyles.audio,
  },
  editor: {
    icon: Wand2,
    name: '剪辑魔法师',
    planetName: '时间沙漏星球居民',
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/40',
    emoji: '🎬',
    style: typeStyles.editor,
  },
  camera: {
    icon: Camera,
    name: '摄影机人',
    planetName: '望远镜星球访客',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/40',
    emoji: '📷',
    style: typeStyles.camera,
  },
  tutor: {
    icon: BookOpen,
    name: '导师狐',
    planetName: '狐狸导师',
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/40',
    emoji: '🦊',
    style: typeStyles.tutor,
  },
  judge: {
    icon: Sparkles,
    name: '评分判官',
    planetName: '评审星球裁判',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/40',
    emoji: '⚖️',
    style: typeStyles.judge,
  },
}

export default function AgentCharacter({ type, message, isAnimating = false, className = '' }: AgentCharacterProps) {
  const config = agentConfig[type]
  const Icon = config.icon

  return (
    <div className={`flex items-center gap-3 ${className} group`}>
      <div
        className={`relative w-12 h-12 ${config.bgColor} ${config.borderColor} border-2 rounded-full flex items-center justify-center transition-all duration-300 ${
          isAnimating ? 'animate-float' : ''
        } group-hover:scale-110`}
      >
        <Icon className={`w-6 h-6 ${config.color}`} />
        {/* 光环效果（judge专用） */}
        {type === 'judge' && (
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-yellow-400/60 blur-sm animate-pulse"></div>
        )}
        {/* hover时周围星星闪两下 */}
        <div className="absolute -inset-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute top-0 left-1/2 w-1 h-1 bg-yellow-400 rounded-full animate-twinkle" style={{ animationDelay: '0s' }}></div>
          <div className="absolute bottom-0 right-1/2 w-1 h-1 bg-yellow-300 rounded-full animate-twinkle" style={{ animationDelay: '0.3s' }}></div>
        </div>
        {isAnimating && (
          <div className="absolute inset-0 rounded-full border-2 border-current animate-ping opacity-75"></div>
        )}
      </div>
      {message && (
        <div className={`glass-card p-4 flex flex-col gap-3 ${config.style.card} animate-slide-up`}>
          <div className="flex items-center justify-between gap-2">
            <h3 className="card-title text-slate-800 dark:text-slate-50">
              {config.name}
            </h3>
            <span className={`text-xs px-2 py-1 rounded-full ${config.style.badge}`}>
              {config.style.label}
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-300">{message}</p>
        </div>
      )}
    </div>
  )
}

