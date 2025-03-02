from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import uuid
from ...utils.captcha import CaptchaGenerator
from ...core.redis import redis_client
from ...core.config import settings

router = APIRouter()

@router.get("/generate")
async def generate_captcha():
    """生成验证码
    
    生成一个新的图片验证码。
    包含以下步骤：
    1. 生成随机验证码文本和对应的图片
    2. 生成唯一的验证码ID
    3. 将验证码存储到Redis并设置过期时间
    4. 返回验证码图片和ID
    
    此接口对所有用户开放。
    
    Returns:
        Response: 包含以下内容：
            - content: 验证码图片的二进制数据
            - media_type: "image/png"
            - headers: 包含验证码ID的头部信息
            
    Note:
        验证码将在settings.CAPTCHA_EXPIRE_MINUTES分钟后过期
    """
    # 生成验证码
    generator = CaptchaGenerator()
    text, image_bytes = generator.generate()
    
    # 生成唯一标识符
    captcha_id = str(uuid.uuid4())
    
    # 将验证码存储到Redis，设置过期时间（转换为秒）
    redis_client.setex(
        f"captcha:{captcha_id}",
        settings.CAPTCHA_EXPIRE_MINUTES * 60,
        text
    )
    
    # 返回验证码图片和ID
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"X-Captcha-ID": captcha_id}
    )

@router.post("/verify/{captcha_id}")
async def verify_captcha(captcha_id: str, code: str):
    """验证验证码
    
    验证用户输入的验证码是否正确。
    包含以下步骤：
    1. 从Redis获取存储的验证码
    2. 验证码验证后立即删除，防止重复使用
    3. 不区分大小写进行验证
    
    此接口对所有用户开放。
    
    Args:
        captcha_id: 验证码ID，从生成接口的响应头中获取
        code: 用户输入的验证码文本
        
    Returns:
        dict: 包含验证结果的信息
        
    Raises:
        HTTPException: 当验证码过期、不存在或错误时抛出400错误
        
    Note:
        验证成功后验证码将被删除，无法重复使用
    """
    # 从Redis获取验证码
    stored_code = redis_client.get(f"captcha:{captcha_id}")
    
    if not stored_code:
        raise HTTPException(status_code=400, detail="验证码已过期或不存在")
    
    # 验证后删除验证码
    redis_client.delete(f"captcha:{captcha_id}")
    
    # 不区分大小写验证
    if code.upper() != stored_code.upper():
        raise HTTPException(status_code=400, detail="验证码错误")
    
    return {"detail": "验证成功"} 