from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from typing import Annotated, Union
import logging

# 导入BusinessError
from ...core.exceptions import BusinessError

# 导入响应模型

from ..responses import (
    TokenResponse,
    TokenDataResponse,
    LoginCheckResponse,
    AuthErrorResponse,
    PasswordResetRequestResponse,
    PasswordResetResponse,
    EmailVerificationResponse,
    EmailVerificationRedirectResponse
)

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
from ...utils.captcha import CaptchaValidator
from ...schemas import auth as auth_schema
from ...services.user_service import UserService
from ...db.repositories.user_repository import UserRepository
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.get("/check-username/{username}", response_model=LoginCheckResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="检查用户名失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def check_username(request: Request, username: str):
    """检查用户名是否可用"""
    user_repository = UserRepository()
    
    if await user_repository.get_by_username(username):
        return {
            "exists": True,
            "message": "用户名已被使用"
        }
    
    return {
        "exists": False,
        "message": "用户名可用"
    }

@router.get("/check-email/{email}", response_model=LoginCheckResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="检查邮箱失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def check_email(request: Request, email: str):
    """检查邮箱是否可用"""
    user_repository = UserRepository()
    
    if await user_repository.get_by_email(email):
        return {
            "exists": True,
            "message": "邮箱已被使用"
        }
    
    return {
        "exists": False,
        "message": "邮箱可用"
    }

@router.post("/register", response_model=TokenResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="用户注册失败", include_details=True)
@rate_limit(limit=5, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def register(
    request: Request,
    user: auth_schema.UserRegister
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
        
    Returns:
        TokenResponse: 包含访问令牌和令牌类型的响应
        
    Raises:
        HTTPException: 当用户名或邮箱已被使用时抛出400错误
    """
    # 检查用户名是否已存在
    user_repository = UserRepository()
    if await user_repository.get_by_username(user.username):
        raise HTTPException(
            status_code=400,
            detail="用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    if await user_repository.get_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="邮箱已被使用"
        )
    
    # 验证验证码
    validator = CaptchaValidator()
    validator.validate_and_delete(user.captcha_id, user.captcha_code)
    
    # 创建新用户
    user_service = UserService()
    user_data = user.model_dump()
    db_user = await user_service.create_user(user_data)
    
    # 从角色获取权限
    role_name = db_user["role"] if isinstance(db_user, dict) else db_user.role
    if hasattr(role_name, 'value'):
        role_name = role_name.value
    
    role = getattr(Role, role_name.upper(), Role.USER)
    permissions = [p for p in get_role_permissions(role)]
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 增加更多用户信息到令牌
    user_id = db_user["id"] if isinstance(db_user, dict) else db_user.id
    username = db_user["username"] if isinstance(db_user, dict) else db_user.username
    
    token_data = {
        "sub": username,
        "id": user_id,
        "role": role_name,
        "permissions": permissions
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # 构建符合TokenResponse的返回结构
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/login", response_model=TokenResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="用户登录失败", include_details=True)
@rate_limit(limit=10, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def login(
    request: Request,
    form_data: auth_schema.Login
):
    """用户登录
    
    验证用户凭据并返回访问令牌。
    包含以下步骤：
    1. 验证验证码
    2. 验证用户名和密码
    3. 生成访问令牌
    
    Args:
        form_data: 登录表单数据，包含用户名、密码和验证码
        
    Returns:
        TokenResponse: 包含访问令牌和令牌类型的响应
        
    Raises:
        HTTPException: 当用户名或密码错误时抛出401错误
    """
    # 验证验证码
    validator = CaptchaValidator()
    validator.validate_and_delete(form_data.captcha_id, form_data.captcha_code)
    
    # 打印登录尝试的信息
    print(f"登录尝试: 用户名={form_data.username}, 验证码ID={form_data.captcha_id}")
    
    user = await authenticate_user(form_data.username, form_data.password)
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
    
    # 构建符合TokenResponse的返回结构
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """获取访问令牌
    
    OAuth2密码流端点，用于Swagger UI授权
    不需要验证码
    
    Args:
        form_data: OAuth2表单数据，包含用户名和密码
        
    Returns:
        TokenResponse: 包含访问令牌和令牌类型的响应
        
    Raises:
        HTTPException: 当用户名或密码错误时抛出401错误
    """
    print(f"OAuth2授权请求: 用户名={form_data.username}")
    
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
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
    
    print(f"OAuth2授权成功: user_id={user.id}, username={user.username}")
    
    # 构建符合TokenResponse的返回结构
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/test-token", response_model=TokenDataResponse)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def test_token(
    request: Request,
    current_user: Annotated[auth_schema.TokenData, Depends(get_current_active_user)]
):
    """测试令牌有效性"""
    # 构建符合TokenDataResponse的返回结构
    return {
        "username": current_user.sub,
        "user_id": current_user.id,
        "role": current_user.role,
        "permissions": current_user.permissions
    }

@router.post("/swagger-login", include_in_schema=False)
@handle_exceptions(SQLAlchemyError, status_code=500, message="API授权失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def swagger_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Swagger UI授权端点
    
    专用于Swagger UI的授权，跳过验证码验证
    仅用于API文档测试，不应在实际应用中使用
    """
    user = await authenticate_user(form_data.username, form_data.password)
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
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", response_model=PasswordResetRequestResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="请求密码重置失败", include_details=True)
@rate_limit(limit=5, window=300)  # 每5分钟限制5次请求
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def request_password_reset(
    request: Request,
    reset_request: auth_schema.PasswordResetRequest
):
    """
    请求密码重置
    
    发送一封包含重置链接的邮件到用户的注册邮箱
    """
    user_service = UserService()
    
    # 尝试发送重置邮件
    success = await user_service.request_password_reset(reset_request.email)
    
    # 无论用户是否存在都返回相同的响应，以防止邮箱探测
    return {
        "message": "如果该邮箱已注册，我们已发送密码重置邮件。请检查您的邮箱。",
        "success": success
    }

@router.post("/reset-password", response_model=PasswordResetResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="密码重置失败", include_details=True)
@rate_limit(limit=5, window=300)  # 每5分钟限制5次请求
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def reset_password(
    request: Request,
    reset_data: auth_schema.PasswordReset
):
    """
    重置密码
    
    使用重置令牌验证用户身份并设置新密码
    """
    user_service = UserService()
    
    try:
        # 验证令牌并重置密码
        success = await user_service.reset_password(
            reset_token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码重置失败"
            )
            
        return {
            "message": "密码已成功重置，请使用新密码登录"
        }
        
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post("/verify-email", response_model=EmailVerificationResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="邮箱验证失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def verify_email(
    request: Request,
    verification_data: auth_schema.EmailVerification
):
    """
    验证用户邮箱
    
    验证邮箱后，用户账号将被激活
    """
    user_service = UserService()
    
    try:
        # 验证邮箱
        success = await user_service.verify_email(
            email=verification_data.email,
            token=verification_data.token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱验证失败"
            )
            
        return {
            "message": "邮箱验证成功，您的账号已激活"
        }
        
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.get("/verify-email/{token}", response_model=EmailVerificationRedirectResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="邮箱验证失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def verify_email_get(
    request: Request,
    token: str,
    email: str
):
    """
    通过GET请求验证用户邮箱
    
    用于邮件中的验证链接跳转
    """
    user_service = UserService()
    
    try:
        # 验证邮箱
        success = await user_service.verify_email(
            email=email,
            token=token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱验证失败"
            )
            
        # 重定向到前端的验证成功页面
        frontend_url = settings.SITE_URL
        return {
            "message": "邮箱验证成功，您的账号已激活",
            "redirect": f"{frontend_url}/verification-success"
        }
        
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )