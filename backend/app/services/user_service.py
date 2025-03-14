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
# from sqlalchemy import select, desc, asc
# from datetime import datetime, timedelta
import secrets
import hashlib
import logging
from datetime import datetime

from ..core.base_service import BaseService
from ..db.models import User
from ..db.repositories.user_repository import UserRepository
from ..db.repositories.post_repository import PostRepository
from ..core.security import get_password_hash, verify_password
from ..core.exceptions import BusinessException
from ..core.logging import get_logger
from ..core.config import settings
# 导入邮件任务
from ..tasks.email import send_welcome_email, send_reset_password_email, send_verification_email

logger = logging.getLogger(__name__)

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
        
        验证用户提供的用户名和密码是否正确
        
        Args:
            username: 用户名或邮箱
            password: 明文密码
            
        Returns:
            Optional[Dict[str, Any]]: 验证成功返回用户信息，失败返回None
        """
        try:
            # 先尝试用户名登录
            user = await self.repository.get_by_username(username)
            
            # 如果用户名不存在，尝试邮箱登录
            if not user:
                user = await self.repository.get_by_email(username)
                
            if not user:
                logger.info(f"用户验证失败: 用户不存在 - {username}")
                return None
                
            # 检查用户是否被禁用或删除
            if not user.get("is_active", False) or user.get("is_deleted", False):
                logger.info(f"用户验证失败: 用户未激活或已删除 - {username}")
                return None
                
            # 验证密码
            if not verify_password(password, user.get("hashed_password", "")):
                logger.info(f"用户验证失败: 密码错误 - {username}")
                return None
            
            # 更新最后登录时间
            user_id = user.get("id")
            await self.repository.update_last_login(user_id)
            
            # 重新获取完整用户信息
            user = await self.repository.get_by_id(user_id)
            
            # 格式化日期时间字段
            self._format_datetime_fields(user)
            
            logger.info(f"用户验证成功: {username}")
            return user
        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}", exc_info=True)
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新用户
        
        处理用户名和邮箱的唯一性校验、密码哈希等业务规则
        
        Args:
            user_data: 用户数据，包含username、email、password等字段
            
        Returns:
            Dict[str, Any]: 创建的用户信息
            
        Raises:
            BusinessException: 当用户名或邮箱已存在时
        """
        # 检查用户名是否已存在
        existing_user = await self.repository.get_by_username(user_data.get("username"))
        if existing_user:
            raise BusinessException(message="用户名已存在", code="username_exists")
            
        # 检查邮箱是否已存在
        existing_email = await self.repository.get_by_email(user_data.get("email"))
        if existing_email:
            raise BusinessException(message="邮箱已被注册", code="email_exists")
            
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
        await self.repository.set_verification_token(user_data.get("email"), verify_token, expires=3600)  # 1小时有效
        
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
            BusinessException: 当令牌无效或已过期时
        """
        # 从Redis中获取与邮箱关联的验证令牌
        stored_token = await self.repository.get_verification_token(email)
        if not stored_token or stored_token != token:
            raise BusinessException(message="无效或已过期的验证令牌", code="invalid_token")
        
        # 获取用户信息
        user = await self.repository.get_by_email(email)
        if not user:
            raise BusinessException(message="用户不存在", code="user_not_found")
        
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
            BusinessException: 当邮箱已被其他用户使用
        """
        # 检查用户是否存在
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
            
        # 检查邮箱唯一性
        if "email" in user_data and user_data["email"] != user["email"]:
            existing = await self.repository.get_by_email(user_data["email"])
            if existing and existing["id"] != user_id:
                raise BusinessException(message="邮箱已被其他用户使用", code="email_exists")
                
        # 处理密码更新
        if "password" in user_data:
            hashed_password = get_password_hash(user_data.pop("password"))
            user_data["hashed_password"] = hashed_password
            
        # 更新用户信息
        updated_user = await self.update(user_id, user_data)
        
        # 格式化日期时间字段
        self._format_datetime_fields(updated_user)
        
        return updated_user
        
    def _format_datetime_fields(self, data: Dict[str, Any]) -> None:
        """格式化字典中的日期时间字段为字符串
        
        Args:
            data: 包含日期时间字段的字典
        """
        if not data:
            return
            
        datetime_fields = ['created_at', 'updated_at', 'deleted_at', 'last_login', 'join_date']
        for field in datetime_fields:
            if field in data and data[field] and not isinstance(data[field], str):
                data[field] = data[field].isoformat()
        
        # 处理嵌套字段
        for key, value in data.items():
            if isinstance(value, dict):
                self._format_datetime_fields(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._format_datetime_fields(item)
        
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
            BusinessException: 当用户不存在时
        """
        # 检查用户是否存在
        user = await self.get(user_id)
        if not user:
            raise BusinessException(message="用户不存在", code="user_not_found")
            
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
            BusinessException: 如果用户不存在或恢复失败
        """
        # 检查用户是否存在
        user = await self.repository.get_by_id(user_id, include_deleted=True)
        if not user:
            raise BusinessException(message="用户不存在", detail="找不到指定ID的用户", error_code="USER_NOT_FOUND")
            
        # 恢复用户
        success = await self.repository.restore(user_id)
        if not success:
            raise BusinessException(message="恢复用户失败", detail="无法恢复用户，可能用户不存在或已经被恢复", error_code="USER_RESTORE_FAILED")
            
        # 获取恢复后的用户信息
        restored_user = await self.repository.get_by_id(user_id)
        return restored_user
        
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户详细资料
        
        返回包含用户基本信息和统计数据的资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户资料
            
        Raises:
            BusinessException: 当用户不存在时抛出
        """
        # 使用Repository获取用户详细资料
        user_profile = await self.repository.get_user_profile(user_id)
        
        if not user_profile:
            raise BusinessException(
                message="用户不存在",
                error_code="user_not_found",
                status_code=404
            )
        
        # 格式化日期时间字段
        self._format_datetime_fields(user_profile)
        
        return user_profile
        
    # async def get_user_profile_id_ref(self, user_id: int) -> Dict[str, Any]:
    #     """获取用户详细资料（ID引用版本）
        
    #     返回包含用户基本信息和ID引用的资料
        
    #     Args:
    #         user_id: 用户ID
            
    #     Returns:
    #         Dict[str, Any]: 用户资料
            
    #     Raises:
    #         BusinessException: 当用户不存在时抛出
    #     """
    #     # 使用Repository获取用户详细资料
    #     user_profile = await self.repository.get_user_profile_id_ref(user_id)
        
    #     if not user_profile:
    #         raise BusinessException(
    #             message="用户不存在",
    #             error_code="user_not_found",
    #             status_code=404
    #         )
        
    #     # 格式化日期时间字段
    #     self._format_datetime_fields(user_profile)
        
    #     return user_profile
        
    async def get_user_post_count(self, user_id: int) -> int:
        """获取用户帖子数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 帖子数量
        """
        return await self.repository.get_user_post_count(user_id)
        
    async def get_user_comment_count(self, user_id: int) -> int:
        """获取用户评论数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 评论数量
        """
        return await self.repository.get_user_comment_count(user_id)
        
    async def get_user_post_ids(self, user_id: int, limit: int = 10) -> List[int]:
        """获取用户帖子ID列表
        
        Args:
            user_id: 用户ID
            limit: 最大返回数量
            
        Returns:
            List[int]: 帖子ID列表
        """
        return await self.repository.get_user_post_ids(user_id, limit)
        
    async def get_user_favorite_post_ids(self, user_id: int, limit: int = 10) -> List[int]:
        """获取用户收藏帖子ID列表
        
        Args:
            user_id: 用户ID
            limit: 最大返回数量
            
        Returns:
            List[int]: 收藏帖子ID列表
        """
        return await self.repository.get_user_favorite_post_ids(user_id, limit)
    
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
        await self.repository.set_reset_token(email, reset_token, expires=3600)  # 1小时有效
        
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
            BusinessException: 当令牌无效或已过期时
        """
        # 根据令牌查找关联的邮箱
        email = await self.repository.get_email_by_reset_token(reset_token)
        
        # 如果找不到关联的邮箱，说明令牌无效或已过期
        if not email:
            raise BusinessException(message="无效或已过期的重置令牌", code="invalid_token")
        
        # 获取用户信息
        user = await self.repository.get_by_email(email)
        if not user:
            raise BusinessException(message="用户不存在", code="user_not_found")
        
        # 更新密码
        hashed_password = get_password_hash(new_password)
        await self.repository.update(user["id"], {"hashed_password": hashed_password})
        
        # 删除已使用的令牌
        await self.repository.delete_reset_token(email, reset_token)
        
        logger.info(f"用户 {user['username']} 成功重置密码")
        return True 

    def model_to_dict(self, model_instance) -> Dict[str, Any]:
        """
        将模型实例转换为字典
        
        支持SQLAlchemy模型实例和已经是字典的数据
        
        Args:
            model_instance: 模型实例或字典
            
        Returns:
            Dict[str, Any]: 包含模型属性的字典
        """
        # 如果已经是字典，直接返回
        if isinstance(model_instance, dict):
            return model_instance
            
        # 如果是None，返回空字典
        if model_instance is None:
            return {}
            
        # 如果存在to_dict方法，使用它
        if hasattr(model_instance, 'to_dict') and callable(getattr(model_instance, 'to_dict')):
            return model_instance.to_dict()
            
        # 否则使用repository的方法
        if hasattr(self.repository, 'model_to_dict'):
            return self.repository.model_to_dict(model_instance)
            
        # 最后尝试自己实现
        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            # 将日期时间对象转换为ISO格式字符串
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result 