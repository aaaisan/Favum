from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi import APIRouter, HTTPException, status, Request, Response
from typing import List, Optional

from ...schemas import post as post_schema
from ...schemas import comment as comment_schema
from ...services.comment_service import CommentService
from ...core.decorators import public_endpoint, admin_endpoint
from ...services.favorite_service import FavoriteService
from ...services import PostService
from ...core.exceptions import BusinessException
from ..responses.post import (
    PostResponse, 
    PostDetailResponse,
    PostListResponse,
    PostCommentResponse,
    PostStatsResponse,
    PostDeleteResponse,
    PostVoteResponse,
    PostFavoriteResponse
)
from ..responses.comment import CommentResponse, CommentListResponse

router = APIRouter()

async def get_post_owner(post_id: int) -> int:
    """获取帖子作者ID
    
    用于权限验证，获取指定帖子的作者ID。
    
    Args:
        post_id: 帖子ID
        
    Returns:
        int: 帖子作者的用户ID
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    try:
        post_service = PostService()
        
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        return post.get("author_id")
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=404 if e.error_code == "post_not_found" else 400,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/", response_model=PostResponse)
@public_endpoint(rate_limit_count=10, auth_required=True, custom_message="创建帖子失败")
async def create_post(
    request: Request,
    post: post_schema.PostCreate
):
    """创建新帖子
    
    创建新的帖子记录，需要用户认证。
    
    包含以下特性：
    1. 速率限制：每小时最多创建10篇帖子
    2. 用户认证：需要有效的访问令牌
    3. 标签处理：自动处理帖子与标签的关联
    
    Args:
        request: FastAPI请求对象
        post: 帖子创建模型，包含标题、内容、分类等
        
    Returns:
        Post: 创建成功的帖子信息
        
    Raises:
        HTTPException: 当权限不足或数据验证失败时抛出相应错误
    """
    # 创建帖子服务实例
    post_service = PostService()
    
    # 从token获取当前用户ID
    current_user_id = request.state.user.get("id")
    
    # 准备帖子数据
    post_data = post.model_dump()
    
    # 如果未提供作者ID，使用当前用户ID
    if "author_id" not in post_data or not post_data["author_id"]:
        post_data["author_id"] = current_user_id
    
    # 创建帖子
    try:
        created_post = await post_service.create_post(post_data)
        return created_post
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/test", response_model=PostResponse)
@public_endpoint(rate_limit_count=10, auth_required=True, custom_message="创建测试帖子失败")
async def create_test_post(
    request: Request
):
    """测试创建帖子
    
    用于测试的简化版创建帖子API。
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 从token获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 准备帖子数据
        post_data = {
            "title": "Test Post",
            "content": "This is a test post",
            "category_id": 1,
            "section_id": 1,
            "author_id": current_user_id
        }
        
        # 创建帖子
        created_post = await post_service.create_post(post_data)
        return created_post
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/", response_model=PostListResponse)
@public_endpoint(rate_limit_count=100, custom_message="获取帖子列表失败")
async def read_posts(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    section_id: Optional[int] = None,
    author_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = None,
    sort: Optional[str] = None,
    order: Optional[str] = "desc"
):
    """获取帖子列表
    
    获取系统中的帖子列表，支持分页、过滤和排序。
    此API端点允许游客访问。
    
    包含以下特性：
    1. 缓存：结果缓存60秒
    2. 过滤：支持按分类、版块、作者、标签过滤
    3. 排序：支持自定义排序字段和顺序
    4. 分页：支持跳过和限制参数
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        category_id: 按分类ID筛选
        section_id: 按版块ID筛选
        author_id: 按作者ID筛选
        tag_ids: 按标签ID列表筛选
        sort: 排序字段
        order: 排序顺序，"asc"或"desc"
        
    Returns:
        PostListResponse: 包含帖子列表和总数的响应
    """
    # 创建帖子服务实例
    post_service = PostService()
    
    # 处理标签ID列表参数
    tag_ids_list = None
    if tag_ids:
        if isinstance(tag_ids, list):
            tag_ids_list = tag_ids
        else:
            # 如果是字符串，尝试解析为列表
            try:
                tag_ids_list = [int(id.strip()) for id in tag_ids.split(",") if id.strip()]
            except ValueError:
                # 忽略无效的标签ID
                pass
    
    # 获取帖子列表和总数
    posts, total = await post_service.get_posts(
        skip=skip,
        limit=limit,
        include_hidden=False,  # 公开API不显示隐藏的帖子
        category_id=category_id,
        section_id=section_id,
        author_id=author_id,
        tag_ids=tag_ids_list,
        sort_field=sort,
        sort_order=order
    )
    
    # 构建响应
    response = {
        "posts": posts,
        "total": total,
        "page_size": limit
    }
    
    return response

