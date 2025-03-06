from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Set, Any, Tuple
from collections import deque
from ..db.models import UserRole, Post, User, Section
from ..db.database import get_db
from .auth import get_current_active_user
from .enums import Role, Permission

# 统一角色配置：包含权限和继承关系
ROLE_CONFIG = {
    Role.GUEST: {
        "permissions": [],  # 访客无权限
        "inherits": []
    },
    Role.USER: {
        "permissions": [
            Permission.CREATE_POST,
            Permission.EDIT_POST,
            Permission.DELETE_POST,
            Permission.CREATE_COMMENT,
            Permission.EDIT_COMMENT,
            Permission.DELETE_COMMENT,
            Permission.EDIT_PROFILE,
            Permission.HIDE_POST,
        ],
        "inherits": [Role.GUEST]
    },
    Role.MODERATOR: {
        "permissions": [
            Permission.VIEW_USERS,
            Permission.MANAGE_CONTENT,
        ],
        "inherits": [Role.USER]
    },
    Role.ADMIN: {
        "permissions": [
            Permission.MANAGE_USERS,
            Permission.MANAGE_SECTIONS,
            Permission.MANAGE_SYSTEM,
        ],
        "inherits": [Role.MODERATOR]
    },
    Role.SUPER_ADMIN: {
        "permissions": [
            # 超级管理员拥有所有权限
            # 可以添加任何系统特定的权限
        ],
        "inherits": [Role.ADMIN]  # 继承管理员的所有权限
    }
}

# 从统一配置生成权限和继承关系
ROLE_PERMISSIONS = {role: config["permissions"] for role, config in ROLE_CONFIG.items()}
ROLE_HIERARCHY = {role: config.get("inherits", []) for role, config in ROLE_CONFIG.items()}

def safe_enum_parse(enum_class, value, default=None):
    """安全解析枚举值
    
    Args:
        enum_class: 枚举类
        value: 要解析的值
        default: 解析失败时的默认值
        
    Returns:
        解析后的枚举值或默认值
    """
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default

def get_role_permissions(role: Role) -> Set[Permission]:
    """
    获取角色所有权限（包含继承的权限）
    
    使用内存缓存优化重复计算，使用迭代方式替代递归，避免重复遍历角色层次结构。
    
    Args:
        role: 角色
        
    Returns:
        角色拥有的所有权限集合
    """
    # 在函数内部导入避免循环引用
    from .decorators.cache import memo
    
    # 定义内部函数并使用缓存
    @memo
    def _get_permissions(r: Role) -> Set[Permission]:
        # 使用BFS代替递归，更高效处理大型层次结构
        result = set(ROLE_PERMISSIONS.get(r, []))
        
        # 使用队列进行广度优先遍历
        queue = deque(ROLE_HIERARCHY.get(r, []))
        processed = {r}
        
        while queue:
            current_role = queue.popleft()
            if current_role in processed:
                continue
                
            processed.add(current_role)
            result.update(ROLE_PERMISSIONS.get(current_role, []))
            queue.extend(r for r in ROLE_HIERARCHY.get(current_role, []) if r not in processed)
                
        return result
    
    return _get_permissions(role)

def has_permission(user_role: str, permission: Permission) -> bool:
    """
    检查角色是否拥有指定权限
    
    使用内存缓存优化重复检查，提高权限验证性能。
    
    Args:
        user_role: 用户角色名称
        permission: 要检查的权限
        
    Returns:
        是否拥有权限
    """
    # 在函数内部导入避免循环引用
    from .decorators.cache import memo
    
    # 定义内部函数并使用缓存
    @memo
    def _check_permission(role_name: str, perm: Permission) -> bool:
        role = safe_enum_parse(Role, role_name)
        if role is None:
            return False
            
        role_permissions = get_role_permissions(role)
        return perm in role_permissions
    
    return _check_permission(user_role, permission)

