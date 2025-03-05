import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 8080,
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
        configure: (proxy, options) => {
          // 确保代理传递授权头
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`[Vite Proxy] 代理请求: ${req.method} ${req.url}`);
            
            // 详细记录所有请求头
            console.log(`[Vite Proxy] 请求头列表:`, Object.keys(req.headers).join(', '));
            
            // 检查标准authorization头（常见的小写形式）
            if (req.headers.authorization) {
              console.log(`[Vite Proxy] 代理请求包含authorization头(小写)`);
              proxyReq.setHeader('Authorization', req.headers.authorization);
            } 
            // 检查大写Authorization头
            else if (req.headers.Authorization) {
              console.log(`[Vite Proxy] 代理请求包含Authorization头(大写)`);
              proxyReq.setHeader('Authorization', req.headers.Authorization);
            }
            else {
              console.log(`[Vite Proxy] 代理请求不包含认证头`);
            }
            
            // 添加X-Requested-With头以标识AJAX请求
            proxyReq.setHeader('X-Requested-With', 'XMLHttpRequest');
            
            // 添加自定义头，方便调试
            proxyReq.setHeader('X-Proxy-Debug', 'vite-proxy');
          });
          
          // 记录代理响应
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log(`[Vite Proxy] 收到后端响应: ${req.method} ${req.url}, 状态码: ${proxyRes.statusCode}`);
            
            // 检查是否有认证相关错误
            if (proxyRes.statusCode === 401) {
              console.error(`[Vite Proxy] 收到401未授权响应，请求可能缺少有效的认证信息`);
            }
          });
        }
      }
    }
  }
})
