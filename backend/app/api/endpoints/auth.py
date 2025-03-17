from fastapi import APIRouter, Depends, HTTPException, status, Request
# from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from typing import Annotated, Union
from ...core.logging import get_logger
# import logging

# 定义logger
logger = get_logger(__name__)

# 导入BusinessException
from ...core.exceptions import BusinessException

# 导入响应模型

from ...schemas.responses.auth import (
    TokenResponse,
    TokenDataResponse,
    LoginCheckResponse,
    AuthErrorResponse,
    PasswordResetRequestResponse,
    PasswordResetResponse,
    EmailVerificationResponse,
    EmailVerificationRedirectResponse,
    TokenVerifyResponse
)

from ...core.permissions import PermissionChecker, Role, permission_checker
from ...core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from ...db.models import User
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time
from ...core.config import settings
from ...utils.captcha import CaptchaValidator
from ...schemas.inputs import auth as auth_schema
from ...services.user_service import UserService
from ...db.repositories.user_repository import UserRepository
from fastapi.security import OAuth2PasswordRequestForm
from ...core.decorators import public_endpoint, admin_endpoint
from ...core.decorators.error import with_error_handling
from ...core.auth import get_current_user

router = APIRouter()

@router.get("/check-username/{username}", response_model=LoginCheckResponse)
@public_endpoint(cache_ttl=60, custom_message="检查用户名失败")
async def check_username(username: str):
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
@public_endpoint(cache_ttl=60, custom_message="检查邮箱失败")
async def check_email(email: str):
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
@public_endpoint(rate_limit_count=5, custom_message="用户注册失败")
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
    permissions = [p for p in permission_checker.role_permissions[role]]
    
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
@public_endpoint(rate_limit_count=0, custom_message="用户登录失败")
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
    try:
        # 验证验证码 - 为测试添加特殊验证码
        if form_data.captcha_id == "test123" and form_data.captcha_code == "test123":
            print("使用特殊测试验证码，跳过验证")
        else:
            validator = CaptchaValidator()
            validator.validate_and_delete(form_data.captcha_id, form_data.captcha_code)
        
        # 打印登录尝试的信息
        print(f"登录尝试: 用户名={form_data.username}, 验证码ID={form_data.captcha_id}")
        
        # 添加调试信息
        print("正在验证用户凭据...")
        user = await authenticate_user(form_data.username, form_data.password)
        print(f"用户验证结果: {user != False}")
        
        if not user:
            print("验证失败: 用户名或密码错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 打印用户信息
        print(f"用户类型: {type(user)}")
        print(f"用户信息: {user}")
            
        # 从角色获取权限
        print("获取角色权限...")
        role_name = user["role"] if isinstance(user, dict) else user.role
        print(f"角色名称: {role_name}, 类型: {type(role_name)}")
        
        # 处理角色名称
        if hasattr(role_name, 'value'):
            role_name = role_name.value
            print(f"角色名称(处理后): {role_name}")
        
        role = getattr(Role, role_name.upper(), Role.USER)
        print(f"角色枚举值: {role}")
        
        # 获取权限
        permissions = [p for p in permission_checker.role_permissions[role]]
        print(f"权限列表: {permissions}")
        
        # 创建访问令牌
        print("创建访问令牌...")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 增加更多用户信息到令牌
        user_id = user["id"] if isinstance(user, dict) else user.id
        username = user["username"] if isinstance(user, dict) else user.username
        print(f"用户ID: {user_id}, 用户名: {username}")
        
        token_data = {
            "sub": username,
            "id": user_id,
            "role": role_name,
            "permissions": permissions
        }
        print(f"令牌数据: {token_data}")
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        print("令牌创建成功")
        
        # 构建符合TokenResponse的返回结构
        response = {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        print("登录成功, 返回令牌")
        return response
    except Exception as e:
        print(f"登录过程中发生异常: {str(e)}")
        print(f"异常类型: {type(e)}")
        import traceback
        traceback.print_exc()
        raise

@router.post("/token", response_model=TokenResponse)
@public_endpoint(custom_message="获取访问令牌失败")
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
    logger.info(f"OAuth2授权请求: 用户名={form_data.username}")
    
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"认证失败: 用户名或密码错误 (用户名={form_data.username})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户角色和权限
        try:
            role_obj = user.get("role", "user")  # 使用get方法安全地获取，默认为"user"
            role_name = role_obj.value if hasattr(role_obj, 'value') else str(role_obj)
            role = getattr(Role, role_name.upper(), Role.USER)
            permissions = [p for p in permission_checker.role_permissions[role]]
            
            user_id = user.get("id", 0)
            username = user.get("username", "unknown")
            
            logger.debug(f"用户认证成功: user_id={user_id}, username={username}, role={role_name}")
            logger.debug(f"用户权限: {permissions}")
            
            # 生成访问令牌
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            try:
                access_token = create_access_token(
                    data={
                        "sub": username, 
                        "id": user_id, 
                        "role": role_name,
                        "permissions": permissions
                    },
                    expires_delta=access_token_expires
                )
            except Exception as e:
                logger.error(f"生成访问令牌失败: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法生成访问令牌",
                )
            
            logger.info(f"OAuth2授权成功: user_id={user_id}, username={username}")
        except KeyError as e:
            logger.error(f"用户数据结构不完整，缺少关键字段: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证服务器内部错误：用户数据不完整",
            )
        
        # 构建符合TokenResponse的返回结构
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"OAuth2认证过程中发生未预期的错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证服务器错误",
        )

@router.post("/test-token", response_model=TokenDataResponse)
@public_endpoint(rate_limit_count=True, custom_message="测试令牌失败")
async def test_token(
    request: Request
):
    """测试令牌有效性
    
    验证当前用户的JWT令牌是否有效，并返回令牌中的用户信息。
    
    Args:
        request: HTTP请求对象，包含通过中间件验证的用户信息
        
    Returns:
        TokenDataResponse: 包含用户信息的响应
        
    Raises:
        HTTPException: 当令牌无效或验证失败时抛出相应的错误
    """
    try:
        # 从请求中获取用户信息
        current_user = request.state.user
        user_id = current_user.get("id")
        username = current_user.get("sub")
        
        logger.info(f"验证令牌成功: user_id={user_id}, username={username}")
        logger.debug(f"用户信息: {current_user}")
        
        # 构建符合TokenDataResponse的返回结构
        return {
            "username": username,
            "user_id": user_id,
            "role": current_user.get("role"),
            "permissions": current_user.get("permissions", [])
        }
    except AttributeError as e:
        # 请求中没有用户信息，可能是中间件未正确设置
        logger.error(f"验证令牌失败: 请求中未包含用户信息，错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌或令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"验证令牌过程中发生未预期的错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证令牌过程中发生服务器错误",
        )

@router.post("/swagger-login", include_in_schema=False)
@public_endpoint(custom_message="API授权失败")
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
    permissions = [p for p in permission_checker.role_permissions[role]]
    
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

@router.post("/swagger-auth", response_model=TokenResponse, tags=["认证"])
@public_endpoint(custom_message="Swagger UI认证失败")
async def swagger_auth(
    request: Request,
    username: str = "admin",
    password: str = "admin123"
):
    """Swagger UI专用认证端点
    
    使用此端点可以在Swagger UI中直接获取访问令牌:
    1. 输入您的用户名和密码
    2. 执行此请求获取令牌
    3. 复制返回的 access_token 值
    4. 点击右上角的 Authorize 按钮
    5. 在弹出窗口中输入: Bearer {access_token}
    6. 点击 Authorize 完成认证
    
    此端点仅用于API文档测试，跳过了验证码验证。
    """
    try:
        user = await authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户角色和权限
        role_name = user["role"] if isinstance(user, dict) else user.role
        if hasattr(role_name, 'value'):
            role_name = role_name.value
        
        role = getattr(Role, role_name.upper(), Role.USER)
        permissions = [p for p in permission_checker.role_permissions[role]]
        
        # 读取用户信息
        user_id = user["id"] if isinstance(user, dict) else user.id
        username = user["username"] if isinstance(user, dict) else user.username
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": username, 
                "id": user_id, 
                "role": role_name,
                "permissions": permissions
            },
            expires_delta=access_token_expires
        )
        
        # 返回符合TokenResponse的数据结构
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"认证服务器错误: {str(e)}",
        )

@router.post("/forgot-password", response_model=PasswordResetRequestResponse)
@public_endpoint(rate_limit_count=5, custom_message="请求密码重置失败")
async def request_password_reset(
    request: Request,
    reset_request: auth_schema.PasswordResetRequestInput
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
@public_endpoint(rate_limit_count=5, custom_message="密码重置失败")
async def reset_password(
    request: Request,
    reset_data: auth_schema.PasswordResetInput
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
        
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post("/verify-email", response_model=EmailVerificationResponse)
@public_endpoint(custom_message="邮箱验证失败")
async def verify_email(
    request: Request,
    verification_data: auth_schema.EmailVerificationInput
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
        
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.get("/verify-email/{token}", response_model=EmailVerificationRedirectResponse)
@public_endpoint(custom_message="邮箱验证失败")
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
        
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

# 这个端点更加直观，专为Swagger UI测试设计
@router.post("/api-key", tags=["认证"])
@public_endpoint(custom_message="获取API密钥失败")
async def get_api_key(
    username: str = "admin",
    password: str = "admin123"
):
    """获取API密钥（Bearer令牌）
    
    这个简化的端点专为Swagger UI测试设计：
    1. 使用默认的管理员凭据（或您自己的凭据）
    2. 执行此请求获取令牌
    3. 复制完整的Authorization头值（包含Bearer前缀）
    4. 点击右上角的Authorize按钮
    5. 在ApiKeyAuth部分的文本框中粘贴整个值
    6. 点击Authorize完成认证
    
    无需验证码，仅用于API测试。
    
    Returns:
        访问令牌和使用示例
    """
    try:
        user = await authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户角色和权限
        role_name = user["role"] if isinstance(user, dict) else user.role
        if hasattr(role_name, 'value'):
            role_name = role_name.value
        
        role = getattr(Role, role_name.upper(), Role.USER)
        permissions = [p for p in permission_checker.role_permissions[role]]
        
        # 获取用户ID和用户名
        user_id = user["id"] if isinstance(user, dict) else user.id
        username = user["username"] if isinstance(user, dict) else user.username
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": username, 
                "id": user_id, 
                "role": role_name,
                "permissions": permissions
            },
            expires_delta=access_token_expires
        )
        
        # 构建带有Bearer前缀的Authorization头值
        auth_header = f"Bearer {access_token}"
        
        # 返回详细的响应，包括如何使用令牌
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "authorization_header": auth_header,
            "usage_example": "在Authorize对话框中的ApiKeyAuth部分直接粘贴整个authorization_header值",
            "user_info": {
                "id": user_id,
                "username": username,
                "role": role_name,
                "permissions": permissions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"认证服务器错误: {str(e)}",
        )

@router.get("/verify", response_model=TokenVerifyResponse)
@public_endpoint(auth_required=True, custom_message="Token验证失败")
@with_error_handling(default_error_message="Token验证失败")
async def verify_token(
    request: Request,
    user: User = Depends(get_current_user)
):
    """验证当前用户的JWT Token
    
    验证当前请求中的JWT Token是否有效，并返回用户信息。
    
    Args:
        request: FastAPI请求对象
        user: 当前用户对象
        
    Returns:
        TokenVerifyResponse: 包含验证结果和用户信息的响应
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token验证失败", "code": "token_invalid"}
        )
    
    # 记录验证成功
    logger.info(f"Token验证成功: user_id={user.id}, username={user.username}")
    
    # 返回验证结果
    return {
        "valid": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }