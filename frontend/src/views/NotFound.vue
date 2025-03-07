<template>
  <div class="not-found-page">
    <div class="container">
      <div class="error-content">
        <div class="error-code">404</div>
        <h1 class="error-title">页面未找到</h1>
        <p class="error-message">
          抱歉，您访问的页面不存在或已被移除。
        </p>
        <div class="error-actions">
          <router-link to="/" class="primary-btn">
            返回首页
          </router-link>
          <button class="secondary-btn" @click="goBack">
            返回上一页
          </button>
        </div>
        
        <div class="suggestions">
          <h2 class="suggestions-title">您可能在寻找：</h2>
          <div class="suggestions-grid">
            <router-link to="/" class="suggestion-card">
              <div class="suggestion-icon">🏠</div>
              <div class="suggestion-text">首页</div>
            </router-link>
            <router-link to="/categories" class="suggestion-card">
              <div class="suggestion-icon">📚</div>
              <div class="suggestion-text">话题分类</div>
            </router-link>
            <router-link to="/login" class="suggestion-card">
              <div class="suggestion-icon">🔑</div>
              <div class="suggestion-text">登录/注册</div>
            </router-link>
            <router-link to="/posts/new" class="suggestion-card">
              <div class="suggestion-icon">✏️</div>
              <div class="suggestion-text">发布新帖</div>
            </router-link>
          </div>
        </div>
      </div>
      
      <div class="illustration">
        <div class="search-character">
          🔍
        </div>
        <div class="terrain"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// 返回上一页
const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
  background-color: #f8fafc;
  position: relative;
  overflow: hidden;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
  position: relative;
  z-index: 2;
}

.error-content {
  max-width: 550px;
}

.error-code {
  font-size: 8rem;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 1.5rem;
  letter-spacing: -0.05em;
}

.error-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 1.5rem;
}

.error-message {
  font-size: 1.25rem;
  color: #64748b;
  margin: 0 0 2.5rem;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 3rem;
}

.primary-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
}

.primary-btn:hover {
  background-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 6px 10px rgba(59, 130, 246, 0.3);
}

.primary-btn:active {
  transform: translateY(0);
}

.secondary-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  background-color: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.suggestions-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #334155;
  margin: 0 0 1.5rem;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.suggestion-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem 1rem;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.suggestion-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
  border-color: #cbd5e1;
}

.suggestion-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.suggestion-text {
  color: #334155;
  font-weight: 500;
}

.illustration {
  position: relative;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-character {
  font-size: 8rem;
  animation: float 3s ease-in-out infinite;
  position: relative;
  z-index: 2;
}

.terrain {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100px;
  background-color: #dbeafe;
  border-radius: 50%;
  transform: scaleX(1.5);
  opacity: 0.7;
}

@keyframes float {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
  100% {
    transform: translateY(0px);
  }
}

/* Responsive design */
@media (max-width: 1024px) {
  .container {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .error-content {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .error-actions {
    justify-content: center;
  }
  
  .illustration {
    height: 300px;
    order: -1;
  }
}

@media (max-width: 640px) {
  .error-code {
    font-size: 6rem;
  }
  
  .error-title {
    font-size: 1.75rem;
  }
  
  .error-message {
    font-size: 1rem;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .primary-btn, .secondary-btn {
    width: 100%;
    text-align: center;
  }
  
  .illustration {
    height: 200px;
  }
  
  .search-character {
    font-size: 5rem;
  }
}
</style>
