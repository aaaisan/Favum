"""遗留依赖模块（兼容性导出）

此模块为了保持向后兼容性而保留。
新代码应直接从 dependencies 包中导入相应的依赖函数。
"""

# 重新导出主要的依赖函数，保持向后兼容性
from .dependencies.auth import get_current_user, require_user, require_active_user
from .dependencies.permission import require_admin, require_moderator, check_post_ownership
from .dependencies.resources import get_post_or_404, get_section_or_404, validate_post_access

# 为了文档和类型检查，添加一些类型别名
from fastapi import Request, Depends, HTTPException
from .core.auth import decode_token
from .db.database import get_db
from .db.models import User
from sqlalchemy.orm import Session
from typing import Optional

__all__ = [
    'get_current_user',
    'require_user',
    'require_active_user',
    'require_admin',
    'require_moderator',
    'check_post_ownership',
    'get_post_or_404',
    'get_section_or_404',
    'validate_post_access'
]

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