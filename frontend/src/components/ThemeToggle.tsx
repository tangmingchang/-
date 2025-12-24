import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // 检查系统偏好或本地存储
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark)
    setIsDark(shouldBeDark)
    
    if (shouldBeDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newIsDark = !isDark
    setIsDark(newIsDark)
    
    if (newIsDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  const [showSparkle, setShowSparkle] = useState(false)

  const handleToggle = () => {
    setShowSparkle(true)
    toggleTheme()
    setTimeout(() => setShowSparkle(false), 600)
  }

  return (
    <button
      onClick={handleToggle}
      className="relative p-2 rounded-lg bg-white/10 dark:bg-white/5 hover:bg-white/20 dark:hover:bg-white/10 transition-all duration-300 backdrop-blur-sm border border-white/20 dark:border-white/10 group"
      aria-label={isDark ? '切换到沙漠晨光模式' : '切换到星空创作模式'}
      title={isDark ? '沙漠晨光模式' : '星空创作模式'}
    >
      {/* 切换瞬间闪出一圈星光 */}
      {showSparkle && (
        <div className="absolute inset-0 rounded-lg pointer-events-none">
          <div className="absolute inset-0 rounded-lg border-2 border-yellow-400/60 animate-ping"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-yellow-400 rounded-full animate-twinkle"></div>
          <div className="absolute top-0 right-0 w-1 h-1 bg-yellow-300 rounded-full animate-twinkle" style={{ animationDelay: '0.2s' }}></div>
          <div className="absolute bottom-0 left-0 w-1 h-1 bg-yellow-300 rounded-full animate-twinkle" style={{ animationDelay: '0.4s' }}></div>
        </div>
      )}
      <div className="relative w-5 h-5">
        <Sun
          className={`absolute inset-0 w-5 h-5 text-accent-500 transition-all duration-300 ${
            isDark ? 'opacity-0 rotate-90 scale-0' : 'opacity-100 rotate-0 scale-100'
          }`}
        />
        <Moon
          className={`absolute inset-0 w-5 h-5 text-neon-blue transition-all duration-300 ${
            isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'
          }`}
        />
      </div>
    </button>
  )
}




