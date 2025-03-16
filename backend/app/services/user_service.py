"""
用户服务

提供用户相关的业务逻辑实现，包括：
- 用户注册与认证
- 用户信息管理
- 用户权限检查
- 用户关联数据处理

该服务层依赖于UserRepository进行数据访问，提供更高层次的业务抽象。
"""

from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy import desc, asc
from sqlalchemy import select, desc, asc
from datetime import datetime, timedelta
import secrets
import hashlib

from ..core.base_service import BaseService
from ..db.models import User
from ..db.repositories.user_repository import UserRepository
from ..db.repositories.post_repository import PostRepository
from ..core.security import get_password_hash, verify_password
from ..core.exceptions import BusinessError
from ..core.logging import get_logger
from ..core.config import settings
# 导入邮件任务
from ..tasks.email import send_welcome_email, send_reset_password_email, send_verification_email

logger = get_logger(__name__)

# 创建代理用户仓库实例
user_repository = UserRepository()
post_repository = PostRepository()

# Redis键前缀
RESET_TOKEN_PREFIX = "password_reset:"
VERIFICATION_TOKEN_PREFIX = "email_verification:"

class UserService(BaseService):
    """用户服务
    
    处理用户相关的业务逻辑
    """
    
    def __init__(self):
        """初始化
        
        创建UserRepository实例，并传递给基类
        """
        super().__init__(User, user_repository)
        self.repository = user_repository
        self.post_repository = post_repository
    
    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户凭据
        
        Args:
            username: 用户名或邮箱
            password: 明文密码
            
        Returns:
            Optional[Dict[str, Any]]: 验证成功返回用户信息，失败返回None
        """
        # 先尝试用户名登录
        user = await self.repository.get_by_username(username)
        
        # 如果用户名不存在，尝试邮箱登录
        if not user:
            user = await self.repository.get_by_email(username)
            
        if not user:
            return None
            
        # 检查用户是否被禁用
        if not user.get("is_active", False):
            return None
            
        # 验证密码
        if not verify_password(password, user.get("hashed_password", "")):
            return None
            
        return user
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新用户
        
        处理用户名和邮箱的唯一性校验、密码哈希等业务规则
        
        Args:
            user_data: 用户数据，包含username、email、password等字段
            
        Returns:
            Dict[str, Any]: 创建的用户信息
            
        Raises:
            BusinessError: 当用户名或邮箱已存在时
        """
        # 检查用户名是否已存在
        existing_user = await self.repository.get_by_username(user_data.get("username"))
        if existing_user:
            raise BusinessError(message="用户名已存在", code="username_exists")
            
        # 检查邮箱是否已存在
        existing_email = await self.repository.get_by_email(user_data.get("email"))
        if existing_email:
            raise BusinessError(message="邮箱已被注册", code="email_exists")
            
        # 处理密码 - 转换为哈希密码
        if "password" in user_data:
            hashed_password = get_password_hash(user_data.pop("password"))
            user_data["hashed_password"] = hashed_password
            
        # 设置默认值
        if "role" not in user_data:
            user_data["role"] = "user"  # 默认普通用户角色
            
        # 新用户默认为未激活状态，需要通过邮箱验证激活
        user_data["is_active"] = False
            
        # 创建用户
        new_user = await self.create(user_data)
        
        # 生成验证令牌
        verify_token = self._generate_token()
        
        # 存储令牌到Redis
        await self.repository.set_verification_token(user_data.get("email"), verify_token, expires=172800)  # 48小时有效
        
        # 发送验证邮件
        try:
            await send_verification_email.delay(
                user_email=user_data.get("email"),
                username=user_data.get("username"),
                verify_token=verify_token
            )
            logger.info(f"已为用户 {user_data.get('username')} 发送邮箱验证邮件")
        except Exception as e:
            # 邮件发送失败不影响用户注册流程
            logger.error(f"邮箱验证邮件发送失败: {str(e)}")
        
        # 发送欢迎邮件
        try:
            await send_welcome_email.delay(
                user_email=user_data.get("email"),
                username=user_data.get("username")
            )
            logger.info(f"已为用户 {user_data.get('username')} 发送欢迎邮件")
        except Exception as e:
            # 邮件发送失败不影响用户注册流程
            logger.error(f"欢迎邮件发送失败: {str(e)}")
        
        return new_user
        
    def _generate_token(self) -> str:
        """生成随机令牌
        
        Returns:
            str: 生成的令牌
        """
        # 生成32字节的随机字符串
        random_bytes = secrets.token_bytes(32)
        # 转换为16进制字符串
        return hashlib.sha256(random_bytes).hexdigest()
        
    async def verify_email(self, email: str, token: str) -> bool:
        """验证用户邮箱
        
        Args:
            email: 用户邮箱
            token: 验证令牌
            
        Returns:
            bool: 验证是否成功
            
        Raises:
            BusinessError: 当令牌无效或已过期时
        """
        # 从Redis中获取与邮箱关联的验证令牌
        stored_token = await self.repository.get_verification_token(email)
        if not stored_token or stored_token != token:
            raise BusinessError(message="无效或已过期的验证令牌", code="invalid_token")
        
        # 获取用户信息
        user = await self.repository.get_by_email(email)
        if not user:
            raise BusinessError(message="用户不存在", code="user_not_found")
        
        # 激活用户
        await self.repository.update(user["id"], {"is_active": True})
        
        # 删除已使用的验证令牌
        await self.repository.delete_verification_token(email)
        
        logger.info(f"用户 {user['username']} 成功验证邮箱")
        return True
        
    async def update_user(self, user_id: int, user_data: Dict[str, Any], current_user_id: int = None) -> Optional[Dict[str, Any]]:
        """更新用户信息
        
        处理密码更新、邮箱唯一性检查等业务规则
        
        Args:
            user_id: 用户ID
            user_data: 要更新的用户数据
            current_user_id: 当前操作用户的ID，用于权限检查
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的用户信息，不存在则返回None
            
        Raises:
            BusinessError: 当邮箱已被其他用户使用
        """
        # 检查用户是否存在
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
            
        # 检查邮箱唯一性
        if "email" in user_data and user_data["email"] != user["email"]:
            existing = await self.repository.get_by_email(user_data["email"])
            if existing and existing["id"] != user_id:
                raise BusinessError(message="邮箱已被其他用户使用", code="email_exists")
                
        # 处理密码更新
        if "password" in user_data:
            hashed_password = get_password_hash(user_data.pop("password"))
            user_data["hashed_password"] = hashed_password
            
        # 更新用户信息
        return await self.update(user_id, user_data)
        
    async def get_user_posts(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 分页偏移
            limit: 每页条数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        return await self.repository.get_user_posts(user_id, skip, limit)
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户列表
        
        支持分页、排序和过滤
        
        Args:
            skip: 分页偏移
            limit: 每页条数
            sort: 排序字段
            order: 排序方向 ("asc"或"desc")
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 用户列表和总数
        """
        # 构建过滤条件和排序规则
        filters = []
        sort_field = None
        
        # 处理排序
        if sort and hasattr(self.model, sort):
            sort_field = getattr(self.model, sort)
            if order.lower() == "desc":
                sort_field = desc(sort_field)
            else:
                sort_field = asc(sort_field)
        
        # 获取分页数据
        data = await self.list(
            skip=skip, 
            limit=limit, 
            filters=filters, 
            sort_field=sort_field
        )
        
        # 获取总数
        total = await self.count(filters=filters)
        
        return data, total 
    
    async def delete_user(self, user_id: int) -> bool:
        """软删除用户
        
        将用户标记为已删除，而不是物理删除
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            BusinessError: 当用户不存在时
        """
        # 检查用户是否存在
        user = await self.get(user_id)
        if not user:
            raise BusinessError(message="用户不存在", code="user_not_found")
            
        # 如果用户已经是删除状态，返回成功
        if user.get("is_deleted"):
            return True
            
        # 执行软删除
        return await self.repository.soft_delete(user_id)
    
    async def restore_user(self, user_id: int) -> Dict[str, Any]:
        """恢复已删除的用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 恢复后的用户信息
            
        Raises:
            BusinessError: 如果用户不存在或恢复失败
        """
        # 检查用户是否存在
        user = await self.repository.get_by_id(user_id, include_deleted=True)
        if not user:
            raise BusinessError(message="用户不存在", detail="找不到指定ID的用户", error_code="USER_NOT_FOUND")
            
        # 恢复用户
        success = await self.repository.restore(user_id)
        if not success:
            raise BusinessError(message="恢复用户失败", detail="无法恢复用户，可能用户不存在或已经被恢复", error_code="USER_RESTORE_FAILED")
            
        # 获取恢复后的用户信息
        restored_user = await self.repository.get_by_id(user_id)
        return restored_user
        
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户的详细资料
        
        获取用户的详细资料，包括基本信息和统计数据（帖子数、评论数等）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户资料详情
            
        Raises:
            BusinessError: 如果用户不存在
        """
        user_profile = await self.repository.get_user_profile(user_id)
        
        if not user_profile:
            raise BusinessError(
                message="用户不存在",
                detail=f"未找到ID为{user_id}的用户",
                error_code="USER_NOT_FOUND"
            )
            
        return user_profile 
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """通过ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户信息，不存在则返回None
            
        Raises:
            HTTPException: 用户不存在时抛出404错误
        """
        user = await self.repository.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user 
    
    async def request_password_reset(self, email: str) -> bool:
        """请求密码重置
        
        生成密码重置令牌并发送密码重置邮件
        
        Args:
            email: 用户邮箱
            
        Returns:
            bool: 操作是否成功
        """
        # 检查用户是否存在
        user = await self.repository.get_by_email(email)
        if not user:
            # 出于安全考虑，即使用户不存在也返回成功
            # 这样攻击者无法通过此接口探测邮箱是否存在
            logger.info(f"尝试为不存在的邮箱 {email} 重置密码")
            return True
            
        # 生成重置令牌
        reset_token = self._generate_token()
        
        # 存储令牌到Redis
        await self.repository.set_reset_token(email, reset_token, expires=86400)  # 24小时有效
        
        # 发送重置密码邮件
        try:
            await send_reset_password_email.delay(
                user_email=email,
                username=user["username"],
                reset_token=reset_token
            )
            logger.info(f"已为用户 {user['username']} 发送密码重置邮件")
            return True
        except Exception as e:
            logger.error(f"密码重置邮件发送失败: {str(e)}")
            return False
    
    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        """重置密码
        
        验证令牌并更新用户密码
        
        Args:
            reset_token: 密码重置令牌
            new_password: 新密码
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            BusinessError: 当令牌无效或已过期时
        """
        # TODO: 实现完整的密码重置逻辑
        # 由于目前缺少从令牌映射到用户的方法，暂时不实现完整逻辑
        
        # 简化版实现，假设token中包含了email信息
        email = "user@example.com"  # 这应该从token中解析出来
        
        # 验证令牌
        stored_token = await self.repository.get_reset_token(email)
        if not stored_token or stored_token != reset_token:
            raise BusinessError(message="无效或已过期的重置令牌", code="invalid_token")
        
        # 获取用户信息
        user = await self.repository.get_by_email(email)
        if not user:
            raise BusinessError(message="用户不存在", code="user_not_found")
        
        # 更新密码
        hashed_password = get_password_hash(new_password)
        await self.repository.update(user["id"], {"hashed_password": hashed_password})
        
        # 删除已使用的令牌
        await self.repository.delete_reset_token(email)
        
        logger.info(f"用户 {user['username']} 成功重置密码")
        return True 