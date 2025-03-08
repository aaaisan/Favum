from typing import Optional
from typing import List, Optional
from ..core.celery_config import celery_app
from ..db.database import SessionLocal
from ..db.models import User, Post, Comment
from ..core.cache import CacheManager

@celery_app.task(
    name="send_notification",
    queue="notification",
)
def send_notification(
    user_id: int,
    title: str,
    content: str,
    notification_type: str,
    related_id: Optional[int] = None
) -> None:
    """发送通知"""
    # 在实际应用中，这里可以集成推送服务
    # 比如：WebSocket、Firebase Cloud Messaging等
    cache_key = f"notification:{user_id}"
    notifications = CacheManager.get(cache_key) or []
    notifications.append({
        "title": title,
        "content": content,
        "type": notification_type,
        "related_id": related_id,
        "is_read": False
    })
    CacheManager.set(cache_key, notifications, 86400)  # 24小时过期

@celery_app.task(
    name="notify_new_comment",
    queue="notification",
)
def notify_new_comment(comment_id: int) -> None:
    """新评论通知"""
    db = SessionLocal()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return
        
        # 通知帖子作者
        send_notification.delay(
            user_id=comment.post.author_id,
            title="新评论提醒",
            content=f"你的帖子《{comment.post.title}》收到了新评论",
            notification_type="new_comment",
            related_id=comment_id
        )
    finally:
        db.close()

@celery_app.task(
    name="notify_post_liked",
    queue="notification",
)
def notify_post_liked(post_id: int, user_id: int) -> None:
    """帖子点赞通知"""
    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not post or not user:
            return
        
        send_notification.delay(
            user_id=post.author_id,
            title="点赞提醒",
            content=f"{user.username} 点赞了你的帖子《{post.title}》",
            notification_type="post_liked",
            related_id=post_id
        )
    finally:
        db.close() 