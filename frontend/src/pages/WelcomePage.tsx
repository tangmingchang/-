import { useState } from 'react'
import { Sun, Moon } from 'lucide-react'

interface WelcomePageProps {
  onStart: () => void
}

export default function WelcomePage({ onStart }: WelcomePageProps) {
  const [isDark, setIsDark] = useState(false)
  const [rippleKey, setRippleKey] = useState(0)

  const handleStart = () => {
    setRippleKey((k) => k + 1)
    onStart()
  }

  return (
    <div className="fixed inset-0 overflow-hidden">
      {/* 背景切换 */}
      <div
        className={`absolute inset-0 transition-opacity duration-700 ${isDark ? 'opacity-0' : 'opacity-100'}`}
        style={{
          backgroundImage: 'url(/旷野.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />
      <div
        className={`absolute inset-0 transition-opacity duration-700 ${isDark ? 'opacity-100' : 'opacity-0'}`}
        style={{
          backgroundImage: 'url(/星空.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />

      {/* 顶部文字 + 主题切换 */}
      <div className="relative z-10 flex flex-col items-center text-center px-6 md:px-10 py-6">
        <div className="text-white drop-shadow-lg">
          <div className="page-title bg-gradient-to-r from-amber-100 via-white to-sky-200 bg-clip-text text-transparent">
            影视制作智能体 · 小王子星球
          </div>
          <div className="mt-3 text-lg md:text-2xl">
            融合教育教学与影视创作实训，让创意在星空中闪光
          </div>
        </div>

        {/* 左上角主题切换 */}
        <button
          onClick={() => setIsDark((v) => !v)}
          className="absolute left-6 top-6 flex items-center gap-2 rounded-full bg-black/40 text-white px-3 py-2 backdrop-blur-md hover:bg-black/60 transition"
          aria-label="切换背景"
        >
          {isDark ? <Moon className="w-6 h-6" /> : <Sun className="w-6 h-6" />}
          <span className="text-sm">{isDark ? '夜间' : '白昼'}</span>
        </button>
      </div>

      {/* 中央：造梦按钮（星球光球） */}
      <div className="relative z-10 w-full h-full">
        <div
          className="absolute left-3/4 -translate-x-1/2 -translate-y-1/2"
          style={{ top: '45%' }}
        >
          <button
            onClick={handleStart}
            className="relative w-56 h-56 rounded-full text-white text-3xl font-bold flex items-center justify-center overflow-hidden shadow-2xl backdrop-blur-md border border-white/40 hover:scale-105 transition-transform"
            style={{
              background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.28), rgba(15,23,42,0.65))',
              boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
            }}
          >
            <span className="relative z-10">点击开始造梦</span>
            {/* 水波扩散效果 */}
            <span
              key={rippleKey}
              className="ripple-effect block"
            />
          </button>
          <div className="mt-4 text-center text-white/80 text-sm">
            轻轻一点，进入小王子的学习与创作宇宙
          </div>
        </div>
      </div>
    </div>
  )
}
