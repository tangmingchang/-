import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // 开发环境：始终代理到本地后端，避免CORS问题
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const authHeader = req.headers['authorization'] || req.headers['Authorization'];
            if (authHeader) {
              proxyReq.setHeader('Authorization', authHeader);
            }
          });
        },
      },
      '/media': {
        // 代理媒体文件（头像、图片等）到本地后端
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/books': {
        // 代理书籍文件到本地后端
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/knowledge': {
        // 代理知识库文件到本地后端
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

