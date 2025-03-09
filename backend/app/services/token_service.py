"""
令牌服务

提供JWT令牌验证和处理相关的服务层功能
"""

from typing import Optional, Dict, Any
from fastapi import Depends
from jose import JWTError, jwt

from ..core.config import settings
from ..db.repositories.user_repository import UserRepository
from ..db.models import User


class TokenService:
    """令牌验证和处理服务类"""
    
    def __init__(self, user_repository: UserRepository = None):
        """初始化令牌服务
        
        Args:
            user_repository: 用户数据访问仓储
        """
        self.user_repository = user_repository or UserRepository()
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            Optional[Dict[str, Any]]: 令牌的payload数据，如果令牌无效则返回None
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def get_user_from_token(self, token: str) -> Optional[User]:
        """从令牌中获取用户
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            Optional[User]: 用户对象，如果令牌无效或用户不存在则返回None
        """
        payload = await self.validate_token(token)
        if not payload:
            return None
            
        username = payload.get("sub")
        if not username:
            return None
            
        user = await self.user_repository.get_by_username(username)
        return user


def get_token_service() -> TokenService:
    """创建TokenService实例的依赖函数
    
    Returns:
        TokenService: 令牌服务实例
    """
    return TokenService() 