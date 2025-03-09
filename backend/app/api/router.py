from fastapi import APIRouter, Depends
from .endpoints import users, posts, comments, auth, sections, categories, tags, captcha  # , tasks
from ..core.config import settings
from ..services.post_service import PostService, get_post_service

api_router = APIRouter()

# 添加API根路由
@api_router.get("")
async def api_root():
    """API根路径处理函数"""
    return {
        "message": "论坛API",
        "version": settings.VERSION,
        "status": "运行中"
    }

# 添加一个简单的测试路由
@api_router.get("/test", response_model=None)
async def test_endpoint():
    """
    测试端点，返回简单的数据
    """
    return {"message": "测试成功", "status": "ok"}

# 添加一个简单的帖子列表测试路由
@api_router.get("/posts-test", response_model=None)
async def posts_test_endpoint(
    skip: int = 0,
    limit: int = 5,
    post_service: PostService = Depends(get_post_service)
):
    """
    帖子列表测试端点
    """
    try:
        # 获取帖子列表
        posts, total = await post_service.get_posts(skip=skip, limit=limit)
        
        # 简化帖子数据
        simplified_posts = []
        for post in posts:
            simplified_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("content", "")[:50],  # 只返回内容的前50个字符
                "author_id": post.get("author_id")
            }
            simplified_posts.append(simplified_post)
        
        return {
            "message": "获取帖子列表成功",
            "total": total,
            "posts": simplified_posts
        }
    except Exception as e:
        return {
            "message": "获取帖子列表失败",
            "error": str(e)
        }

# 注册认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 注册其他路由
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(captcha.router, prefix="/captcha", tags=["captcha"])
# api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
