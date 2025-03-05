<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="card-header">
          <h1 class="card-title">登录</h1>
          <p class="card-subtitle">欢迎回来，请登录您的账号</p>
        </div>
        
        <div class="card-body">
          <form class="auth-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label for="email">用户名</label>
              <input
                id="email"
                v-model="username"
                type="text"
                placeholder="请输入您的用户名"
                required
                autocomplete="username"
              />
              <div v-if="usernameError" class="error-text">{{ usernameError }}</div>
            </div>
            
            <div class="form-group">
              <div class="password-label">
                <label for="password">密码</label>
                <router-link to="/forgot-password" class="forgot-password">
                  忘记密码?
                </router-link>
              </div>
              <div class="password-input">
                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入您的密码"
                  required
                  autocomplete="current-password"
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <div v-if="passwordError" class="error-text">{{ passwordError }}</div>
            </div>
            
            <div class="form-group captcha-group">
              <label for="captcha">验证码</label>
              <div class="captcha-container">
                <input 
                  type="text" 
                  id="captcha" 
                  v-model="captchaCode" 
                  placeholder="请输入验证码"
                  required
                >
                <div class="captcha-image" @click="refreshCaptcha">
                  <img v-if="captchaImage" :src="captchaImage" alt="验证码" />
                  <div v-else class="captcha-placeholder">
                    <span>加载中...</span>
                  </div>
                </div>
              </div>
              <div v-if="captchaError" class="error-text">{{ captchaError }}</div>
            </div>
            
            <div class="form-options">
              <label class="checkbox-label">
                <input type="checkbox" id="rememberMe" name="rememberMe" v-model="rememberMe" />
                <span>记住我</span>
              </label>
            </div>
            
            <button type="submit" class="submit-btn" :disabled="isLoading">
              <span v-if="isLoading" class="loader"></span>
              <span v-else>登录</span>
            </button>
          </form>
          
          <div v-if="generalError" class="general-error">
            {{ generalError }}
          </div>
          
          <div class="divider">
            <span>或</span>
          </div>
          
          <div class="social-login">
            <button class="social-btn google">
              <span class="icon">G</span>
              <span>使用 Google 登录</span>
            </button>
            
            <button class="social-btn github">
              <span class="icon">GH</span>
              <span>使用 GitHub 登录</span>
            </button>
          </div>
        </div>
        
        <div class="card-footer">
          <p>还没有账号? <router-link to="/register" class="register-link">立即注册</router-link></p>
        </div>
      </div>
      
      <div class="brand-info">
        <div class="brand-logo">Forum</div>
        <h2 class="brand-title">加入我们的技术社区</h2>
        <p class="brand-description">
          连接开发者，分享知识，一起学习和成长。
        </p>
        <div class="testimonials">
          <div class="testimonial">
            <p class="quote">"这是我见过的最友好、最有帮助的技术社区！"</p>
            <div class="author">—— 张三，前端开发者</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import apiClient from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const captchaId = ref('')
const captchaCode = ref('')

// 错误信息
const usernameError = ref('')
const passwordError = ref('')
const captchaError = ref('')
const generalError = ref('')

// 加载状态
const isLoading = ref(false)

// 验证码图片URL
const captchaImage = ref('')

// 获取验证码
const getCaptcha = async () => {
  isLoading.value = true;
  captchaError.value = '';
  captchaId.value = '';
  captchaImage.value = '';
  
  console.log('开始获取验证码...');
  
  try {
    // 使用当前时间戳防止缓存
    const timestamp = new Date().getTime();
    console.log('尝试请求验证码，URL:', `/captcha/generate?t=${timestamp}`);
    
    const response = await apiClient.get(`/captcha/generate?t=${timestamp}`, {
      responseType: 'blob',
      timeout: 10000, // 10秒超时
      headers: {
        'Accept': 'image/png',
        'Cache-Control': 'no-cache'
      }
    });
    
    console.log('验证码请求成功，状态码:', response.status);
    
    // 检查并记录所有响应头
    console.log('验证码响应头:');
    Object.keys(response.headers).forEach(key => {
      console.log(`${key}: ${response.headers[key]}`);
    });
    
    // 尝试多种可能的响应头名称（浏览器可能将头名称转为小写）
    let id = response.headers['x-captcha-id'] || 
             response.headers['X-Captcha-ID'] || 
             response.headers['x-captcha-id'.toLowerCase()] ||
             response.headers['X-CAPTCHA-ID'];
    
    if (!id) {
      console.error('响应头中没有找到验证码ID');
      throw new Error('验证码ID获取失败');
    }
    
    console.log('成功获取验证码ID:', id);
    captchaId.value = id;
    
    // 将Blob转换为base64
    const reader = new FileReader();
    reader.onload = () => {
      const base64data = reader.result as string;
      captchaImage.value = base64data;
      console.log('验证码图片已设置，长度:', captchaImage.value.length);
    };
    reader.onerror = (error: any) => {
      console.error('读取验证码图片失败:', error);
      captchaError.value = '验证码图片加载失败';
    };
    reader.readAsDataURL(response.data);
  } catch (error: any) {
    console.error('获取验证码失败:', error);
    captchaError.value = error.message || '获取验证码失败，请重试';
    // 清空验证码ID和图片
    captchaId.value = '';
    captchaImage.value = '';
  } finally {
    isLoading.value = false;
  }
}

