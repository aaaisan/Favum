"""
Celery配置模块

配置异步任务处理系统，包括：
- 任务队列设置
- 结果后端配置
- 任务路由规则
- 执行超时限制
- 定时任务计划
- 工作进程参数

使用Redis作为消息代理和结果后端。
支持多个专用队列（邮件、通知等）。
包含内置的定时维护任务。
"""

from celery import Celery
from .config import settings

# 创建Celery实例
celery_app = Celery(
    "forum",  # 应用名称
    broker=settings.CELERY_BROKER_URL,  # 消息代理URL
    backend=settings.CELERY_RESULT_BACKEND  # 结果后端URL
)

# 配置Celery
celery_app.conf.update(
    # 任务序列化配置
    task_serializer="json",  # 任务序列化格式
    accept_content=["json"],  # 允许的内容类型
    result_serializer="json",  # 结果序列化格式
    timezone="Asia/Shanghai",  # 时区设置
    enable_utc=True,  # 启用UTC时间
    
    # 任务队列配置
    # 为不同类型的任务定义专门的队列
    task_queues={
        "default": {  # 默认队列
            "exchange": "default",
            "routing_key": "default",
        },
        "email": {  # 邮件任务队列
            "exchange": "email",
            "routing_key": "email",
        },
        "notification": {  # 通知任务队列
            "exchange": "notification",
            "routing_key": "notification",
        },
    },
    
    # 任务路由配置
    # 根据任务名称将任务分配到相应的队列
    task_routes={
        "app.tasks.email.*": {"queue": "email"},  # 所有邮件任务
        "app.tasks.notification.*": {"queue": "notification"},  # 所有通知任务
    },
    
    # 任务执行超时配置
    task_time_limit=30 * 60,  # 硬超时限制：30分钟
    task_soft_time_limit=25 * 60,  # 软超时限制：25分钟（允许优雅关闭）
    
    # 任务结果配置
    task_ignore_result=False,  # 保存任务结果
    result_expires=24 * 60 * 60,  # 结果过期时间：24小时
    
    # 工作进程配置
    worker_prefetch_multiplier=1,  # 每次预取一个任务
    worker_max_tasks_per_child=1000,  # 子进程最大执行任务数
    
    # 定时任务计划
    # 使用Celery Beat进行调度
    beat_schedule={
        "cleanup-expired-tokens": {  # 清理过期令牌
            "task": "app.tasks.maintenance.cleanup_expired_tokens",
            "schedule": 60 * 60,  # 执行间隔：每小时
        },
        "update-post-stats": {  # 更新帖子统计信息
            "task": "app.tasks.maintenance.update_post_stats",
            "schedule": 30 * 60,  # 执行间隔：每30分钟
        },
    }
)

# 自动发现任务定义
# 扫描指定包中的所有任务装饰器
celery_app.autodiscover_tasks([
    "app.tasks.email",  # 邮件相关任务
    "app.tasks.notification",  # 通知相关任务
    "app.tasks.maintenance"  # 维护相关任务
]) 