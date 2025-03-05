from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.security import get_current_superuser
from app.db.session import get_db
from app.schemas import StatusMsg
from app.scripts.seed_forum_data import seed_forum_data

router = APIRouter()

@router.post("/seed-forum-data", response_model=StatusMsg)
async def import_forum_seed_data(
    background_tasks: BackgroundTasks,
    clear_existing: bool = False,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(get_current_superuser)
) -> Any:
    """
    导入论坛种子数据，包括用户、分类、标签、帖子和评论。
    
    - **clear_existing**: 是否先清除现有数据
    
    注意：该操作仅限超级管理员。
    """
    # 后台运行数据导入任务
    background_tasks.add_task(seed_forum_data, db, clear_existing)
    
    return {
        "status": "success",
        "message": "论坛种子数据导入任务已启动，请稍后检查结果"
    }

@router.get("/clear-forum-data", response_model=StatusMsg)
async def clear_forum_data(
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(get_current_superuser)
) -> Any:
    """
    清除所有论坛数据（用户、分类、标签、帖子和评论）。
    
    注意：该操作仅限超级管理员，且操作不可逆，请谨慎使用！
    """
    try:
        # 按依赖关系的反向顺序删除数据
        await db.execute("DELETE FROM post_tags")
        await db.execute("DELETE FROM comments")
        await db.execute("DELETE FROM posts")
        await db.execute("DELETE FROM tags")
        await db.execute("DELETE FROM categories")
        
        # 注意：不删除用户表以保留管理员账户
        # 如果需要删除所有非管理员用户：
        # await db.execute("DELETE FROM users WHERE role != 'admin'")
        
        await db.commit()
        
        return {
            "status": "success",
            "message": "所有论坛数据已清除"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"清除数据时出错：{str(e)}"
        ) 