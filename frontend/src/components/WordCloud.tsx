import { useEffect, useRef, useState } from 'react'

interface WordCloudProps {
  words: Array<{ text: string; value: number }>
  width?: number
  height?: number
  colors?: string[]
}

interface WordPosition {
  text: string
  x: number
  y: number
  fontSize: number
  color: string
  value: number
}

export default function WordCloud({ words, width = 800, height = 400, colors }: WordCloudProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [wordPositions, setWordPositions] = useState<WordPosition[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || words.length === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 获取实际容器宽度
    const actualWidth = containerRef.current?.clientWidth || width
    const actualHeight = height

    // 设置画布大小（考虑设备像素比）
    const dpr = window.devicePixelRatio || 1
    canvas.width = actualWidth * dpr
    canvas.height = actualHeight * dpr
    canvas.style.width = `${actualWidth}px`
    canvas.style.height = `${actualHeight}px`
    ctx.scale(dpr, dpr)

    // 清空画布
    ctx.clearRect(0, 0, actualWidth, actualHeight)

    // 默认颜色方案
    const defaultColors = colors || [
      '#3b82f6', // blue
      '#8b5cf6', // purple
      '#ec4899', // pink
      '#f59e0b', // amber
      '#10b981', // emerald
      '#ef4444', // red
      '#06b6d4', // cyan
      '#f97316', // orange
    ]

    // 计算最大和最小权重
    const maxValue = Math.max(...words.map(w => w.value))
    const minValue = Math.min(...words.map(w => w.value))

    // 计算字体大小范围
    const wordCount = words.length
    const minFontSize = wordCount > 30 ? 14 : 18
    const maxFontSize = wordCount > 30 ? 50 : 64

    // 按权重排序，重要词汇优先放置
    const sortedWords = [...words].sort((a, b) => b.value - a.value)

    const placedWords: WordPosition[] = []
    // 使用更精确的矩形碰撞检测
    const placedRects: Array<{ x: number; y: number; width: number; height: number }> = []

    // 检查矩形是否与已放置的矩形重叠（增加边距）
    const hasCollision = (x: number, y: number, w: number, h: number, padding: number = 8): boolean => {
      for (const rect of placedRects) {
        // 检查两个矩形是否重叠（考虑边距）
        if (
          x - padding < rect.x + rect.width + padding &&
          x + w + padding > rect.x - padding &&
          y - padding < rect.y + rect.height + padding &&
          y + h + padding > rect.y - padding
        ) {
          return true
        }
      }
      return false
    }

    // 标记区域为已占用
    const markAreaOccupied = (x: number, y: number, w: number, h: number) => {
      placedRects.push({ x, y, width: w, height: h })
    }

    // 放置每个单词
    sortedWords.forEach((word, index) => {
      // 计算字体大小（基于权重）
      const fontSize = minFontSize + ((word.value - minValue) / (maxValue - minValue || 1)) * (maxFontSize - minFontSize)
      
      // 设置字体以测量文本
      ctx.font = `bold ${fontSize}px "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif`
      const textMetrics = ctx.measureText(word.text)
      const textWidth = textMetrics.width
      const textHeight = fontSize

      // 选择颜色
      const color = defaultColors[index % defaultColors.length]

      // 使用改进的螺旋布局算法
      let placed = false
      const centerX = actualWidth / 2
      const centerY = actualHeight / 2
      
      // 黄金角度分布，每个词有不同的起始角度
      const baseAngle = (index * 137.508) % 360
      let angle = (baseAngle * Math.PI) / 180
      let radius = 0
      const angleStep = 0.1 // 更小的角度步长，更密集搜索
      const radiusStep = 0.8 // 更小的半径步长

      // 尝试放置
      let attempts = 0
      const maxAttempts = 3000 // 增加尝试次数
      
      while (attempts < maxAttempts && !placed) {
        const x = centerX + Math.cos(angle) * radius - textWidth / 2
        const y = centerY + Math.sin(angle) * radius

        // 检查边界（增加边距）
        const margin = 5
        if (x >= margin && x + textWidth <= actualWidth - margin && 
            y >= textHeight + margin && y <= actualHeight - margin) {
          // 检查碰撞（使用更大的边距）
          if (!hasCollision(x, y - textHeight, textWidth, textHeight, 10)) {
            placedWords.push({
              text: word.text,
              x,
              y,
              fontSize,
              color,
              value: word.value
            })
            markAreaOccupied(x, y - textHeight, textWidth, textHeight)
            placed = true
          }
        }

        angle += angleStep
        if (angle > Math.PI * 2) {
          angle = 0
          radius += radiusStep
        }
        attempts++
      }

      // 如果还是没放置成功，使用随机位置（增加尝试次数）
      if (!placed) {
        const maxRetries = 200
        for (let retry = 0; retry < maxRetries; retry++) {
          // 使用更均匀的随机分布
          const x = Math.random() * (actualWidth - textWidth - 20) + 10
          const y = Math.random() * (actualHeight - textHeight - 20) + textHeight + 10
          
          if (!hasCollision(x, y - textHeight, textWidth, textHeight, 10)) {
            placedWords.push({
              text: word.text,
              x,
              y,
              fontSize,
              color,
              value: word.value
            })
            markAreaOccupied(x, y - textHeight, textWidth, textHeight)
            placed = true
            break
          }
        }
        
        // 如果随机位置也失败，尝试更宽松的碰撞检测
        if (!placed) {
          const maxRetriesLoose = 100
          for (let retry = 0; retry < maxRetriesLoose; retry++) {
            const x = Math.random() * (actualWidth - textWidth - 20) + 10
            const y = Math.random() * (actualHeight - textHeight - 20) + textHeight + 10
            
            // 使用更小的边距
            if (!hasCollision(x, y - textHeight, textWidth, textHeight, 3)) {
              placedWords.push({
                text: word.text,
                x,
                y,
                fontSize,
                color,
                value: word.value
              })
              markAreaOccupied(x, y - textHeight, textWidth, textHeight)
              placed = true
              break
            }
          }
        }
        
        // 最后手段：强制放置（允许轻微重叠）
        if (!placed) {
          const x = Math.random() * (actualWidth - textWidth - 20) + 10
          const y = Math.random() * (actualHeight - textHeight - 20) + textHeight + 10
          placedWords.push({
            text: word.text,
            x,
            y,
            fontSize,
            color,
            value: word.value
          })
          markAreaOccupied(x, y - textHeight, textWidth, textHeight)
        }
      }
    })

    // 绘制所有单词
    placedWords.forEach((word) => {
      ctx.font = `bold ${word.fontSize}px "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif`
      ctx.fillStyle = word.color
      
      // 添加透明度变化
      const opacity = 0.7 + (word.value / maxValue) * 0.3
      ctx.globalAlpha = opacity

      // 绘制文本阴影
      ctx.shadowColor = 'rgba(0, 0, 0, 0.15)'
      ctx.shadowBlur = 3
      ctx.shadowOffsetX = 1
      ctx.shadowOffsetY = 1

      ctx.fillText(word.text, word.x, word.y)
      
      ctx.globalAlpha = 1.0
      ctx.shadowColor = 'transparent'
      ctx.shadowBlur = 0
      ctx.shadowOffsetX = 0
      ctx.shadowOffsetY = 0
    })

    setWordPositions(placedWords)
    console.log(`词云图: 成功放置 ${placedWords.length} / ${words.length} 个词`)
  }, [words, width, height, colors])

  return (
    <div ref={containerRef} className="w-full flex items-center justify-center overflow-hidden rounded-lg">
      <canvas
        ref={canvasRef}
        className="max-w-full h-auto"
      />
    </div>
  )
}
