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
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, desc, asc

from ..core.base_service import BaseService
from ..db.models import User
from ..db.repositories.user_repository import UserRepository
from ..core.security import get_password_hash, verify_password
from ..core.exceptions import BusinessError

class UserService(BaseService):
    """用户业务逻辑服务"""
    
    def __init__(self):
        """初始化用户服务
        
        创建UserRepository实例，并传递给基类
        """
        self.repository = UserRepository()
        super().__init__(User, self.repository)
    
    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证
        
        验证用户名和密码是否匹配
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            Optional[Dict[str, Any]]: 认证成功返回用户信息，失败返回None
        """
        # 先尝试用用户名查询
        user = await self.repository.get_by_username(username)
        
        # 如果未找到，尝试用邮箱查询
        if not user:
            user = await self.repository.get_by_email(username)
            
        if not user:
            return None
            
        # 验证密码
        if not verify_password(password, user["hashed_password"]):
            return None
            
        return user
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新用户
        
        包含业务规则验证：
        - 检查用户名和邮箱是否已存在
        - 密码哈希处理
        - 设置默认角色和状态
        
        Args:
            user_data: 用户数据，包含username、email、password等字段
            
        Returns:
            Dict[str, Any]: 创建成功的用户信息
            
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
            
        if "is_active" not in user_data:
            user_data["is_active"] = True
            
        # 创建用户
        return await self.create(user_data)
        
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
        current_user = await self.get(user_id)
        if not current_user:
            return None
            
        # 如果更新邮箱，需要检查唯一性
        if "email" in user_data and user_data["email"] != current_user["email"]:
            existing = await self.repository.get_by_email(user_data["email"])
            if existing and existing["id"] != user_id:
                raise BusinessError(message="邮箱已被其他用户使用", code="email_exists")
                
        # 如果更新密码，需要加密
        if "password" in user_data:
            hashed_password = get_password_hash(user_data.pop("password"))
            user_data["hashed_password"] = hashed_password
            
        # 更新用户
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