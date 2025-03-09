from typing import Dict, Optional, Any, Union
# from typing import Dict, List, Optional, Any, Union
from app.services.user_service import UserService
from app.services.category_service import CategoryService
from app.services.tag_service import TagService
from app.services.post_service import PostService
from app.services.comment_service import CommentService
from app import models
from app import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession

async def process_frontend_post_data(
    db: AsyncSession,
    post_data: Dict[str, Any],
    username_map: Dict[str, int] = None,
    category_map: Dict[str, int] = None,
    tag_map: Dict[str, int] = None
) -> Optional[models.Post]:
    """
    处理来自前端的帖子数据，将其转换为后端数据结构并保存到数据库
    
    Args:
        db: 数据库会话
        post_data: 前端帖子数据
        username_map: 用户名到用户ID的映射
        category_map: 分类名到分类ID的映射
        tag_map: 标签名到标签ID的映射
        
    Returns:
        Optional[models.Post]: 创建的帖子对象，如果失败则返回None
    """
    # 初始化服务
    user_service = UserService()
    category_service = CategoryService()
    tag_service = TagService()
    post_service = PostService()
    
    # 处理用户ID
    user_id = None
    if username_map and post_data["userId"] in username_map:
        user_id = username_map[post_data["userId"]]
    else:
        # 查找用户
        user = await user_service.get_user_by_id(post_data["userId"])
        if user:
            user_id = user["id"]
    
    if not user_id:
        # 如果没有找到有效的用户ID，使用第一个管理员用户
        admin_user = await user_service.get_first_admin_user()
        if admin_user:
            user_id = admin_user["id"]
        else:
            # 查找任何用户
            any_user = await user_service.get_first_user()
            if any_user:
                user_id = any_user["id"]
            else:
                return None  # 没有用户，无法创建帖子
    
    # 处理分类ID
    category_id = None
    if "categoryId" in post_data:
        if category_map and post_data["categoryId"] in category_map:
            category_id = category_map[post_data["categoryId"]]
        else:
            # 查找分类
            try:
                category = await category_service.get_category_detail(post_data["categoryId"])
                if category:
                    category_id = category["id"]
            except:
                pass
    
    if not category_id:
        # 如果没有找到有效的分类ID，尝试使用'技术讨论'分类
        try:
            tech_category = await category_service.get_category_by_name("技术讨论")
            if tech_category:
                category_id = tech_category["id"]
        except:
            # 使用第一个可用分类
            first_category = await category_service.get_first_category()
            if first_category:
                category_id = first_category["id"]
    
    # 如果还是没有分类ID，则无法创建帖子
    if not category_id:
        return None
    
    # 处理标签
    tag_ids = []
    if "tags" in post_data and post_data["tags"]:
        for tag_name in post_data["tags"]:
            # 先从映射中查找
            if tag_map and tag_name in tag_map:
                tag_ids.append(tag_map[tag_name])
                continue
                
            # 尝试从数据库查找
            try:
                tag = await tag_service.get_tag_by_name(tag_name)
                if tag:
                    tag_ids.append(tag["id"])
                    continue
            except:
                pass
                
            # 如果标签不存在，创建新标签
            try:
                new_tag = await tag_service.create_tag({"name": tag_name})
                tag_ids.append(new_tag["id"])
            except:
                pass
    
    # 创建帖子
    post_data_copy = post_data.copy()
    
    # 转换字段
    post_create_data = {
        "title": post_data_copy.get("title", ""),
        "content": post_data_copy.get("content", ""),
        "user_id": user_id,
        "category_id": category_id,
        "tags": tag_ids,
        "is_pinned": post_data_copy.get("is_pinned", False),
        "visibility": post_data_copy.get("visibility", "public")
    }
    
    # 创建帖子
    try:
        created_post = await post_service.create_post(post_create_data, user_id)
        return created_post
    except Exception as e:
        print(f"创建帖子失败: {str(e)}")
        return None

async def process_frontend_comment_data(
    db: AsyncSession,
    comment_data: Dict[str, Any],
    frontend_post_id: int,
    backend_post_map: Dict[int, int] = None,
    username_map: Dict[str, int] = None,
    parent_id_map: Dict[int, int] = None
) -> Optional[models.Comment]:
    """
    处理来自前端的评论数据，将其转换为后端数据结构并保存到数据库
    
    Args:
        db: 数据库会话
        comment_data: 前端评论数据
        frontend_post_id: 前端帖子ID
        backend_post_map: 前端帖子ID到后端帖子ID的映射
        username_map: 用户名到用户ID的映射
        parent_id_map: 前端评论ID到后端评论ID的映射
        
    Returns:
        Optional[models.Comment]: 创建的评论对象，如果失败则返回None
    """
    # 初始化服务
    user_service = UserService()
    post_service = PostService()
    comment_service = CommentService()
    
    # 获取帖子ID
    post_id = None
    if backend_post_map and frontend_post_id in backend_post_map:
        post_id = backend_post_map[frontend_post_id]
    else:
        try:
            post = await post_service.get_post_detail(frontend_post_id)
            if post:
                post_id = post["id"]
        except:
            pass
    
    if not post_id:
        return None  # 没有找到对应的帖子
    
    # 处理用户ID
    user_id = None
    user_id_or_name = comment_data.get("userId") or comment_data.get("username")
    
    # 先查映射表
    if username_map and user_id_or_name in username_map:
        user_id = username_map[user_id_or_name]
    else:
        # 尝试直接按ID查找
        try:
            user = await user_service.get_user_by_id(user_id_or_name)
            if user:
                user_id = user["id"]
        except:
            # 使用任何有效用户
            try:
                any_user = await user_service.get_first_user()
                if any_user:
                    user_id = any_user["id"]
            except:
                pass
    
    if not user_id:
        return None  # 没有找到有效的用户
    
    # 处理父评论ID
    parent_id = None
    frontend_parent_id = comment_data.get("parentId")
    if frontend_parent_id and parent_id_map and frontend_parent_id in parent_id_map:
        parent_id = parent_id_map[frontend_parent_id]
    
    # 创建评论
    comment_create_data = {
        "content": comment_data.get("content", ""),
        "user_id": user_id,
        "post_id": post_id,
        "parent_id": parent_id
    }
    
    try:
        created_comment = await comment_service.create_comment(comment_create_data, user_id)
        return created_comment
    except Exception as e:
        print(f"创建评论失败: {str(e)}")
        return None 