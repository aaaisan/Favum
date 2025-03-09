from fastapi import APIRouter, HTTPException, Request, Query, Depends
# from fastapi import APIRouter, HTTPException, status, Request, Response
from typing import List, Optional
import json
from datetime import datetime
import traceback
import logging

from ...schemas import post as post_schema
# from ...schemas import comment as comment_schema
from ...services.comment_service import CommentService
from ...core.decorators import public_endpoint, admin_endpoint
from ...services.favorite_service import FavoriteService
from ...services import PostService
from ...services.post_service import get_post_service
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
# from ..responses.comment import CommentResponse, CommentListResponse
from ...core.auth import get_current_user_optional, get_current_active_user
from ...db.models import User, VoteType
#import logging

logger = logging.getLogger(__name__)

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
    logger.debug(f"获取帖子 {post_id} 的作者ID")
    try:
        post_service = PostService()
        
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id)
        if not post:
            logger.warning(f"帖子 {post_id} 不存在")
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        author_id = post.get("author_id")
        if not author_id:
            logger.warning(f"帖子 {post_id} 的作者ID为空")
            raise HTTPException(status_code=500, detail="帖子数据不完整")
        
        logger.debug(f"帖子 {post_id} 的作者ID: {author_id}")
        return author_id
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        logger.warning(f"获取帖子 {post_id} 作者ID时发生业务异常: {str(e)}")
        raise HTTPException(
            status_code=404 if e.error_code == "post_not_found" else 400,
            detail=str(e)
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 其他未预期的异常
        logger.error(f"获取帖子 {post_id} 作者ID时发生未预期异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取帖子作者信息失败: {str(e)}"
        )

@router.post("", response_model=PostResponse)
@public_endpoint(auth_required=True, custom_message="创建帖子失败")
async def create_post(
    request: Request,
    post: post_schema.PostCreate
):
    """创建新帖子
    
    创建新的帖子记录，需要用户认证。
    
    包含以下特性：
    1. 用户认证：需要有效的访问令牌
    2. 标签处理：自动处理帖子与标签的关联
    
    Args:
        request: FastAPI请求对象
        post: 帖子创建模型，包含标题、内容、分类等
        
    Returns:
        Post: 创建成功的帖子信息
        
    Raises:
        HTTPException: 当权限不足或数据验证失败时抛出相应错误
    """
    try:
        # 创建帖子服务实例
        post_service = PostService()
        
        # 从token获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 准备帖子数据
        post_data = post.model_dump()
        
        # 如果未提供作者ID，使用当前用户ID
        if "author_id" not in post_data or not post_data["author_id"]:
            post_data["author_id"] = current_user_id
            logger.info(f"使用当前用户ID作为作者: {current_user_id}")
        
        # 使用PostService的create_post方法创建帖子，包括处理标签关联
        logger.info(f"创建帖子: {post_data.get('title')}, 标签: {post_data.get('tag_ids', [])}")
        created_post = await post_service.create_post(post_data)
        logger.info(f"成功创建帖子: {created_post.get('id')}")
        
        return created_post
    except BusinessException as e:
        # 业务异常转换为HTTP异常
        logger.error(f"业务异常: {e.message}, 状态码: {e.status_code}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
    except Exception as e:
        # 处理所有其他异常
        logger.error(f"创建帖子失败: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={"message": "创建帖子失败", "error_code": "INTERNAL_ERROR"}
        )

# @router.post("/test", response_model=PostResponse)
# @public_endpoint(rate_limit_count=10, auth_required=True, custom_message="创建测试帖子失败")
# async def create_test_post(
#     request: Request
# ):
#     """测试创建帖子
    
#     用于测试的简化版创建帖子API。
#     """
#     try:
#         # 创建帖子服务实例
#         post_service = PostService()
        
#         # 从token获取当前用户ID
#         current_user_id = request.state.user.get("id")
        
#         # 准备帖子数据
#         post_data = {
#             "title": "Test Post",
#             "content": "This is a test post",
#             "category_id": 1,
#             "section_id": 1,
#             "author_id": current_user_id
#         }
        
#         # 创建帖子
#         created_post = await post_service.create_post(post_data)
#         return created_post
#     except BusinessException as e:
#         # 业务异常转换为HTTP异常
#         raise HTTPException(
#             status_code=e.status_code,
#             detail={"message": e.message, "error_code": e.error_code}
#         )

@router.get("", response_model=PostListResponse)
async def read_posts(
    skip: int = 0,
    limit: int = 100,
    include_hidden: bool = False,
    category_id: Optional[int] = None,
    section_id: Optional[int] = None,
    author_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = Query(None),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    current_user: Optional[User] = Depends(get_current_user_optional),
    post_service: PostService = Depends(get_post_service),
):
    """
    获取帖子列表，支持分页、筛选和排序
    """
    try:
        # 获取帖子列表
        posts, total = await post_service.get_posts(
            skip=skip,
            limit=limit,
            include_hidden=include_hidden,
            category_id=category_id,
            section_id=section_id,
            author_id=author_id,
            tag_ids=tag_ids,
            sort_field=sort_field,
            sort_order=sort_order
        )
        
        # 处理帖子数据，确保结构与响应模型匹配
        processed_posts = []
        for post in posts:
            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("content", ""),
                "author_id": post.get("author_id"),
                "section_id": post.get("section_id"),
                "category_id": post.get("category_id"),
                "is_hidden": post.get("is_hidden", False),
                "created_at": str(post.get("created_at")) if post.get("created_at") else "",
                "updated_at": str(post.get("updated_at")) if post.get("updated_at") else None,
                "is_deleted": post.get("is_deleted", False),
                "vote_count": post.get("vote_count", 0)
            }
            
            # 添加分类信息
            if post.get("category"):
                processed_post["category"] = {
                    "id": post["category"].get("id"),
                    "name": post["category"].get("name"),
                    "created_at": str(post["category"].get("created_at")) if post["category"].get("created_at") else None
                }
            
            # 添加版块信息
            if post.get("section"):
                processed_post["section"] = {
                    "id": post["section"].get("id"),
                    "name": post["section"].get("name")
                }
            
            # 添加标签信息
            if post.get("tags"):
                processed_post["tags"] = []
                for tag in post["tags"]:
                    processed_post["tags"].append({
                        "id": tag.get("id"),
                        "name": tag.get("name"),
                        "created_at": str(tag.get("created_at")) if tag.get("created_at") else None
                    })
            
            processed_posts.append(processed_post)
        
        # 返回符合PostListResponse结构的数据
        return {
            "posts": processed_posts,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except Exception as e:
        error_msg = f"获取帖子列表失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 保持简单的错误返回
        raise HTTPException(
            status_code=500,
            detail={"message": "获取帖子列表失败", "error": str(e)}
        )

@router.get("/{post_id}", response_model=PostDetailResponse)
async def read_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    post_service: PostService = Depends(get_post_service),
):
    """
    获取帖子详情
    """
    try:
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id=post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 检查权限
        if post.get("is_hidden", False):
            if not current_user:
                raise HTTPException(status_code=404, detail="帖子不存在")
                
            can_view_hidden = hasattr(current_user, 'permissions') and any(
                perm in current_user.permissions for perm in ["manage_content", "manage_system"]
            )
            
            if not can_view_hidden and post.get("author_id") != current_user.id:
                raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 处理帖子数据，确保结构与响应模型匹配
        processed_post = {
            "id": post.get("id"),
            "title": post.get("title"),
            "content": post.get("content", ""),
            "author_id": post.get("author_id"),
            "section_id": post.get("section_id"),
            "category_id": post.get("category_id"),
            "is_hidden": post.get("is_hidden", False),
            "created_at": str(post.get("created_at")) if post.get("created_at") else "",
            "updated_at": str(post.get("updated_at")) if post.get("updated_at") else None,
            "is_deleted": post.get("is_deleted", False),
            "vote_count": post.get("vote_count", 0),
            "view_count": 0,  # 添加默认的查看次数
            "favorite_count": 0  # 添加默认的收藏次数
        }
        
        # 添加分类信息
        if post.get("category"):
            processed_post["category"] = {
                "id": post["category"].get("id"),
                "name": post["category"].get("name"),
                "created_at": str(post["category"].get("created_at")) if post["category"].get("created_at") else None
            }
        
        # 添加版块信息
        if post.get("section"):
            processed_post["section"] = {
                "id": post["section"].get("id"),
                "name": post["section"].get("name")
            }
        
        # 添加标签信息
        if post.get("tags"):
            processed_post["tags"] = []
            for tag in post["tags"]:
                processed_post["tags"].append({
                    "id": tag.get("id"),
                    "name": tag.get("name"),
                    "created_at": str(tag.get("created_at")) if tag.get("created_at") else None
                })
        else:
            processed_post["tags"] = []  # 确保tags字段存在
        
        # 添加作者信息（简化版）
        processed_post["author"] = {
            "id": post.get("author_id"),
            "username": "未知用户",  # 默认用户名
            "avatar_url": None,
            "role": "user"
        }
        
        return processed_post
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取帖子详情失败, post_id={post_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 保持简单的错误返回
        raise HTTPException(
            status_code=500,
            detail={"message": "获取帖子详情失败", "error": str(e)}
        )

@router.put("/{post_id}", response_model=PostResponse)
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
        # 验证用户是否已登录
        authorization = request.headers.get('Authorization')
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(
                status_code=401,
                detail="缺少有效的身份验证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = authorization.split(' ')[1]
        
        # 验证token
        from ...core.auth import decode_token
        token_data = decode_token(token)
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="令牌无效或已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 将用户信息存储在request.state中
        request.state.user = token_data
        
        # 获取当前用户ID
        current_user_id = request.state.user.get("id")
        logger.info(f"用户 {current_user_id} 正在更新帖子 {post_id}")
        
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取帖子详情，检查是否存在
        existing_post = await post_service.get_post_detail(post_id)
        if not existing_post:
            raise HTTPException(
                status_code=404,
                detail="帖子不存在"
            )
        
        # 检查权限 - 确认当前用户是帖子作者或管理员
        user_role = request.state.user.get("role", "user")
        is_author = existing_post.get("author_id") == current_user_id
        is_admin = user_role in ["admin", "moderator"]
        
        if not (is_author or is_admin):
            logger.warning(f"用户 {current_user_id} 无权限更新帖子 {post_id}")
            raise HTTPException(
                status_code=403,
                detail="没有权限更新此帖子"
            )
            
        # 更新帖子内容
        # 兼容不同版本的Pydantic，尝试使用dict()或model_dump()
        try:
            post_data = post.model_dump(exclude_unset=True)
        except AttributeError:
            try:
                post_data = post.dict(exclude_unset=True)
            except AttributeError:
                post_data = {k: v for k, v in post.__dict__.items() if not k.startswith('_')}
        
        updated_post = await post_service.update_post(post_id, post_data)
        
        # 确保日期时间字段为字符串格式
        if updated_post.get("created_at") and not isinstance(updated_post.get("created_at"), str):
            updated_post["created_at"] = updated_post["created_at"].isoformat()
            
        if updated_post.get("updated_at") and not isinstance(updated_post.get("updated_at"), str):
            updated_post["updated_at"] = updated_post["updated_at"].isoformat()
        
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
        # 记录请求信息
        with open("logs/visibility_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 请求修改帖子可见性: post_id={post_id}, visibility={visibility}\n")
        
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取帖子详情，检查是否存在
        existing_post = await post_service.get_post_detail(post_id)
        if not existing_post:
            with open("logs/visibility_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 帖子不存在: post_id={post_id}\n")
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        with open("logs/visibility_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 帖子存在, 当前状态: {existing_post.get('is_hidden')}\n")
        
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
                with open("logs/visibility_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 权限错误: user_id={user_id}, author_id={author_id}\n")
                raise HTTPException(status_code=403, detail="您只能隐藏自己的帖子")
        
        # 更新帖子可见性
        is_hidden = visibility.get("hidden", not existing_post.get("is_hidden", False))
        with open("logs/visibility_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 准备切换可见性: is_hidden={is_hidden}\n")
        
        try:
            updated_post = await post_service.toggle_visibility(post_id, is_hidden)
            
            with open("logs/visibility_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 切换成功, 返回数据: {updated_post}\n")
            
            # 确保日期字段是字符串格式
            if isinstance(updated_post, dict):
                # 格式化日期字段
                if isinstance(updated_post.get('created_at'), datetime):
                    updated_post['created_at'] = updated_post['created_at'].isoformat()
                if isinstance(updated_post.get('updated_at'), datetime):
                    updated_post['updated_at'] = updated_post['updated_at'].isoformat()
                if isinstance(updated_post.get('deleted_at'), datetime):
                    updated_post['deleted_at'] = updated_post['deleted_at'].isoformat()
                
                # 格式化嵌套对象中的日期
                if isinstance(updated_post.get('category'), dict) and isinstance(updated_post['category'].get('created_at'), datetime):
                    updated_post['category']['created_at'] = updated_post['category']['created_at'].isoformat()
            
            # 返回完整的帖子详情，而不是简单的状态消息
            return updated_post
        except Exception as e:
            with open("logs/visibility_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 切换失败, 错误: {str(e)}\n")
                f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
            raise
    except BusinessException as e:
        # 记录业务异常
        with open("logs/visibility_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 业务异常: {e.message}, {e.code}\n")
            
        # 业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.code}
        )
    except Exception as e:
        # 记录未处理异常
        with open("logs/visibility_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 未处理异常: {str(e)}\n")
            f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
            
        # 重新抛出异常
        raise

@router.post("/{post_id}/vote", response_model=PostVoteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="点赞操作失败")
async def vote_post(
    post_id: int,
    vote_data: post_schema.PostVoteCreate,
    request: Request
):
    """
    为帖子投票（赞同或反对）
    """
    try:
        # 获取当前用户信息
        current_user = request.state.user
        user_id = current_user.get("id")
        
        logger.info("开始处理投票请求", extra={
            "post_id": post_id,
            "user_id": user_id,
            "vote_type": vote_data.vote_type
        })
        
        with open("logs/vote_endpoint.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 投票请求: post_id={post_id}, user_id={user_id}, vote_type={vote_data.vote_type}\n")
        
        # 将字符串转换为枚举
        if vote_data.vote_type == "upvote":
            vote_type_enum = VoteType.UPVOTE
        elif vote_data.vote_type == "downvote":
            vote_type_enum = VoteType.DOWNVOTE
        else:
            error_msg = f"无效的投票类型: {vote_data.vote_type}"
            logger.warning(error_msg)
            with open("logs/vote_endpoint.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 错误: {error_msg}\n")
            raise HTTPException(
                status_code=400, 
                detail={"message": "无效的投票类型", "error_code": "INVALID_VOTE_TYPE"}
            )
        
        logger.info("转换投票类型", extra={
            "vote_type_str": vote_data.vote_type,
            "vote_enum": str(vote_type_enum)
        })
        
        # 创建服务实例
        post_service = PostService()
        
        try:
            vote_result = await post_service.vote_post(
                post_id=post_id,
                user_id=user_id,
                vote_type=vote_type_enum
            )
            
            if vote_result is None:
                error_msg = f"帖子不存在或已删除: post_id={post_id}"
                logger.warning(error_msg)
                with open("logs/vote_endpoint.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 错误: {error_msg}\n")
                raise HTTPException(
                    status_code=404, 
                    detail={"message": "帖子不存在或已删除", "error_code": "POST_NOT_FOUND"}
                )
            
            # 确保结果符合响应模型
            processed_result = {
                "post_id": vote_result.get("post_id"),
                "upvotes": vote_result.get("upvotes", 0),
                "downvotes": vote_result.get("downvotes", 0),
                "score": vote_result.get("score", 0),
                "user_vote": vote_result.get("user_vote"),
                "action": vote_result.get("action", "")
            }
            
            logger.info("投票成功", extra={"result": processed_result})
            with open("logs/vote_endpoint.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 投票成功: {json.dumps(processed_result, default=str)}\n")
            
            return processed_result
        except BusinessException as e:
            error_msg = f"业务异常: {e.message}"
            logger.error(error_msg)
            with open("logs/vote_endpoint.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 业务异常: {error_msg}\n")
            raise HTTPException(
                status_code=e.status_code,
                detail={"message": e.message, "error_code": e.code}
            )
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        error_msg = f"投票处理失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        with open("logs/vote_endpoint.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 未处理异常: {error_msg}\n")
            f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
        raise HTTPException(
            status_code=500,
            detail={"message": "投票处理失败", "error_code": "VOTE_FAILED"}
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
        # 记录请求信息
        with open("logs/vote_count_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 请求获取帖子投票数: post_id={post_id}\n")
        
        # 创建帖子服务实例
        post_service = PostService()
        
        # 获取点赞数
        try:
            count = await post_service.get_vote_count(post_id)
            
            # 记录成功结果
            with open("logs/vote_count_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 获取投票数成功: post_id={post_id}, count={count}\n")
            
            return {
                "post_id": post_id,
                "vote_count": count
            }
        except Exception as e:
            # 记录服务层异常
            with open("logs/vote_count_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 服务层异常: {str(e)}\n")
                f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
            
            # 返回默认值
            return {
                "post_id": post_id,
                "vote_count": 0
            }
            
    except BusinessException as e:
        # 记录业务异常
        with open("logs/vote_count_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 业务异常: {e.message}, {e.code}\n")
            
        # 将业务异常转换为HTTP异常
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.code}
        )
    except Exception as e:
        # 记录未处理异常
        with open("logs/vote_count_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 未处理异常: {str(e)}\n")
            f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
            
        # 返回通用错误
        raise HTTPException(
            status_code=500,
            detail={"message": "获取投票数失败", "error_code": "GET_VOTES_FAILED"}
        )

@router.post("/{post_id}/favorite", response_model=PostFavoriteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="收藏操作失败")
async def favorite_post(
    post_id: int,
    request: Request
):
    """
    收藏帖子
    """
    try:
        # 获取当前用户信息
        current_user = request.state.user
        user_id = current_user.get("id")
        
        logger.info(f"用户 {user_id} 尝试收藏帖子 {post_id}")
        with open("logs/favorite_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 收藏请求: user_id={user_id}, post_id={post_id}\n")
        
        # 创建服务实例
        post_service = PostService()
        
        try:
            result = await post_service.favorite_post(post_id=post_id, user_id=user_id)
            
            logger.info(f"收藏帖子成功: {result}")
            with open("logs/favorite_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 收藏成功: {json.dumps(result, default=str)}\n")
            
            return result
        except BusinessException as e:
            error_msg = f"业务异常: {e.message}"
            logger.error(error_msg)
            with open("logs/favorite_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 业务异常: {error_msg}\n")
            raise HTTPException(
                status_code=e.status_code,
                detail={"message": e.message, "error_code": e.error_code}
            )
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        error_msg = f"收藏帖子失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        with open("logs/favorite_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 未处理异常: {error_msg}\n")
            f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
        raise HTTPException(
            status_code=500,
            detail={"message": "收藏帖子失败", "error_code": "FAVORITE_FAILED"}
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
        
        # 格式化返回结果
        return {
            "post_id": post_id,
            "user_id": user_id,
            "status": "unfavorited",
            "favorite_id": None,
            "created_at": None
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{post_id}/favorite/status", response_model=bool)
@public_endpoint(auth_required=True, cache_ttl=10, custom_message="获取收藏状态失败")
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
        if not hasattr(request.state, 'user') or not request.state.user:
            with open("logs/favorite_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 用户未登录或token无效, post_id={post_id}\n")
            return False
        
        user_id = request.state.user.get("id")
        if not user_id:
            with open("logs/favorite_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 无法获取用户ID, post_id={post_id}\n")
            return False
            
        # 记录查询请求
        with open("logs/favorite_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 查询收藏状态: post_id={post_id}, user_id={user_id}\n")
        
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 检查收藏状态
        is_favorited = await favorite_service.is_post_favorited(post_id, user_id)
        
        with open("logs/favorite_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 查询结果: post_id={post_id}, user_id={user_id}, is_favorited={is_favorited}\n")
            
        return is_favorited
    except Exception as e:
        # 记录错误
        with open("logs/favorite_debug.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - 查询收藏状态异常: {str(e)}, post_id={post_id}\n")
            f.write(f"{datetime.now().isoformat()} - 堆栈: {traceback.format_exc()}\n")
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
        
        # 处理评论数据
        processed_comments = []
        for comment in comments:
            # 如果有日期时间字段，转换为字符串
            if isinstance(comment, dict):
                if "created_at" in comment and comment["created_at"]:
                    comment["created_at"] = str(comment["created_at"])
                if "updated_at" in comment and comment["updated_at"]:
                    comment["updated_at"] = str(comment["updated_at"])
                processed_comments.append(comment)
            else:
                # 如果评论不是字典，直接添加
                processed_comments.append(comment)
        
        # 返回符合PostCommentResponse格式的响应
        return {
            "post_id": post_id,
            "comments": processed_comments,
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

@router.get("/debug-test", response_model=None)
async def test_endpoint():
    """
    测试端点，返回简单的数据
    """
    return {"message": "测试成功", "status": "ok"}