def get_user_permissions(user_role: str) -> List[str]:
    """
    获取用户所有权限列表
    
    使用内存缓存优化重复计算，加速权限列表获取。
    
    Args:
        user_role: 用户角色名称
        
    Returns:
        权限列表
    """
    # 在函数内部导入避免循环引用
    from .decorators.cache import memo
    
    # 定义内部函数并使用缓存
    @memo
    def _get_permissions(role_name: str) -> List[str]:
        role = safe_enum_parse(Role, role_name)
        if role is None:
            return []
            
        return [p.value for p in get_role_permissions(role)]
    
    return _get_permissions(user_role)

def check_resource_permission(
    user: User,
    resource_id: int,
    resource_type: str,
    action: str,
    db: Session,
    owner_id_field: str = "author_id"
) -> Tuple[bool, Any]:
    """通用资源权限检查
    
    Args:
        user: 用户对象
        resource_id: 资源ID
        resource_type: 资源类型 ('post', 'comment', 'section')
        action: 操作类型 ('edit', 'delete', 'hide')
        db: 数据库会话
        owner_id_field: 资源所有者ID字段名
        
    Returns:
        (是否有权限, 资源对象)
    """
    # 选择资源类型
    if resource_type == 'post':
        ResourceModel = Post
        admin_permission = Permission.MANAGE_CONTENT
    elif resource_type == 'comment':
        ResourceModel = Post  # 假设注释模型
        admin_permission = Permission.MANAGE_CONTENT
    elif resource_type == 'section':
        ResourceModel = Section
        admin_permission = Permission.MANAGE_SECTIONS
    else:
        return False, None
    
    # 获取资源
    resource = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
    if not resource:
        return False, None
    
    # 管理员权限检查
    if has_permission(user.role, Permission.MANAGE_SYSTEM) or has_permission(user.role, admin_permission):
        return True, resource
    
    # 版主权限检查 (对于帖子和评论)
    if resource_type in ['post', 'comment'] and has_permission(user.role, Permission.MANAGE_CONTENT):
        # 检查版主是否管理该版块
        if resource_type == 'post' and hasattr(resource, 'section_id'):
            return any(section.id == resource.section_id for section in user.moderated_sections), resource
    
    # 普通用户权限：检查是否资源所有者
    action_permission = None
    if action == 'edit':
        action_permission = Permission.EDIT_POST if resource_type == 'post' else Permission.EDIT_COMMENT
    elif action == 'delete':
        action_permission = Permission.DELETE_POST if resource_type == 'post' else Permission.DELETE_COMMENT
    elif action == 'hide':
        action_permission = Permission.HIDE_POST
    
    if action_permission and has_permission(user.role, action_permission):
        # 检查是否资源所有者
        return getattr(resource, owner_id_field) == user.id, resource
    
    return False, resource

