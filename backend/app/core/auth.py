from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
# from fastapi.security.utils import get_authorization_scheme_param

from .config import settings
from ..schemas import auth as auth_schema
from ..db.repositories.user_repository import UserRepository
from ..db.models import User
import logging

logger = logging.getLogger(__name__)

# OAuth2密码流认证方案，指定token获取URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  # 修改为正确的登录端点
    scheme_name="JWT"  # 明确指定为JWT认证方案
)

# 添加API密钥认证方案，使用Authorization头
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# 可选的OAuth2密码流，不自动抛出错误
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  # 修改为与上面相同的URL
    auto_error=False,
    scheme_name="JWT"  # 明确指定为JWT认证方案
)

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
    logger.debug(f"开始验证用户令牌: {token[:20] if token else None}...")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="令牌无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        logger.warning("未提供令牌，认证失败")
        raise credentials_exception
        
    try:
        logger.debug("开始解码令牌")
        
        # 先不验证令牌，只解码查看内容
        debug_payload = None
        try:
            debug_payload = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"令牌内容解码 (不验证签名): {debug_payload}")
        except Exception as e:
            logger.warning(f"令牌解码失败 (不验证签名): {str(e)}")
        
        # 正常解码并验证令牌
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未包含用户ID (sub)")
            raise credentials_exception
        logger.debug(f"令牌解码成功，用户名: {username}")
    except JWTError as e:
        logger.warning(f"令牌解码失败: {str(e)}")
        
        # 添加更多调试信息
        try:
            # 检查令牌格式
            parts = token.split('.')
            if len(parts) != 3:
                logger.error(f"令牌格式错误，应有3部分但有{len(parts)}部分")
            else:
                # 检查签名问题
                logger.info(f"令牌头部: {parts[0][:10]}...")
                logger.info(f"令牌载荷: {parts[1][:10]}...")
                logger.info(f"令牌签名: {parts[2][:10]}...")
                logger.info(f"使用的密钥: {settings.SECRET_KEY[:10]}...")
        except Exception as debug_e:
            logger.error(f"调试令牌过程中出错: {str(debug_e)}")
        
        raise credentials_exception
    
    try:
        logger.debug(f"查询用户信息: {username}")
        user_repository = UserRepository()
        user = await user_repository.get_by_username(username=username)
        if user is None:
            logger.warning(f"用户 {username} 不存在")
            raise credentials_exception
        
        logger.info(f"用户 {username} 认证成功")
        return user
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"获取用户信息时发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"服务器错误: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前活跃用户（验证用户是否被禁用）
    
    Args:
        current_user: 当前认证用户信息
        
    Returns:
        Dict[str, Any]: 当前活跃用户信息
        
    Raises:
        HTTPException: 用户被禁用时抛出401错误
    """
    user_id = current_user.get("id", "未知")
    username = current_user.get("username", "未知")
    logger.debug(f"检查用户 ID:{user_id} ({username}) 是否处于活跃状态")
    
    if not current_user.get("is_active", False):
        logger.warning(f"用户 ID:{user_id} ({username}) 已被禁用，拒绝访问")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号已被禁用"
        )
    
    logger.debug(f"用户 ID:{user_id} ({username}) 处于活跃状态，允许访问")
    return current_user

async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional)) -> Optional[User]:
    """获取当前用户（可选）
    
    与get_current_user不同，此函数在未提供token时返回None而不是抛出异常
    
    Args:
        token: JWT令牌，可选
        
    Returns:
        Optional[User]: 当前用户，未认证时为None
    """
    logger.debug(f"可选获取当前用户，令牌: {token[:10] if token else None}")
    
    if not token:
        logger.debug("未提供令牌，返回None")
        return None
    
    try:
        user = await get_current_user(token)
        user_id = user.get("id", "未知") if user else "未知"
        logger.debug(f"可选获取用户成功，用户ID: {user_id}")
        return user
    except HTTPException as e:
        logger.debug(f"认证失败 (可选): {e.detail}")
        return None
    except Exception as e:
        logger.error(f"可选获取用户时发生未预期的错误: {str(e)}", exc_info=True)
        return None

async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header)
) -> Optional[auth_schema.TokenData]:
    """
    从API密钥头部提取Bearer令牌并获取当前用户
    
    Args:
        api_key: Authorization头部值，应包含Bearer令牌
        
    Returns:
        Optional[auth_schema.TokenData]: 令牌数据或None
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
    
    # 从payload中提取用户信息
    username = payload.get("sub")
    if not username:
        return None
    
    # 创建令牌数据
    return auth_schema.TokenData(
        username=username,
        role=payload.get("role", "user"),
        permissions=payload.get("permissions", [])
    ) 