from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
# from fastapi.security.utils import get_authorization_scheme_param

from .config import settings
from ..schemas import auth as auth_schema
from ..db.repositories.user_repository import UserRepository
from ..db.models import User

# OAuth2密码流认证方案，指定token获取URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

# 可选的OAuth2密码流，不自动抛出错误
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析JWT令牌
    
    尝试解析JWT令牌并返回payload数据。
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        Optional[Dict[str, Any]]: 令牌的payload数据，如果令牌无效则返回None
        
    Note:
        - 使用settings中配置的密钥和算法验证令牌
        - 如果令牌无效或过期，返回None而不是抛出异常
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌
    
    根据提供的数据创建JWT访问令牌。
    
    Args:
        data: 要编码到令牌中的数据字典
        expires_delta: 可选的过期时间增量，如果不提供则使用默认值
        
    Returns:
        str: 编码后的JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """获取当前用户
    
    从JWT令牌中解析用户信息，并验证用户是否存在。
    
    Args:
        token: JWT令牌
        
    Returns:
        Dict[str, Any]: 当前用户信息
        
    Raises:
        HTTPException: 当令牌无效或用户不存在时抛出401错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_repository = UserRepository()
    user = await user_repository.get_by_username(username=username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前活跃用户（验证用户是否被禁用）
    
    Args:
        current_user: 当前认证用户信息
        
    Returns:
        Dict[str, Any]: 当前活跃用户信息
        
    Raises:
        HTTPException: 用户被禁用时抛出401错误
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号已被禁用"
        )
    return current_user

async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional)) -> Optional[User]:
    """获取当前用户（可选）
    
    与get_current_user不同，此函数在未提供token时返回None而不是抛出异常
    
    Args:
        token: JWT令牌，可选
        
    Returns:
        Optional[User]: 当前用户，未认证时为None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None 