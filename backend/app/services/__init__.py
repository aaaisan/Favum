"""
服务层模块

提供业务逻辑层的实现，位于控制器(API)和数据访问层(Repository)之间。
服务层负责：
- 实现业务规则和处理逻辑
- 协调多个Repository操作
- 处理事务和一致性
- 提供领域概念的高级抽象

这种分层设计有助于分离关注点，使代码更具可维护性和可测试性。
"""

from .user_service import UserService
from .post_service import PostService
from .comment_service import CommentService
from .tag_service import TagService
from .section_service import SectionService
from .category_service import CategoryService
from .favorite_service import FavoriteService
from .captcha_service import CaptchaService
# 暂时注释掉，待tasks功能启用时取消注释
# from .task_service import TaskService

# 导出服务类
__all__ = [
    'UserService',
    'PostService',
    'CommentService',
    'TagService',
    'SectionService',
    'CategoryService',
    'FavoriteService',
    'CaptchaService',
    # 'TaskService',
] 