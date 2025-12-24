import { useState } from 'react'
import { Sparkles, Lightbulb } from 'lucide-react'

interface InspirationTip {
  type: 'plot' | 'scene' | 'technique'
  content: string
  emoji: string
}

const inspirationTips: InspirationTip[] = [
  { type: 'plot', content: '让反派突然帮助主角一次', emoji: '🔄' },
  { type: 'scene', content: '下一幕尝试设置在雨夜街头', emoji: '🌧️' },
  { type: 'technique', content: '试试用蒙太奇表现接下来的内容', emoji: '🎬' },
  { type: 'plot', content: '增加一个意外的转折点', emoji: '⚡' },
  { type: 'scene', content: '尝试在黎明时分的场景', emoji: '🌅' },
  { type: 'technique', content: '使用长镜头展现空间感', emoji: '📹' },
  { type: 'plot', content: '让配角说出关键信息', emoji: '💬' },
  { type: 'scene', content: '设置在一个废弃的工厂', emoji: '🏭' },
  { type: 'technique', content: '尝试手持摄影的晃动感', emoji: '📱' },
  { type: 'plot', content: '加入一个时间倒流的元素', emoji: '⏰' },
]

export default function InspirationDice() {
  const [isRolling, setIsRolling] = useState(false)
  const [currentTip, setCurrentTip] = useState<InspirationTip | null>(null)
  const [showTip, setShowTip] = useState(false)

  const rollDice = () => {
    if (isRolling) return
    
    setIsRolling(true)
    setShowTip(false)
    
    // 模拟掷骰子动画
    setTimeout(() => {
      const randomTip = inspirationTips[Math.floor(Math.random() * inspirationTips.length)]
      setCurrentTip(randomTip)
      setIsRolling(false)
      setShowTip(true)
    }, 1500)
  }

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <button
        onClick={rollDice}
        disabled={isRolling}
        className="relative w-16 h-16 bg-gradient-creative dark:bg-gradient-to-br dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 rounded-full shadow-lg hover:shadow-xl transition-all card-hover flex items-center justify-center group z-50"
        aria-label="灵感骰子"
      >
        {isRolling ? (
          <Sparkles className="w-8 h-8 text-gold dark:text-white animate-spin" />
        ) : (
          <Lightbulb className="w-8 h-8 text-gold dark:text-white group-hover:scale-110 transition-transform" />
        )}
        {!isRolling && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent-500 rounded-full animate-pulse"></span>
        )}
      </button>

      {showTip && currentTip && (
        <div className="absolute bottom-20 right-0 w-64 glass rounded-lg p-4 shadow-xl animate-scale-in border-l-4 border-accent-500">
          <div className="flex items-start gap-3">
            <div className="text-3xl">{currentTip.emoji}</div>
            <div className="flex-1">
              <div className="text-xs text-slate-600 dark:text-slate-400 mb-1 uppercase">
                {currentTip.type === 'plot' ? '剧情建议' : currentTip.type === 'scene' ? '场景建议' : '拍摄技巧'}
              </div>
              <p className="text-slate-800 dark:text-white font-medium">{currentTip.content}</p>
            </div>
            <button
              onClick={() => setShowTip(false)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

