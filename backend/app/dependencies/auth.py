from fastapi import Request, Depends, HTTPException
from ..core.auth import decode_token
from ..db.models import User
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

async def require_user(current_user: Optional[User] = Depends(get_current_user)):
    """要求用户必须登录
    
    Args:
        current_user: 从get_current_user依赖获取的用户对象
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果用户未登录，则抛出401异常
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="未提供有效的认证凭据"
        )
    return current_user

async def require_active_user(current_user: User = Depends(require_user)):
    """要求用户账户处于活跃状态
    
    检查用户是否被禁用或暂停
    
    Args:
        current_user: 从require_user依赖获取的用户对象
        
    Returns:
        User: 当前活跃用户对象
        
    Raises:
        HTTPException: 如果用户账户被禁用或暂停，则抛出403异常
    """
    if current_user.is_banned:
        raise HTTPException(
            status_code=403,
            detail="账户已被禁用"
        )
    
    if getattr(current_user, "is_suspended", False) and getattr(current_user, "suspension_end_date", None):
        raise HTTPException(
            status_code=403,
            detail=f"账户已被暂停至 {current_user.suspension_end_date}"
        )
    
    return current_user 