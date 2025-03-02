from fastapi import APIRouter
from .endpoints import users, posts, comments, auth, sections, categories, tags, captcha  # , tasks

api_router = APIRouter()

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
