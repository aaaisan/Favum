from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from typing import Annotated
import logging

from ...core.permissions import get_role_permissions, Role
from ...core.security import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time
from ...core.config import settings
from ...db.database import get_db
from ...db.models import User
from ...crud import user as user_crud
from ...utils.captcha import CaptchaValidator
from ...schemas import auth as auth_schema

router = APIRouter()

@router.get("/check-username/{username}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="检查用户名失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def check_username(request: Request, username: str, db: Session = Depends(get_db)):
    """检查用户名是否可用"""
    if user_crud.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="用户名已被使用")
    return {"message": "用户名可用"}

@router.get("/check-email/{email}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="检查邮箱失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def check_email(request: Request, email: str, db: Session = Depends(get_db)):
    """检查邮箱是否可用"""
    if user_crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    return {"message": "邮箱可用"}

@router.post("/register", response_model=auth_schema.Token)
@handle_exceptions(SQLAlchemyError, status_code=500, message="用户注册失败", include_details=True)
@rate_limit(limit=5, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def register(
    request: Request,
    user: auth_schema.UserRegister,
    db: Session = Depends(get_db)
):
    """注册新用户
    
    创建新用户账户并返回访问令牌。
    包含以下步骤：
    1. 验证用户名和邮箱的唯一性
    2. 验证验证码
    3. 创建新用户记录
    4. 生成访问令牌
    
    Args:
        user: 用户注册信息
        db: 数据库会话实例
        
    Returns:
        Token: 包含访问令牌和令牌类型的响应
        
    Raises:
        HTTPException: 当用户名或邮箱已被使用时抛出400错误
    """
    # 检查用户名是否已存在
    if user_crud.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    if user_crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=400,
            detail="邮箱已被使用"
        )
    
    # 验证验证码
    validator = CaptchaValidator()
    validator.validate_and_delete(user.captcha_id, user.captcha_code)
    
    # 创建新用户
    db_user = user_crud.create_user(db, user)
    
    # 从角色获取权限
    role_name = db_user.role.value if hasattr(db_user.role, 'value') else 'user'
    role = getattr(Role, role_name.upper(), Role.USER)
    permissions = [p for p in get_role_permissions(role)]
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 增加更多用户信息到令牌
    token_data = {
        "sub": db_user.username,
        "id": db_user.id,
        "role": role_name,
        "permissions": permissions
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=auth_schema.Token)
@handle_exceptions(SQLAlchemyError, status_code=500, message="用户登录失败", include_details=True)
@rate_limit(limit=10, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def login(
    request: Request,
    form_data: auth_schema.Login,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 验证验证码
    validator = CaptchaValidator()
    validator.validate_and_delete(form_data.captcha_id, form_data.captcha_code)
    
    # 打印登录尝试的信息
    print(f"登录尝试: 用户名={form_data.username}, 验证码ID={form_data.captcha_id}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户角色和权限
    role_name = user.role.value if hasattr(user.role, 'value') else str(user.role)
    role = getattr(Role, role_name.upper(), Role.USER)
    permissions = [p for p in get_role_permissions(role)]
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "id": user.id, 
            "role": role_name,
            "permissions": permissions
        },
        expires_delta=access_token_expires
    )
    
    # 打印生成的令牌信息
    print(f"生成访问令牌: user_id={user.id}, username={user.username}, role={user.role}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/test-token", response_model=auth_schema.TokenData)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def test_token(
    request: Request,
    current_user: Annotated[auth_schema.TokenData, Depends(get_current_active_user)]
):
    """测试令牌有效性"""
    return current_user