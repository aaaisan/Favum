"""
权限系统使用示例

本模块展示了如何使用经过lru_cache优化的权限系统，并演示了缓存带来的性能提升。
"""

import time
from typing import Dict, List, Optional

from ..core.permissions import Permission, Role, get_role_permissions, has_permission, get_user_permissions

class User:
    """用户类，用于示例"""
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

class Post:
    """帖子类，用于示例"""
    def __init__(self, id: int, title: str, content: str, author_id: int):
        self.id = id
        self.title = title
        self.content = content
        self.author_id = author_id
        self.hidden = False

# 用户数据
users = {
    1: User(1, "admin", Role.ADMIN),
    2: User(2, "moderator", Role.MODERATOR),
    3: User(3, "user1", Role.USER),
    4: User(4, "user2", Role.USER),
    5: User(5, "guest", Role.GUEST)
}

# 帖子数据
posts = {
    1: Post(1, "管理员帖子", "这是管理员的帖子", 1),
    2: Post(2, "版主帖子", "这是版主的帖子", 2),
    3: Post(3, "用户1帖子", "这是用户1的帖子", 3),
    4: Post(4, "用户2帖子", "这是用户2的帖子", 4)
}

def can_edit_post(user_id: int, post_id: int) -> bool:
    """
    检查用户是否有权限编辑帖子
    
    Args:
        user_id: 用户ID
        post_id: 帖子ID
        
    Returns:
        是否有权限编辑
    """
    user = users.get(user_id)
    post = posts.get(post_id)
    
    if not user or not post:
        return False
    
    # 管理员和版主可以编辑任何帖子
    if has_permission(user.role, Permission.MANAGE_CONTENT):
        return True
    
    # 普通用户只能编辑自己的帖子
    if has_permission(user.role, Permission.EDIT_POST) and post.author_id == user.id:
        return True
    
    return False

def hide_post(user_id: int, post_id: int) -> bool:
    """
    隐藏帖子
    
    Args:
        user_id: 用户ID
        post_id: 帖子ID
        
    Returns:
        是否成功隐藏
    """
    if not can_edit_post(user_id, post_id):
        return False
    
    post = posts.get(post_id)
    if post:
        post.hidden = True
        return True
    return False

def demonstration():
    """演示权限系统的使用和性能"""
    print("===== 权限系统演示 =====")
    
    # 1. 展示不同角色的权限
    print("\n各角色权限列表:")
    for user_id, user in users.items():
        perms = get_user_permissions(user.role)
        print(f"{user.username} ({user.role}): {', '.join(perms)}")
    
    # 2. 测试权限检查性能（首次调用 vs 缓存后调用）
    print("\n权限检查性能测试:")
    
    # 清除可能已有的缓存数据（实际项目中一般不需要）
    # 这里仅用于演示首次调用和后续调用的差异
    get_role_permissions.cache_clear()
    has_permission.cache_clear()
    
    # 首次检查权限（未缓存）
    start_time = time.time()
    for _ in range(1000):
        has_permission(Role.MODERATOR, Permission.MANAGE_CONTENT)
    uncached_time = time.time() - start_time
    print(f"首次检查1000次权限（未缓存）: {uncached_time:.6f}秒")
    
    # 再次检查相同权限（已缓存）
    start_time = time.time()
    for _ in range(1000):
        has_permission(Role.MODERATOR, Permission.MANAGE_CONTENT)
    cached_time = time.time() - start_time
    print(f"再次检查1000次相同权限（已缓存）: {cached_time:.6f}秒")
    print(f"性能提升: {uncached_time/cached_time:.2f}倍")
    
    # 3. 测试权限应用场景
    print("\n权限应用场景测试:")
    
    # 测试帖子编辑权限
    test_cases = [
        (1, 3, "管理员编辑用户帖子"),
        (2, 4, "版主编辑用户帖子"),
        (3, 3, "用户编辑自己的帖子"),
        (3, 4, "用户尝试编辑他人帖子"),
        (5, 1, "访客尝试编辑帖子"),
    ]
    
    for user_id, post_id, desc in test_cases:
        user = users.get(user_id)
        result = can_edit_post(user_id, post_id)
        print(f"{desc}: {user.username} {'可以' if result else '不能'}编辑帖子 #{post_id}")

if __name__ == "__main__":
    demonstration() 