@router.get("/{post_id}", response_model=PostDetailResponse)
@public_endpoint(rate_limit_count=1000, custom_message="获取帖子详情失败")
async def read_post(
    request: Request,
    post_id: int
):
    """获取帖子详情
    
    获取指定ID的帖子详细信息，包括分类、标签等关联数据。
    此API端点允许游客访问。
    
    包含以下特性：
    1. 缓存：结果缓存60秒
    2. 关联加载：自动加载分类、版块、标签等关联信息
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        
    Returns:
        Post: 帖子详细信息
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    # 创建帖子服务实例
    post_service = PostService()
    
    # 获取帖子详情，包含关联信息
    post = await post_service.get_post_detail(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查可见性
    if post.get("is_hidden", False):
        # 获取当前用户（如果已登录）
        current_user = None
        try:
            current_user = request.state.user if hasattr(request.state, "user") else None
        except:
            pass
            
        # 游客或普通用户不能查看隐藏的帖子
        is_admin = current_user and current_user.get("role") in ["admin", "super_admin", "moderator"]
        is_author = current_user and str(current_user.get("id")) == str(post.get("author_id"))
        
        if not is_admin and not is_author:
            raise HTTPException(status_code=404, detail="帖子不存在")
    
    return post

@router.put("/{post_id}", response_model=PostResponse)
@public_endpoint(rate_limit_count=20, auth_required=True, custom_message="更新帖子失败", ownership_check_func=get_post_owner)
async def update_post(
    request: Request,
    post_id: int,
    post: post_schema.PostUpdate
):
    """更新帖子
    
    更新指定ID的帖子信息，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post: 更新的帖子数据
        
    Returns:
        Post: 更新后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取帖子详情，检查是否存在
        existing_post = await post_service.get_post_detail(post_id)
        if not existing_post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 检查权限
        user_role = request.state.user.get("role", "user")
        user_id = request.state.user.get("id")
        
        # 如果是管理员或版主，直接允许访问
        if user_role not in ["admin", "super_admin", "moderator"]:
            # 检查是否为资源所有者
            author_id = existing_post.get("author_id")
            if str(author_id) != str(user_id):
                raise HTTPException(
                    status_code=403,
                    detail="没有权限访问此资源"
                )
        
        # 更新帖子
        updated_post = await post_service.update_post(post_id, post.model_dump(exclude_unset=True))
        return updated_post
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{post_id}", response_model=PostDeleteResponse)
@public_endpoint(auth_required=True, custom_message="删除帖子失败")
async def delete_post(
    request: Request,
    post_id: int
):
    """删除帖子
    
    软删除指定的帖子，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取帖子详情，检查是否存在
        existing_post = await post_service.get_post_detail(post_id)
        if not existing_post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 检查权限
        user_role = request.state.user.get("role", "user")
        user_id = request.state.user.get("id")
        
        # 如果是管理员或版主，直接允许访问
        if user_role not in ["admin", "super_admin", "moderator"]:
            # 检查是否为资源所有者
            author_id = existing_post.get("author_id")
            if str(author_id) != str(user_id):
                raise HTTPException(
                    status_code=403,
                    detail="没有权限访问此资源"
                )
        
        # 删除帖子
        success = await post_service.delete_post(post_id)
        
        if success:
            return {"message": "帖子已成功删除", "post_id": post_id}
        else:
            raise HTTPException(status_code=500, detail="删除帖子失败")
            
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{post_id}/restore", response_model=PostResponse)
@admin_endpoint(custom_message="恢复帖子失败")
async def restore_post(
    request: Request,
    post_id: int
):
    """恢复已删除的帖子
    
    恢复指定的已删除帖子，仅允许版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 恢复帖子
        restored_post = await post_service.restore_post(post_id)
        
        return {
            "message": "帖子已成功恢复",
            "post_id": post_id,
            "post": restored_post
        }
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.patch("/{post_id}/visibility", response_model=PostResponse)
@public_endpoint(auth_required=True, custom_message="更改帖子可见性失败")
async def toggle_post_visibility(
    request: Request,
    post_id: int,
    visibility: dict
):
    """切换帖子可见性
    
    隐藏或显示指定的帖子。
    权限规则：
    1. 管理员可以隐藏/显示任何帖子
    2. 版主可以隐藏/显示其管理的版块中的帖子
    3. 普通用户只能隐藏/显示自己的帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        visibility: 包含可见性设置的字典，例如 {"hidden": true}
        
    Returns:
        dict: 包含成功消息和更新后的帖子状态的响应
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取帖子详情，检查是否存在
        existing_post = await post_service.get_post_detail(post_id)
        if not existing_post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 从token中获取用户ID和角色
        user_data = request.state.user
        user_id = user_data.get("id")
        user_role = user_data.get("role", "user")
        
        # 检查权限
        if user_role in ["admin", "super_admin"]:
            # 管理员可以隐藏任何帖子
            pass
        elif user_role == "moderator":
            # TODO: 使用服务层检查版主权限
            # 此处简单实现，实际应将此逻辑迁移到服务层
            # 直接放行，版主权限在业务逻辑层处理
            pass
        else:
            # 普通用户只能隐藏自己的帖子
            author_id = existing_post.get("author_id")
            if author_id != user_id:
                raise HTTPException(status_code=403, detail="您只能隐藏自己的帖子")
        
        # 更新帖子可见性
        is_hidden = visibility.get("hidden", not existing_post.get("is_hidden", False))
        updated_post = await post_service.toggle_visibility(post_id, is_hidden)
        
        status_text = "隐藏" if is_hidden else "显示"
        return {
            "detail": f"帖子已{status_text}",
            "post_id": post_id,
            "is_hidden": is_hidden
        }
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{post_id}/vote", response_model=PostVoteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="点赞操作失败")
async def vote_post(
    request: Request,
    post_id: int,
    vote: post_schema.PostVoteCreate
):
    """对帖子进行点赞或反对
    
    用户可以对帖子进行点赞（赞数+1）或反对（赞数-1）。
    如果用户已经点赞/反对过该帖子，则再次点击相同操作会取消。
    如果用户已经点赞后点击反对，会取消点赞并添加反对，反之亦然。
    
    包含以下特性：
    1. 速率限制：每小时最多进行30次投票操作
    2. 用户认证：需要有效的访问令牌
    3. 原子性：使用事务保证投票和计数更新的原子性
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        vote: 点赞操作信息，包含点赞类型
        
    Returns:
        VoteResponse: 包含操作结果、更新后的点赞数和消息
        
    Raises:
        HTTPException: 当帖子不存在或操作失败时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取当前用户ID
        user_id = request.state.user.get("id")
        
        # 执行投票操作
        result = await post_service.vote_post(post_id, user_id, vote.vote_type)
        
        return result
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{post_id}/votes", response_model=PostStatsResponse)
@public_endpoint(cache_ttl=10, custom_message="获取点赞数失败")
async def get_post_votes(
    request: Request,
    post_id: int
):
    """获取帖子的点赞数
    
    提供帖子的当前点赞计数。
    
    包含以下特性：
    1. 缓存：结果缓存10秒
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        
    Returns:
        PostStatsResponse: 包含点赞数和帖子ID的响应
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取点赞数
        count = await post_service.get_vote_count(post_id)
        
        return {
            "post_id": post_id,
            "vote_count": count
        }
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{post_id}/favorite", response_model=PostFavoriteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="收藏操作失败")
async def favorite_post(
    request: Request,
    post_id: int
):
    """收藏帖子
    
    将指定帖子添加到当前用户的收藏列表中
    
    Args:
        request: FastAPI请求对象
        post_id: 要收藏的帖子ID
        
    Returns:
        FavoriteResponse: 收藏操作结果
        
    Raises:
        HTTPException: 当用户未登录或操作失败时抛出相应错误
    """
    try:
        # 获取当前用户ID
        if not request.state.user:
            raise HTTPException(status_code=401, detail="需要登录才能收藏帖子")
        
        user_id = request.state.user.get("id")
        
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 添加收藏
        result = await favorite_service.add_favorite(post_id, user_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{post_id}/favorite", response_model=PostFavoriteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="取消收藏操作失败")
async def unfavorite_post(
    request: Request,
    post_id: int
):
    """取消收藏帖子
    
    从当前用户的收藏列表中移除指定帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要取消收藏的帖子ID
        
    Returns:
        FavoriteResponse: 取消收藏操作结果
        
    Raises:
        HTTPException: 当用户未登录或操作失败时抛出相应错误
    """
    try:
        # 获取当前用户ID
        if not request.state.user:
            raise HTTPException(status_code=401, detail="需要登录才能操作收藏")
        
        user_id = request.state.user.get("id")
        
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 移除收藏
        result = await favorite_service.remove_favorite(post_id, user_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{post_id}/favorite/status", response_model=bool)
@public_endpoint(cache_ttl=10, custom_message="获取收藏状态失败")
async def check_favorite_status(
    request: Request,
    post_id: int
):
    """检查当前用户是否已收藏指定帖子
    
    返回布尔值，表示当前用户是否已收藏该帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要检查的帖子ID
        
    Returns:
        bool: 如果用户已收藏该帖子则返回True，否则返回False
    """
    try:
        # 获取当前用户ID
        if not request.state.user:
            return False
        
        user_id = request.state.user.get("id")
        
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 检查收藏状态
        return await favorite_service.is_post_favorited(post_id, user_id)
    except Exception:
        # 如果出现任何错误，默认返回未收藏状态
        return False

@router.get("/{post_id}/comments", response_model=PostCommentResponse)
@public_endpoint(cache_ttl=60, custom_message="获取帖子评论失败")
async def read_post_comments(
    request: Request,
    post_id: int,
    skip: int = 0,
    limit: int = 100
):
    """获取帖子评论列表
    
    通过RESTful风格的API获取指定帖子下的所有评论，支持分页。
    此API端点允许游客访问，不需要身份验证。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        PostCommentResponse: 包含评论列表和总数的响应
    """
    try:
        # 使用 Service 架构
        post_service = PostService()
        comment_service = CommentService()
        
        # 首先检查帖子是否存在
        await post_service.get_post_detail(post_id)
        
        # 获取评论列表
        comments, total = await comment_service.get_comments_by_post(
            post_id=post_id, 
            skip=skip, 
            limit=limit
        )
        
        # 返回符合PostCommentResponse格式的响应
        return {
            "post_id": post_id,
            "comments": comments,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
