"""API响应模型

此包包含所有API端点的标准化响应模型定义。
使用这些模型可以确保API响应的一致性、类型安全和文档完整性。
"""

# 基础响应模型
from .base import (
    BaseResponse, 
    ErrorResponse, 
    DataResponse, 
    PaginatedResponse
)

# 用户相关响应模型
from .user import (
    UserResponse,
    UserProfileResponse,
    UserInfoResponse,
    UserListResponse,
    UserDeleteResponse
)

# 帖子相关响应模型
from .post import (
    PostResponse,
    PostListResponse
)

# 评论相关响应模型
from .comment import (
    CommentResponse,
    CommentListResponse,
    CommentDeleteResponse
)

# 类别相关响应模型
from .category import (
    CategoryResponse,
    CategoryDetailResponse,
    CategoryListResponse,
    CategoryTreeResponse
)

# 板块相关响应模型
from .section import (
    SectionResponse,
    SectionDetailResponse,
    SectionListResponse
)

# 标签相关响应模型
from .tag import (
    TagResponse,
    TagListResponse,
    TagWithPostsResponse,
    TagCloudResponse
)

# 认证相关响应模型
from .auth import (
    TokenResponse,
    TokenDataResponse,
    LoginCheckResponse,
    AuthErrorResponse
)

# 导出所有响应模型，方便导入

__all__ = [
    'BaseResponse', 'ErrorResponse', 'DataResponse', 'PaginatedResponse',
    'UserResponse', 'UserProfileResponse', 'UserInfoResponse', 'UserListResponse', 'UserDeleteResponse',
    'PostResponse', 'PostListResponse',
    'CommentResponse', 'CommentListResponse', 'CommentDeleteResponse',
    'CategoryResponse', 'CategoryDetailResponse', 'CategoryListResponse', 'CategoryTreeResponse',
    'SectionResponse', 'SectionDetailResponse', 'SectionListResponse',
    'TagResponse', 'TagListResponse', 'TagWithPostsResponse', 'TagCloudResponse',
    'TokenResponse', 'TokenDataResponse', 'LoginCheckResponse', 'AuthErrorResponse'
] 