// 刷新验证码
const refreshCaptcha = async () => {
  console.log('手动刷新验证码');
  captchaCode.value = ''; // 清空输入框
  await getCaptcha();
}

// 登录处理
const handleLogin = async () => {
  // 重置错误信息
  usernameError.value = '';
  passwordError.value = '';
  captchaError.value = '';
  generalError.value = '';
  
  // 表单验证
  let isValid = true;
  
  if (!username.value) {
    usernameError.value = '请输入用户名';
    isValid = false;
  }
  
  if (!password.value) {
    passwordError.value = '请输入密码';
    isValid = false;
  }
  
  if (!captchaCode.value) {
    captchaError.value = '请输入验证码';
    isValid = false;
  }
  
  if (!captchaId.value) {
    captchaError.value = '验证码ID无效，请刷新验证码';
    await refreshCaptcha();
    isValid = false;
  }
  
  if (!isValid) return;
  
  // 设置加载状态
  isLoading.value = true;
  
  try {
    // 记录请求数据（不包含密码）
    console.log('[Login] 登录请求数据:', {
      username: username.value,
      captcha_id: captchaId.value,
      captcha_code: captchaCode.value,
      remember: rememberMe.value
    });
    
    // 使用authStore处理登录
    console.log('[Login] 使用authStore处理登录...');
    console.log('[Login] 传递参数: username:', username.value, ', captchaId:', captchaId.value, ', captchaCode:', captchaCode.value);
    const loginResult = await authStore.login(
      username.value, 
      password.value, 
      captchaId.value,  // 修正：这里应该传递验证码ID
      captchaCode.value // 修正：这里应该传递验证码值
    );
    
    console.log('[Login] 登录成功，结果:', loginResult);
    
    // 检查localStorage中的token
    const storedToken = localStorage.getItem('token');
    console.log('[Login] 登录成功后检查localStorage中的token:', storedToken ? '存在' : '不存在');
    if (storedToken) {
      console.log('[Login] localStorage中的token长度:', storedToken.length);
      console.log('[Login] localStorage中的token前20个字符:', storedToken.substring(0, 20));
    }
    
    // 检查authStore中的认证状态
    console.log('[Login] authStore.isAuthenticated:', authStore.isAuthenticated);
    console.log('[Login] authStore.token存在:', !!authStore.token);
    console.log('[Login] authStore.user存在:', !!authStore.user);
    
    // 强制刷新authStore状态
    authStore.init();
    console.log('[Login] 重新初始化后 authStore.isAuthenticated:', authStore.isAuthenticated);
    
    // 检查是否有返回路径
    let returnPath = '/';
    
    try {
      const savedPath = sessionStorage.getItem('returnPath');
      
      if (savedPath) {
        returnPath = savedPath;
        sessionStorage.removeItem('returnPath');
        console.log('[Login] 准备重定向到:', returnPath);
      }
    } catch (e) {
      console.error('[Login] 读取返回路径失败:', e);
    }
    
    // 重定向到目标页面
    console.log('[Login] 登录完成，重定向到:', returnPath);
    router.push(returnPath);
  } catch (error: any) {
    console.error('[Login] 登录失败:', error);
    
    // 刷新验证码 - 只在登录失败时刷新
    refreshCaptcha();
    
    // 特定处理验证码错误
    if (error.response?.status === 400) {
      const errorData = error.response.data;
      console.log('[Login] 收到400错误:', errorData);
      
      // 检查错误数据格式
      let errorMessage = '';
      
      if (errorData.error && errorData.error.message) {
        // 新的错误格式
        errorMessage = errorData.error.message;
      } else if (errorData.detail) {
        // 旧的错误格式
        errorMessage = errorData.detail;
      } else if (typeof errorData === 'string') {
        // 直接字符串错误
        errorMessage = errorData;
      } else {
        errorMessage = '请求参数错误';
      }
      
      console.log('[Login] 错误消息:', errorMessage);
      
      // 处理验证码相关错误
      if (errorMessage.includes('验证码')) {
        captchaError.value = errorMessage;
        console.log('[Login] 验证码错误:', errorMessage);
      } else if (errorMessage.includes('用户名') || errorMessage.includes('不存在')) {
        usernameError.value = errorMessage;
        console.log('[Login] 用户名错误:', errorMessage);
      } else if (errorMessage.includes('密码')) {
        passwordError.value = errorMessage;
        console.log('[Login] 密码错误:', errorMessage);
      } else {
        generalError.value = errorMessage;
        console.log('[Login] 一般错误:', errorMessage);
      }
    } else if (error.response?.status === 401) {
      passwordError.value = '用户名或密码错误';
      console.log('[Login] 认证错误 (401)');
    } else if (error.response?.status === 429) {
      generalError.value = '请求过于频繁，请稍后再试';
      console.log('[Login] 请求频率限制错误 (429)');
    } else {
      generalError.value = error.message || '登录失败，请稍后再试';
      console.log('[Login] 其他错误:', error.message);
    }
  } finally {
    isLoading.value = false;
  }
}

