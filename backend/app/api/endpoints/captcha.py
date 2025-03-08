from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ...core.decorators import public_endpoint
from ...core.exceptions import BusinessException
from ...services.captcha_service import CaptchaService

router = APIRouter()

@router.get("/generate")
@public_endpoint(custom_message="生成验证码失败")
async def generate_captcha(request: Request):
    """生成验证码
    
    生成一个新的图片验证码。
    包含以下步骤：
    1. 生成随机验证码文本和对应的图片
    2. 生成唯一的验证码ID
    3. 将验证码存储到Redis并设置过期时间
    4. 返回验证码图片和ID
    
    此接口对所有用户开放，并有速率限制防止滥用。
    
    Returns:
        Response: 包含以下内容：
            - content: 验证码图片的二进制数据
            - media_type: "image/png"
            - headers: 包含验证码ID的头部信息
            
    Notes:
        - 验证码将在一定时间后过期
        - 每分钟最多可以请求30次验证码
    """
    try:
        captcha_service = CaptchaService()
        captcha_id, image_bytes = await captcha_service.generate_captcha()
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"X-Captcha-ID": captcha_id}
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.post("/verify/{captcha_id}")
@public_endpoint(custom_message="验证码验证失败")
async def verify_captcha(request: Request, captcha_id: str, code: str):
    """验证验证码
    
    验证用户输入的验证码是否正确。
    包含以下步骤：
    1. 从Redis获取存储的验证码
    2. 验证码验证后立即删除，防止重复使用
    3. 不区分大小写进行验证
    
    此接口对所有用户开放，并有速率限制防止暴力尝试。
    
    Args:
        captcha_id: 验证码ID，从生成接口的响应头中获取
        code: 用户输入的验证码文本
        
    Returns:
        dict: 包含验证结果的信息
        
    Raises:
        HTTPException: 当验证码过期、不存在或错误时抛出400错误
        
    Notes:
        - 验证成功后验证码将被删除，无法重复使用
        - 每分钟最多可以验证30次
    """
    try:
        captcha_service = CaptchaService()
        await captcha_service.verify_captcha(captcha_id, code)
        
        return {"message": "验证码正确"}
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        ) 