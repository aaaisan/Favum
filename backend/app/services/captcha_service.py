"""
验证码服务模块

提供验证码生成、验证和管理相关的业务逻辑。
主要功能：
- 生成图形验证码
- 验证用户输入的验证码
- 管理验证码过期和使用状态
"""

import uuid
from fastapi import HTTPException, status
from ..utils.captcha import CaptchaGenerator
from ..core.redis import redis_client
from ..core.config import settings
from ..core.exceptions import BusinessException
from ..core.logging import get_logger

logger = get_logger(__name__)

class CaptchaService:
    """
    验证码服务类
    
    封装所有与验证码相关的业务逻辑，包括：
    - 生成新的图形验证码
    - 验证用户提交的验证码
    - 管理验证码的存储和过期
    
    Attributes:
        generator: 验证码生成器实例
    """
    
    def __init__(self):
        """初始化验证码服务"""
        self.generator = CaptchaGenerator()
        self.logger = logger
    
    async def generate_captcha(self) -> tuple[str, bytes]:
        """
        生成新的验证码
        
        生成一个随机验证码文本和对应的图片，并存储在Redis中。
        
        Returns:
            tuple: (验证码ID, 验证码图片二进制数据)
            
        Raises:
            BusinessException: 当验证码生成失败时抛出
        """
        try:
            # 生成验证码
            text, image_bytes = self.generator.generate()
            
            # 生成唯一标识符
            captcha_id = str(uuid.uuid4())
            
            # 将验证码存储到Redis，设置过期时间（转换为秒）
            redis_client.setex(
                f"captcha:{captcha_id}",
                settings.CAPTCHA_EXPIRE_MINUTES * 60,
                text
            )
            
            self.logger.info(f"验证码生成成功: ID={captcha_id}")
            return captcha_id, image_bytes
            
        except Exception as e:
            self.logger.error(f"验证码生成失败: {str(e)}")
            raise BusinessException(
                error_code="CAPTCHA_GENERATION_FAILED",
                message="生成验证码失败",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def verify_captcha(self, captcha_id: str, code: str) -> bool:
        """
        验证用户输入的验证码
        
        Args:
            captcha_id: 验证码ID
            code: 用户输入的验证码文本
            
        Returns:
            bool: 验证结果，True表示验证成功
            
        Raises:
            BusinessException: 当验证码无效、过期或错误时抛出
        """
        try:
            # 从Redis获取验证码
            stored_code = redis_client.get(f"captcha:{captcha_id}")
            
            if not stored_code:
                self.logger.warning(f"验证码不存在或已过期: ID={captcha_id}")
                raise BusinessException(
                    error_code="CAPTCHA_EXPIRED",
                    message="验证码已过期或不存在",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # 验证后删除验证码
            redis_client.delete(f"captcha:{captcha_id}")
            
            # 不区分大小写验证
            if code.upper() != stored_code.upper():
                self.logger.warning(f"验证码错误: ID={captcha_id}, 输入={code}, 实际={stored_code}")
                raise BusinessException(
                    error_code="CAPTCHA_INVALID",
                    message="验证码错误",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            self.logger.info(f"验证码验证成功: ID={captcha_id}")
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            self.logger.error(f"验证码验证过程发生错误: {str(e)}")
            raise BusinessException(
                error_code="CAPTCHA_VERIFICATION_ERROR",
                message="验证码验证失败",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def validate_and_delete(self, captcha_id: str, captcha_code: str) -> None:
        """
        验证并删除验证码（同步方法，供现有代码兼容）
        
        Args:
            captcha_id: 验证码ID
            captcha_code: 用户输入的验证码
            
        Raises:
            HTTPException: 当验证码无效或过期时抛出
        """
        # 从Redis获取验证码
        stored_code = redis_client.get(f"captcha:{captcha_id}")
        if not stored_code:
            self.logger.warning(f"验证码不存在或已过期: ID={captcha_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期或不存在"
            )
        
        # 验证后删除验证码
        redis_client.delete(f"captcha:{captcha_id}")
        
        # 验证码不区分大小写
        if captcha_code.upper() != stored_code.upper():
            self.logger.warning(f"验证码错误: ID={captcha_id}, 输入={captcha_code}, 实际={stored_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
        
        self.logger.info(f"验证码验证成功: ID={captcha_id}") 