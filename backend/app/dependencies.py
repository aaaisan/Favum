from fastapi import Request, Depends, HTTPException
from .core.auth import decode_token
from .db.database import get_db
from .db.models import User
from sqlalchemy.orm import Session
from typing import Optional

async def get_current_user(request: Request) -> Optional[User]:
    """获取当前用户
    
    从请求头中获取令牌，解析出用户信息，并从数据库获取用户对象
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Optional[User]: 当前用户对象，如果未登录则返回None
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
        
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        return None
        
    payload = decode_token(token)
    if not payload:
        return None
        
    user_id = payload.get("sub")
    if not user_id:
        return None
        
    db = request.state.db
    user = db.query(User).filter(User.id == user_id).first()
    return user 