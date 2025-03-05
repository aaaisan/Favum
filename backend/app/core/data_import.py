from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from app import crud, models, schemas
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
        保存的帖子对象，如果失败则返回None
    """
    # 处理用户ID
    user_id = None
    if "userId" in post_data:
        if username_map and post_data["userId"] in username_map:
            user_id = username_map[post_data["userId"]]
        else:
            # 查找用户
            user = await crud.user.get(db, id=post_data["userId"])
            if user:
                user_id = user.id
    
    if not user_id:
        # 如果没有找到有效的用户ID，使用第一个管理员用户
        admin_user = await crud.user.get_first_by_role(db, role="admin")
        if admin_user:
            user_id = admin_user.id
        else:
            # 查找任何用户
            any_user = await crud.user.get_first(db)
            if any_user:
                user_id = any_user.id
            else:
                return None  # 没有用户，无法创建帖子
    
    # 处理分类ID
    category_id = None
    if "categoryId" in post_data:
        if category_map and post_data["categoryId"] in category_map:
            category_id = category_map[post_data["categoryId"]]
        else:
            # 查找分类
            category = await crud.category.get(db, id=post_data["categoryId"])
            if category:
                category_id = category.id
    
    if not category_id:
        # 如果没有找到有效的分类ID，尝试使用'技术讨论'分类
        tech_category = await crud.category.get_by_name(db, name="技术讨论")
        if tech_category:
            category_id = tech_category.id
        else:
            # 使用第一个可用分类
            first_category = await crud.category.get_first(db)
            if first_category:
                category_id = first_category.id
    
    # 处理标签
    tag_ids = []
    if "tags" in post_data and isinstance(post_data["tags"], list):
        for tag_item in post_data["tags"]:
            tag_id = None
            if isinstance(tag_item, int):
                # 如果是ID
                tag_id = tag_item
            elif isinstance(tag_item, dict) and "id" in tag_item:
                # 如果是对象带ID
                tag_id = tag_item["id"]
            elif isinstance(tag_item, dict) and "name" in tag_item:
                # 如果是对象带名称
                tag_name = tag_item["name"]
                if tag_map and tag_name in tag_map:
                    tag_id = tag_map[tag_name]
                else:
                    tag = await crud.tag.get_by_name(db, name=tag_name)
                    if tag:
                        tag_id = tag.id
                    else:
                        # 创建新标签
                        new_tag = await crud.tag.create(db, obj_in=schemas.TagCreate(name=tag_name))
                        tag_id = new_tag.id
                        if tag_map is not None:
                            tag_map[tag_name] = tag_id
            
            if tag_id:
                tag_ids.append(tag_id)
    
    # 创建帖子对象
    post_in = schemas.PostCreate(
        title=post_data.get("title", "无标题"),
        content=post_data.get("content", ""),
        user_id=user_id,
        category_id=category_id,
        tag_ids=tag_ids,
        view_count=post_data.get("view_count", 0),
        vote_count=post_data.get("vote_count", 0),
        comment_count=post_data.get("comment_count", 0),
        is_sticky=post_data.get("is_sticky", False),
        is_hidden=post_data.get("is_hidden", False)
    )
    
    # 创建帖子
    try:
        created_post = await crud.post.create_with_tags(db, obj_in=post_in)
        
        # 如果有创建时间，更新它
        if "created_at" in post_data and post_data["created_at"]:
            try:
                created_at = post_data["created_at"]
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                await db.execute(
                    f"UPDATE posts SET created_at = '{created_at}' WHERE id = {created_post.id}"
                )
                await db.commit()
            except Exception as e:
                print(f"更新创建时间失败: {e}")
        
        return created_post
    except Exception as e:
        print(f"创建帖子失败: {e}")
        return None

async def process_frontend_comment_data(
    db: AsyncSession,
    comment_data: Dict[str, Any],
    post_id_map: Dict[int, int] = None,
    username_map: Dict[str, int] = None
) -> Optional[models.Comment]:
    """
    处理来自前端的评论数据，将其转换为后端数据结构并保存到数据库
    
    Args:
        db: 数据库会话
        comment_data: 前端评论数据
        post_id_map: 前端帖子ID到后端帖子ID的映射
        username_map: 用户名到用户ID的映射
    
    Returns:
        保存的评论对象，如果失败则返回None
    """
    # 处理帖子ID
    post_id = None
    if "postId" in comment_data:
        frontend_post_id = comment_data["postId"]
        if post_id_map and frontend_post_id in post_id_map:
            post_id = post_id_map[frontend_post_id]
        else:
            # 直接使用ID查找
            post = await crud.post.get(db, id=frontend_post_id)
            if post:
                post_id = post.id
    
    if not post_id:
        return None  # 没有帖子ID，无法创建评论
    
    # 处理用户ID
    user_id = None
    if "userId" in comment_data:
        user_id_or_name = comment_data["userId"]
        if isinstance(user_id_or_name, str) and username_map and user_id_or_name in username_map:
            user_id = username_map[user_id_or_name]
        else:
            # 查找用户
            user = await crud.user.get(db, id=user_id_or_name)
            if user:
                user_id = user.id
    
    if not user_id:
        # 如果没有找到有效的用户ID，使用第一个用户
        any_user = await crud.user.get_first(db)
        if any_user:
            user_id = any_user.id
        else:
            return None  # 没有用户，无法创建评论
    
    # 处理父评论ID
    parent_id = comment_data.get("parent_id", None)
    if parent_id:
        # 验证父评论是否存在
        parent_comment = await crud.comment.get(db, id=parent_id)
        if not parent_comment:
            parent_id = None
    
    # 创建评论对象
    comment_in = schemas.CommentCreate(
        content=comment_data.get("content", ""),
        user_id=user_id,
        post_id=post_id,
        parent_id=parent_id
    )
    
    # 创建评论
    try:
        created_comment = await crud.comment.create(db, obj_in=comment_in)
        
        # 如果有点赞数，更新它
        if "likes" in comment_data and isinstance(comment_data["likes"], int):
            await db.execute(
                f"UPDATE comments SET likes = {comment_data['likes']} WHERE id = {created_comment.id}"
            )
            await db.commit()
        
        # 更新帖子的评论计数
        await db.execute(
            f"UPDATE posts SET comment_count = comment_count + 1 WHERE id = {post_id}"
        )
        await db.commit()
        
        return created_comment
    except Exception as e:
        print(f"创建评论失败: {e}")
        return None 