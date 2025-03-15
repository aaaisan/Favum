#!/usr/bin/env python3
"""
调试认证问题
"""

import os
import sys
import requests
import json
from datetime import datetime
import jwt

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 导入项目配置
from app.core.config import settings

# 认证配置
DEFAULT_HOST = "localhost:8000"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
CAPTCHA_ID = "test123"
CAPTCHA_CODE = "test123"

def get_token_from_api():
    """从API获取认证令牌"""
    host = DEFAULT_HOST
    login_url = f"http://{host}/api/v1/auth/login"
    
    # 构建登录请求数据
    login_data = {
        "username": DEFAULT_USERNAME,
        "password": DEFAULT_PASSWORD,
        "captcha_id": CAPTCHA_ID,
        "captcha_code": CAPTCHA_CODE
    }
    
    print(f"尝试从 {login_url} 获取令牌")
    print(f"请求数据: {json.dumps(login_data, indent=2)}")
    
    try:
        response = requests.post(
            login_url,
            json=login_data
        )
        
        print(f"收到响应: 状态码={response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据结构: {list(data.keys())}")
            
            # 从响应中提取令牌
            token = data.get("access_token")
            
            if token:
                print(f"成功获取令牌: {token[:20]}...")
                return token
            else:
                print(f"响应中未找到令牌: {json.dumps(data, indent=2)}")
                return None
        else:
            print(f"登录失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"获取令牌时出错: {str(e)}")
        return None

def decode_and_verify_token(token):
    """解码并验证JWT令牌"""
    print("\n验证令牌...")
    print(f"使用的SECRET_KEY: {settings.SECRET_KEY[:10]}...")
    print(f"使用的算法: {settings.ALGORITHM}")
    
    try:
        # 解码令牌而不验证签名
        decoded_payload = jwt.decode(token, options={"verify_signature": False})
        print(f"\n令牌内容 (未验证):")
        print(json.dumps(decoded_payload, indent=2))
        
        # 检查令牌各个字段
        print("\n令牌字段检查:")
        if "exp" in decoded_payload:
            exp_time = datetime.fromtimestamp(decoded_payload["exp"])
            print(f"过期时间: {exp_time.isoformat()}")
            print(f"是否已过期: {'是' if exp_time < datetime.now() else '否'}")
        else:
            print("警告: 令牌中没有过期时间 (exp) 字段")
            
        if "sub" in decoded_payload:
            print(f"用户标识 (sub): {decoded_payload['sub']}")
        else:
            print("警告: 令牌中没有用户标识 (sub) 字段")
            
        # 尝试使用配置的密钥验证令牌
        try:
            verified_payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            print("\n令牌验证成功!")
            print(f"验证后的载荷: {json.dumps(verified_payload, indent=2)}")
            return True
        except Exception as e:
            print(f"\n令牌验证失败: {str(e)}")
            return False
    except Exception as e:
        print(f"解码令牌失败: {str(e)}")
        return False

def test_api_with_token(token):
    """使用令牌测试API端点"""
    print("\n测试带认证的API端点...")
    endpoints = [
        "/api/v1/users/me",  # 获取当前用户信息
        "/api/v1/posts",      # 获取帖子列表
    ]
    
    host = DEFAULT_HOST
    
    for endpoint in endpoints:
        url = f"http://{host}{endpoint}"
        print(f"\n测试: GET {url}")
        
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("请求成功!")
                # 打印部分响应内容
                data = response.json()
                print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            else:
                print(f"请求失败: {response.text}")
        except Exception as e:
            print(f"请求出错: {str(e)}")

def main():
    """主函数"""
    print(f"系统信息:")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目配置信息:")
    print(f"SECRET_KEY: {settings.SECRET_KEY[:10]}...")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # 获取令牌
    token = get_token_from_api()
    
    if token:
        # 验证令牌
        is_valid = decode_and_verify_token(token)
        
        # 测试API
        test_api_with_token(token)
    else:
        print("无法获取令牌，无法继续测试")

if __name__ == "__main__":
    main() 