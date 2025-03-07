// 验证码响应接口
export interface CaptchaResponse {
  captcha_id: string;
  captcha_image: string; // base64 编码的图片
}

// 验证码请求接口
export interface CaptchaRequest {
  captcha_id: string;
  captcha_code: string;
} 