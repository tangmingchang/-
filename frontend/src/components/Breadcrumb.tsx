import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  path: string
}

export default function Breadcrumb() {
  const location = useLocation()
  
  // 定义路径映射
  const pathMap: Record<string, string> = {
    '/': '首页',
    '/learning': '学习空间',
    '/creation': '创作空间',
    '/script-analysis': '剧本分析',
    '/video-generation': '视频生成',
    '/evaluation': '评估页',
    '/admin': '后台管理',
    '/chat': '智能对话',
    '/knowledge': '知识库',
    '/history': '对话历史',
    '/profile': '个人中心',
  }

  // 生成面包屑路径
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const paths = location.pathname.split('/').filter(Boolean)
    const breadcrumbs: BreadcrumbItem[] = [{ label: '首页', path: '/' }]

    let currentPath = ''
    paths.forEach((path) => {
      currentPath += `/${path}`
      const label = pathMap[currentPath] || path
      breadcrumbs.push({ label, path: currentPath })
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()

  // 如果只有一个首页，不显示面包屑
  if (breadcrumbs.length <= 1) return null

  return (
    <nav className="flex items-center gap-2 text-sm text-gold-700 dark:text-slate-400 mb-4">
      {breadcrumbs.map((item, index) => (
        <div key={item.path} className="flex items-center gap-2">
          {index === 0 ? (
            <Link
              to={item.path}
              className="flex items-center gap-1 hover:text-gold dark:hover:text-neon-blue transition-colors"
            >
              <Home className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          ) : (
            <>
              <ChevronRight className="w-4 h-4 text-gold-600 dark:text-slate-500" />
              {index === breadcrumbs.length - 1 ? (
                <span className="text-gold dark:text-white font-medium">{item.label}</span>
              ) : (
                <Link
                  to={item.path}
                  className="hover:text-gold dark:hover:text-neon-blue transition-colors"
                >
                  {item.label}
                </Link>
              )}
            </>
          )}
        </div>
      ))}
    </nav>
  )
}