class PermissionChecker:
    """权限检查器类
    
    提供各种权限检查方法，用于验证用户对特定资源的访问权限
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        """初始化权限检查器
        
        Args:
            db: 数据库会话实例
        """
        self.db = db

    def _is_role(self, user: User, roles: List[Role]) -> bool:
        """检查用户是否具有指定角色之一
        
        Args:
            user: 用户对象
            roles: 角色列表
            
        Returns:
            是否匹配角色
        """
        user_role = safe_enum_parse(Role, user.role)
        return user_role in roles

    async def is_admin(self, user: User = Depends(get_current_active_user)) -> bool:
        """检查用户是否为管理员
        
        Args:
            user: 当前用户实例
            
        Returns:
            bool: 是否为管理员
        """
        return self._is_role(user, [Role.ADMIN])

    async def is_moderator(self, user: User = Depends(get_current_active_user)) -> bool:
        """检查用户是否为版主
        
        Args:
            user: 当前用户实例
            
        Returns:
            bool: 是否为版主
        """
        return self._is_role(user, [Role.ADMIN, Role.MODERATOR])

    async def can_modify_post(
        self,
        post_id: int,
        user: User = Depends(get_current_active_user)
    ) -> bool:
        """检查用户是否可以修改指定帖子
        
        验证规则：
        1. 管理员可以修改任何帖子
        2. 版主可以修改其管理的版块中的帖子
        3. 普通用户只能修改自己的帖子
        
        Args:
            post_id: 帖子ID
            user: 当前用户实例
            
        Returns:
            bool: 是否可以修改帖子
            
        Raises:
            HTTPException: 帖子不存在时抛出404错误
        """
        has_permission, post = check_resource_permission(
            user, post_id, 'post', 'edit', self.db
        )
        
        if post is None:
            raise HTTPException(status_code=404, detail="帖子不存在")
            
        return has_permission

    async def can_delete_post(
        self,
        post_id: int,
        user: User = Depends(get_current_active_user)
    ) -> bool:
        """检查用户是否可以删除指定帖子
        
        验证规则与修改帖子相同
        
        Args:
            post_id: 帖子ID
            user: 当前用户实例
            
        Returns:
            bool: 是否可以删除帖子
        """
        has_permission, post = check_resource_permission(
            user, post_id, 'post', 'delete', self.db
        )
        
        if post is None:
            raise HTTPException(status_code=404, detail="帖子不存在")
            
        return has_permission

    async def can_hide_post(
        self,
        post_id: int,
        user: User = Depends(get_current_active_user)
    ) -> bool:
        """检查用户是否可以隐藏指定帖子
        
        验证规则：
        1. 管理员可以隐藏任何帖子
        2. 版主可以隐藏其管理的版块中的帖子
        3. 普通用户只能隐藏自己的帖子
        
        Args:
            post_id: 帖子ID
            user: 当前用户实例
            
        Returns:
            bool: 是否可以隐藏帖子
            
        Raises:
            HTTPException: 帖子不存在时抛出404错误
        """
        has_permission, post = check_resource_permission(
            user, post_id, 'post', 'hide', self.db
        )
        
        if post is None:
            raise HTTPException(status_code=404, detail="帖子不存在")
            
        return has_permission

    async def can_manage_section(
        self,
        section_id: int,
        user: User = Depends(get_current_active_user)
    ) -> bool:
        """检查用户是否可以管理指定版块
        
        验证规则：
        1. 管理员可以管理任何版块
        2. 版主只能管理被分配的版块
        3. 其他用户没有管理权限
        
        Args:
            section_id: 版块ID
            user: 当前用户实例
            
        Returns:
            bool: 是否可以管理版块
        """
        has_permission, section = check_resource_permission(
            user, section_id, 'section', 'edit', self.db
        )
        
        if section is None:
            raise HTTPException(status_code=404, detail="版块不存在")
            
        return has_permission

def get_permission_checker(db: Session = Depends(get_db)):
    """创建权限检查器实例
    
    用于依赖注入的工厂函数
    
    Args:
        db: 数据库会话
        
    Returns:
        PermissionChecker实例
    """
    return PermissionChecker(db)

def check_admin(user: User = Depends(get_current_active_user)):
    """验证用户是否为管理员
    
    用于FastAPI依赖注入的管理员权限检查。
    
    Args:
        user: 当前登录用户
        
    Returns:
        dict: 成功时返回用户信息
        
    Raises:
        HTTPException: 权限不足时抛出403错误
    """
    if not has_permission(user.role, Permission.MANAGE_SYSTEM):
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")
    return {"id": user.id, "username": user.username}

def check_moderator(user: User = Depends(get_current_active_user)):
    """验证用户是否为版主或管理员
    
    Args:
        user: 当前登录用户
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 权限不足时抛出403错误
    """
    role = safe_enum_parse(Role, user.role)
    if role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(
            status_code=403,
            detail="需要版主权限"
        )
    return user 