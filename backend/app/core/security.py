from datetime import datetime, timedelta
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt # type: ignore
from passlib.context import CryptContext # type: ignore
from sqlalchemy.orm import Session

from .config import settings
from ..db.database import get_db
from ..crud import user as user_crud
from ..schemas import auth as auth_schema

"""
安全相关功能模块
提供密码加密、JWT令牌生成和验证、用户认证等功能
"""

# 密码加密上下文
# 使用bcrypt算法进行密码哈希,自动处理salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2认证方案
# 配置token获取URL为/api/v1/auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 已加密的密码哈希值
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    
    Args:
        password: 明文密码
        
    Returns:
        str: 使用bcrypt算法生成的密码哈希值
    """
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    """
    验证用户凭据
    
    检查用户名和密码是否匹配，用于用户登录认证。
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码
        
    Returns:
        Union[User, bool]: 如果验证成功则返回用户对象，否则返回False
    """
    user = user_crud.get_user_by_username(db, username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 可选的过期时间增量,如不指定则默认15分钟
        
    Returns:
        str: 生成的JWT令牌字符串
        
    Notes:
        - 使用settings中配置的SECRET_KEY和ALGORITHM进行签名
        - 令牌中会包含过期时间(exp)声明
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> auth_schema.TokenData:
    """
    获取当前认证用户
    
    Args:
        token: JWT访问令牌,通过OAuth2认证方案获取
        db: 数据库会话
        
    Returns:
        auth_schema.TokenData: 包含用户名的令牌数据对象
        
    Raises:
        HTTPException: 当令牌无效、过期或用户不存在时抛出401错误
        
    Notes:
        - 验证JWT令牌的签名和过期时间
        - 从令牌中提取用户名
        - 检查用户是否存在于数据库中
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = auth_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = user_crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return token_data

async def get_current_active_user(
    current_user: Annotated[auth_schema.TokenData, Depends(get_current_user)]
) -> auth_schema.TokenData:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前认证用户的令牌数据
        
    Returns:
        auth_schema.TokenData: 当前活跃用户的令牌数据
        
    Notes:
        - 作为FastAPI依赖项使用
        - 依赖于get_current_user
        - 可用于需要验证用户是否处于活跃状态的路由
    """
    return current_user