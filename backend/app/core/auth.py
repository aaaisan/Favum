"""
认证模块

提供JWT令牌认证相关的功能，包括：
- 令牌生成和验证
- 用户认证
- API密钥认证
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
# from fastapi.security.utils import get_authorization_scheme_param

from .config import settings
# from ..schemas import auth as auth_schema
from ..db.repositories.user_repository import UserRepository
from ..db.models import User
from .exceptions import UserNotFoundError, UserNotActivatedError, AuthenticationError
import logging

logger = logging.getLogger(__name__)

# OAuth2密码流认证方案，指定token获取URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  # 修改为正确的登录端点
    scheme_name="JWT",  # 明确指定为JWT认证方案
    auto_error=False  # 不自动抛出错误
)

# 添加API密钥认证方案，使用Authorization头
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

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
    logger.debug(f"开始解析JWT令牌: {token[:10] if token else None}...")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug(f"令牌解析成功，包含用户ID: {payload.get('sub', '未知')}")
        return payload
    except JWTError as e:
        logger.warning(f"令牌解析失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"令牌解析过程中发生未预期的错误: {str(e)}", exc_info=True)
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
    logger.debug(f"开始创建访问令牌，用户ID: {data.get('sub', '未知')}")
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        logger.debug(f"令牌将在 {expire} 过期")
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.debug("访问令牌创建成功")
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建访问令牌失败: {str(e)}", exc_info=True)
        raise

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    """获取当前用户
    
    从JWT令牌中解析用户信息并返回用户对象。如果:
    1. 未提供token或token无效 -> 返回None
    2. 用户不存在 -> 抛出UserNotFoundError异常
    3. 用户存在但未激活 -> 抛出用户未激活异常
    4. 用户存在且激活 -> 返回用户对象
    
    Args:
        token: JWT令牌(可选)
        
    Returns:
        Optional[User]: 当前用户对象,未认证时返回None
        
    Raises:
        UserNotFoundError: 当用户不存在时抛出此异常
        HTTPException: 当用户未激活时抛出相应异常
    """
    logger.debug(f"开始验证用户令牌: {token[:20] if token else None}...")
    
    if token is None:
        logger.debug("未提供令牌，返回None")
        return None
        
    try:
        logger.debug("开始解码令牌")
        
        # 先不验证令牌，只解码查看内容
        debug_payload = None
        try:
            debug_payload = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"令牌内容解码 (不验证签名): {debug_payload}")
        except Exception as e:
            logger.warning(f"令牌解码失败 (不验证签名): {str(e)}")
            return None
        
        # 正常解码并验证令牌
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未包含用户ID (sub)")
            return None
        logger.debug(f"令牌解码成功，用户名: {username}")
    except JWTError as e:
        logger.warning(f"令牌解码失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"令牌解码过程中发生未预期的错误: {str(e)}", exc_info=True)
        return None
    
    try:
        logger.debug(f"查询用户信息: {username}")
        user_repository = UserRepository()
        user = await user_repository.get_by_username(username=username)
        if user is None:
            logger.warning(f"用户 {username} 不存在")
            raise UserNotFoundError(username)
            
        # 检查用户激活状态
        if not user.is_active:
            logger.warning(f"用户 {username} 未激活")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "请先激活您的账号", "code": "user_not_activated"}
            )
        
        logger.info(f"用户 {username} 认证成功")
        return user
    except UserNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}", exc_info=True)
        return None

async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header)
) -> Optional[User]:
    """从API密钥头部提取Bearer令牌并获取当前用户
    
    Args:
        api_key: Authorization头部值，应包含Bearer令牌
        
    Returns:
        Optional[User]: 用户对象或None
        
    Raises:
        UserNotFoundError: 当用户不存在时抛出此异常
        HTTPException: 当用户未激活时抛出相应异常
    """
    if not api_key:
        return None
        
    # 提取Bearer令牌
    try:
        scheme, token = api_key.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        # 如果没有空格分隔，假设整个值是令牌
        token = api_key
    
    # 解析令牌
    payload = decode_token(token)
    if not payload:
        return None
        
    # 获取用户信息
    try:
        username: str = payload.get("sub")
        if not username:
            return None
            
        user_repository = UserRepository()
        user = await user_repository.get_by_username(username=username)
        if not user:
            raise UserNotFoundError(username)
            
        # 检查用户激活状态
        if not user.is_active:
            logger.warning(f"用户 {username} 未激活")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "请先激活您的账号", "code": "user_not_activated"}
            )
            
        return user
    except UserNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从API密钥获取用户信息时发生错误: {str(e)}", exc_info=True)
        return None 

def require_active_user(user: Optional[User]) -> User:
    """要求用户存在且处于激活状态
    
    Args:
        user: 用户对象
        
    Returns:
        User: 用户对象
        
    Raises:
        AuthenticationError: 当用户不存在时抛出
        UserNotActivatedError: 当用户未激活时抛出
    """
    if not user:
        raise AuthenticationError(detail="需要认证")
    if not user.is_active:
        raise UserNotActivatedError()
    return user 