// 组件挂载时获取验证码
onMounted(() => {
  console.log('Login组件已挂载，获取首次验证码');
  
  // 测试localStorage
  try {
    console.log('[Login] 测试localStorage功能...');
    localStorage.setItem('test_key', 'test_value');
    const testValue = localStorage.getItem('test_key');
    console.log('[Login] localStorage测试结果:', testValue === 'test_value' ? '成功' : '失败');
    if (testValue !== 'test_value') {
      console.error('[Login] localStorage测试失败：存储的值无法正确读取');
    }
    localStorage.removeItem('test_key');
    const removedValue = localStorage.getItem('test_key');
    console.log('[Login] localStorage移除测试:', removedValue === null ? '成功' : '失败');
    
    // 检查当前localStorage中是否存在token
    const currentToken = localStorage.getItem('token');
    console.log('[Login] 当前localStorage中token状态:', currentToken ? '存在' : '不存在');
    if (currentToken) {
      console.log('[Login] 当前token长度:', currentToken.length);
    }
  } catch (e) {
    console.error('[Login] localStorage测试出错:', e);
  }
  
  refreshCaptcha();
  
  // 不再使用定时器自动刷新验证码
});
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  padding: 2rem 1rem;
}

.auth-container {
  width: 100%;
  max-width: 1200px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background-color: white;
}

.auth-card {
  padding: 3rem 2.5rem;
  display: flex;
  flex-direction: column;
}

.card-header {
  margin-bottom: 2.5rem;
}

.card-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 0.75rem;
}

.card-subtitle {
  color: #64748b;
  font-size: 1rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #334155;
  font-weight: 500;
  font-size: 0.95rem;
}

.password-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-password {
  color: #3b82f6;
  font-size: 0.85rem;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-password:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.form-group input {
  padding: 0.9rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  width: 100%;
  transition: all 0.2s;
}

.form-group input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.password-input {
  position: relative;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0;
}

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.form-options {
  display: flex;
  align-items: center;
  margin-top: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  color: #475569;
  font-size: 0.95rem;
}

.checkbox-label input {
  width: 1rem;
  height: 1rem;
}

.submit-btn {
  padding: 1rem;
  background-color: #3b82f6;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 3.25rem;
  margin-top: 1rem;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.loader {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.divider {
  display: flex;
  align-items: center;
  margin: 2rem 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.divider::before,
.divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background-color: #e2e8f0;
}

.divider span {
  margin: 0 1rem;
}

.social-login {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background-color: white;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.social-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.social-btn .icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.8rem;
}

.social-btn.google .icon {
  background-color: #db4437;
  color: white;
}

.social-btn.github .icon {
  background-color: #333;
  color: white;
}

.card-footer {
  margin-top: auto;
  padding-top: 2rem;
  text-align: center;
  color: #475569;
  font-size: 0.95rem;
}

.register-link {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.register-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.brand-info {
  background-color: #1e40af;
  background-image: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  color: white;
  padding: 4rem 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-logo {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 2rem;
  letter-spacing: -0.05em;
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1.5rem;
  line-height: 1.3;
}

.brand-description {
  font-size: 1.1rem;
  margin: 0 0 3rem;
  opacity: 0.9;
  line-height: 1.7;
}

.testimonials {
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  padding: 2rem;
  border-radius: 12px;
  margin-top: auto;
}

.quote {
  font-size: 1.1rem;
  font-style: italic;
  margin: 0 0 1rem;
  line-height: 1.6;
}

.author {
  font-size: 0.9rem;
  opacity: 0.8;
}

/* Responsive design */
@media (max-width: 1024px) {
  .auth-container {
    grid-template-columns: 1fr;
    max-width: 600px;
  }
  
  .brand-info {
    display: none;
  }
  
  .auth-card {
    padding: 2.5rem 2rem;
  }
}

@media (max-width: 640px) {
  .auth-card {
    padding: 2rem 1.5rem;
  }
  
  .card-title {
    font-size: 1.75rem;
  }
}

.general-error {
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin: 1rem 0;
  font-size: 0.9rem;
  text-align: center;
}

/* 验证码相关样式 */
.captcha-group {
  margin-bottom: 1rem;
}

.captcha-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.captcha-container input {
  flex: 1;
}

.captcha-image {
  width: 130px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  background-color: #f8fafc;
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.captcha-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  color: #64748b;
  font-size: 0.85rem;
}
</style> 