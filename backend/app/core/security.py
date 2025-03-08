from typing import Any, Dict, Optional, Union
from typing import Any, Dict, Optional, Union
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi import Depends, HTTPException, Security, status
from fastapi import Depends, HTTPException, Security, status
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt # type: ignore
from passlib.context import CryptContext # type: ignore
from typing import Annotated
from sqlalchemy.orm import Session
from types import SimpleNamespace

from ..core.config import settings
from ..schemas import auth as auth_schema
from ..db.database import get_db
from ..db.repositories.user_repository import UserRepository

"""
安全相关功能模块
提供密码加密、JWT令牌生成和验证、用户认证等功能
"""

# 密码加密上下文
# 使用bcrypt算法进行密码哈希,自动处理salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2认证方案
# 配置token获取URL为/token以兼容Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

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

async def authenticate_user(username: str, password: str) -> Union[Dict[str, Any], bool]:
    """
    验证用户凭据
    
    Args:
        username: 用户名
        password: 明文密码
        
    Returns:
        Union[Dict[str, Any], bool]: 如果验证成功则返回用户字典，否则返回False
    """
    user_repository = UserRepository()
    user = await user_repository.get_by_username(username=username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    
    # 创建一个类似于User对象的字典，以保持与现有代码的兼容性
    user_obj = SimpleNamespace()
    for key, value in user.items():
        setattr(user_obj, key, value)
    
    return user_obj

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
    
    # 调试信息
    print(f"[Security] 创建访问令牌, 原始数据: {to_encode}")
    
    # 确保token包含必要的字段
    if "sub" not in to_encode:
        print(f"[Security] 警告: token数据中缺少'sub'字段")
    if "role" not in to_encode:
        print(f"[Security] 警告: token数据中缺少'role'字段")
        # 添加默认角色
        to_encode["role"] = "user"
    if "id" not in to_encode and "sub" in to_encode:
        try:
            # 尝试从sub推断id
            to_encode["id"] = int(to_encode["sub"])
            print(f"[Security] 从sub推断的id: {to_encode['id']}")
        except:
            print(f"[Security] 无法从sub推断id: {to_encode['sub']}")
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    print(f"[Security] 令牌将在 {expire.isoformat()} 过期")
    
    # 编码JWT
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        print(f"[Security] JWT令牌创建成功, 长度: {len(encoded_jwt)}")
        # 验证令牌是否可以解码
        decoded = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"[Security] JWT令牌验证成功, 解码数据: {decoded}")
        return encoded_jwt
    except Exception as e:
        print(f"[Security] 创建JWT令牌时出错: {str(e)}")
        raise

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
        detail="凭证无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 打印获取到的token前20个字符和长度，便于调试
    token_length = len(token) if token else 0
    print(f"[Security] 收到token长度: {token_length}")
    if token_length > 0:
        print(f"[Security] 收到token前20个字符: {token[:20]}...")
    
    try:
        # 解码JWT令牌
        print(f"[Security] 尝试解码JWT，使用密钥: {settings.SECRET_KEY[:3]}...和算法: {settings.ALGORITHM}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"[Security] 解码JWT成功, payload: {payload}")
        
        # 提取用户标识
        username: str = payload.get("sub")
        if username is None:
            print("[Security] JWT中没有'sub'字段")
            raise credentials_exception
            
        # 获取用户角色
        role = payload.get("role", "user")
        print(f"[Security] 用户 {username} 的角色: {role}")
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp:
            now = datetime.utcnow().timestamp()
            print(f"[Security] 当前时间: {now}, 令牌过期时间: {exp}, 差值: {exp - now}秒")
            if now > exp:
                print(f"[Security] 令牌已过期: 当前时间 {now}, 过期时间 {exp}")
                raise credentials_exception
        
        # 创建令牌数据
        token_data = auth_schema.TokenData(
            username=username,
            role=role,
            permissions=payload.get("permissions", [])
        )
        print(f"[Security] 创建TokenData成功: {token_data}")
    except JWTError as e:
        print(f"[Security] JWT解码错误: {str(e)}")
        print(f"[Security] 失败的token: {token}")
        raise credentials_exception
    except Exception as e:
        print(f"[Security] 未知错误: {str(e)}")
        print(f"[Security] 失败的token: {token}")
        raise credentials_exception
    
    # 检查用户是否存在
    user_repository = UserRepository()
    user = await user_repository.get_by_username(username=token_data.username)
    if user is None:
        print(f"[Security] 用户不存在: {token_data.username}")
        raise credentials_exception
    
    print(f"[Security] 用户验证成功: {user['username']}")
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