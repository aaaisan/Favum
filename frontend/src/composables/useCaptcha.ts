import { ref } from 'vue'
import apiClient from '../services/api'

export function useCaptcha() {
  const captchaId = ref('')
  const captchaImage = ref('')
  const isLoading = ref(false)
  const error = ref('')

  const getCaptcha = async () => {
    isLoading.value = true
    error.value = ''
    
    console.log('开始获取验证码...')
    console.log('当前验证码ID:', captchaId.value)
    
    try {
      console.log('发送验证码请求到:', `${apiClient.defaults.baseURL}/captcha/generate`)
      const response = await apiClient.get('/captcha/generate', {
        responseType: 'blob'
      })
      
      console.log('验证码请求成功，状态码:', response.status)
      
      // 检查响应头中是否包含验证码ID
      const id = response.headers['x-captcha-id']
      console.log('响应头中的验证码ID:', id)
      
      // 打印所有响应头，用于调试
      console.log('所有响应头:')
      Object.keys(response.headers).forEach(key => {
        console.log(`${key}: ${response.headers[key]}`)
      })
      
      if (!id) {
        console.error('响应头中没有验证码ID')
        throw new Error('验证码ID获取失败')
      }
      
      // 设置验证码ID
      captchaId.value = id
      console.log('验证码ID已设置:', captchaId.value)
      
      // 使用 Promise 包装 FileReader，确保它完成后再返回
      return new Promise<void>((resolve, reject) => {
        // 使用 FileReader 读取 Blob 数据
        const reader = new FileReader()
        reader.onloadend = () => {
          console.log('FileReader 加载完成')
          try {
            const base64data = reader.result as string
            // 移除 data:image/png;base64, 前缀
            captchaImage.value = base64data.split(',')[1]
            console.log('验证码图片已设置，长度:', captchaImage.value.length)
            resolve()
          } catch (err) {
            console.error('处理验证码图片失败:', err)
            reject(err)
          }
        }
        
        reader.onerror = (err) => {
          console.error('FileReader 错误:', err)
          reject(err)
        }
        
        console.log('开始读取 Blob 数据...')
        reader.readAsDataURL(response.data)
      })
    } catch (err: any) {
      console.error('获取验证码失败:', err)
      console.error('错误详情:', err.message)
      if (err.response) {
        console.error('响应状态:', err.response.status)
        console.error('响应数据:', err.response.data)
        console.error('响应头:', err.response.headers)
      }
      error.value = err.response?.data?.detail || '获取验证码失败'
      // 清空验证码ID和图片
      captchaId.value = ''
      captchaImage.value = ''
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    captchaId,
    captchaImage,
    isLoading,
    error,
    getCaptcha
  }
} 