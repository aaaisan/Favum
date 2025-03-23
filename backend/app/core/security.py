from typing import Any, Dict, Optional, Union
from typing import Any, Dict, Optional, Union
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
# from fastapi import Depends, HTTPException, Security, status
# from fastapi import Depends, HTTPException, Security, status
# from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt # type: ignore
from passlib.context import CryptContext # type: ignore
from typing import Annotated
from sqlalchemy.orm import Session
# from types import SimpleNamespace

from ..core.config import settings
# from ..schemas.inputs import auth as auth_schema
# from ..core.database import get_db
from ..db.repositories.user_repository import UserRepository
from ..db.models import User
"""
安全相关功能模块
提供密码加密、JWT令牌生成和验证、用户认证等功能
"""

# 密码加密上下文
# 使用bcrypt算法进行密码哈希,自动处理salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2认证方案
# 配置token获取URL为/token以兼容Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  # 修改为正确的登录URL
    scheme_name="JWT"  # 明确指定为JWT方案
)

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

async def authenticate_user(username: str, password: str) -> Union[Optional[User], bool]:
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
    print(user.username)
    print(user.role)
    print(type(user))
    print(user.hashed_password)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    # 直接返回用户字典
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