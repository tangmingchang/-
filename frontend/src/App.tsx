import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect, Suspense, lazy } from 'react'
import Layout from './components/Layout'
import WelcomePage from './pages/WelcomePage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'

// 代码拆分 - 按需加载
const LearningSpacePage = lazy(() => import('./pages/LearningSpacePage'))
const CreationSpacePage = lazy(() => import('./pages/CreationSpacePage'))
const ScriptAnalysisPage = lazy(() => import('./pages/ScriptAnalysisPage'))
const VideoGenerationPage = lazy(() => import('./pages/VideoGenerationPage'))
const EvaluationPage = lazy(() => import('./pages/EvaluationPage'))
const TeacherManagementPage = lazy(() => import('./pages/TeacherManagementPage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const ChatPage = lazy(() => import('./pages/ChatPage'))
const KnowledgePage = lazy(() => import('./pages/KnowledgePage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

// 加载中组件
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-gold dark:text-slate-400">加载中...</p>
    </div>
  </div>
)

function App() {
  const [showWelcome, setShowWelcome] = useState(true)
  const [hasVisited, setHasVisited] = useState(false)

  useEffect(() => {
    // 检查是否已经访问过（使用sessionStorage，关闭标签页后重新显示欢迎页）
    const visited = sessionStorage.getItem('hasVisited')
    if (visited) {
      setShowWelcome(false)
      setHasVisited(true)
    } else {
      // 首次访问，显示欢迎页
      setShowWelcome(true)
    }
  }, [])

  const handleWelcomeComplete = () => {
    sessionStorage.setItem('hasVisited', 'true')
    setShowWelcome(false)
    setHasVisited(true)
  }

  // 如果显示欢迎页，直接渲染欢迎页
  if (showWelcome && !hasVisited) {
    return <WelcomePage onStart={handleWelcomeComplete} />
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={
          <Layout>
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/learning" element={<LearningSpacePage />} />
                <Route path="/creation" element={<CreationSpacePage />} />
                <Route path="/script-analysis" element={<ScriptAnalysisPage />} />
                <Route path="/video-generation" element={<VideoGenerationPage />} />
                <Route path="/evaluation" element={<EvaluationPage />} />
                <Route path="/teacher-management" element={<TeacherManagementPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/knowledge" element={<KnowledgePage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Routes>
            </Suspense>
          </Layout>
        } />
      </Routes>
    </Router>
  )
}

export default App

