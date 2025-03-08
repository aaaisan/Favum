from typing import Any, Callable, Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import logging

from ..core.logging import get_logger
from ..core.decorators.error import handle_exceptions, retry
from ..core.decorators.logging import log_execution_time
from ..core.decorators.logging import log_execution_time, log_exception
# 注释掉不存在的模块导入
# from ..core.profiling import Profiler

logger = get_logger(__name__)

class BackgroundTask:
    """后台任务"""
    
    def __init__(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        interval: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.interval = interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.retries = 0
        self.is_running = False
        self.total_runs = 0
        self.success_runs = 0
        self.failed_runs = 0
        self.total_execution_time = 0.0
        self.profiler = Profiler()
    
    @handle_exceptions(Exception, include_details=True)
    @log_execution_time(level=logging.INFO)
    async def execute(self) -> Any:
        """执行任务"""
        self.is_running = True
        self.last_run = datetime.now()
        self.total_runs += 1
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            with self.profiler.time_tracker(self.func.__name__), \
                 self.profiler.memory_tracker(self.func.__name__):
                
                if asyncio.iscoroutinefunction(self.func):
                    result = await self.func(*self.args, **self.kwargs)
                else:
                    result = self.func(*self.args, **self.kwargs)
            
            self.success_runs += 1
            self.retries = 0
            if self.interval:
                self.next_run = datetime.now() + timedelta(seconds=self.interval)
            
            return result
            
        except Exception as e:
            self.failed_runs += 1
            logger.error(
                f"任务执行失败: {str(e)}",
                extra={
                    "function": self.func.__name__,
                    "args": self.args,
                    "kwargs": self.kwargs,
                    "retries": self.retries,
                    "memory_usage": self.profiler.get_memory_usage(),
                    "cpu_usage": self.profiler.get_cpu_usage()
                }
            )
            
            if self.retries < self.max_retries:
                self.retries += 1
                self.next_run = datetime.now() + timedelta(seconds=self.retry_delay)
            else:
                logger.error(f"任务重试次数超过限制: {self.func.__name__}")
            
            raise
        finally:
            end_time = asyncio.get_event_loop().time()
            self.total_execution_time += (end_time - start_time)
            self.is_running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            "total_runs": self.total_runs,
            "success_runs": self.success_runs,
            "failed_runs": self.failed_runs,
            "success_rate": (self.success_runs / self.total_runs * 100) if self.total_runs > 0 else 0,
            "average_execution_time": self.total_execution_time / self.total_runs if self.total_runs > 0 else 0,
            "memory_usage": self.profiler.get_memory_usage(),
            "cpu_usage": self.profiler.get_cpu_usage()
        }

class BackgroundWorker:
    """后台工作器"""
    
    def __init__(self, max_workers: int = 10):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self._lock = threading.Lock()
        self.profiler = Profiler()
        self.start_time = datetime.now()
    
    @handle_exceptions(Exception, include_details=True)
    @log_execution_time(level=logging.INFO)
    async def add_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        interval: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> None:
        """添加任务"""
        with self._lock:
            if name in self.tasks:
                raise ValueError(f"任务已存在: {name}")
            
            task = BackgroundTask(
                func=func,
                args=args,
                kwargs=kwargs,
                interval=interval,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            
            self.tasks[name] = task
            if interval:
                task.next_run = datetime.now() + timedelta(seconds=interval)
                self.task_queue.put((task.next_run, name))
    
    def remove_task(self, name: str) -> None:
        """移除任务"""
        with self._lock:
            if name in self.tasks:
                del self.tasks[name]
    
    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(name)
        if task:
            status = {
                "name": name,
                "is_running": task.is_running,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "retries": task.retries,
                "interval": task.interval
            }
            status.update(task.get_stats())
            return status
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [
            self.get_task_status(name)
            for name in self.tasks
        ]
    
    @retry(max_retries=3, delay=1, backoff=True)
    async def _run_task(self, name: str) -> None:
        """运行任务"""
        task = self.tasks.get(name)
        if task and not task.is_running:
            try:
                await task.execute()
            except Exception:
                pass  # 错误已在任务执行时记录
    
    @log_execution_time(level=logging.INFO)
    async def _worker(self) -> None:
        """工作器循环"""
        while self.running:
            try:
                # 检查是否有需要执行的任务
                now = datetime.now()
                while not self.task_queue.empty():
                    next_run, name = self.task_queue.get()
                    if next_run > now:
                        self.task_queue.put((next_run, name))
                        break
                    
                    task = self.tasks.get(name)
                    if task and not task.is_running:
                        await self._run_task(name)
                        if task.interval:
                            task.next_run = now + timedelta(seconds=task.interval)
                            self.task_queue.put((task.next_run, name))
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"工作器循环出错: {str(e)}")
    
    def start(self) -> None:
        """启动工作器"""
        if not self.running:
            self.running = True
            asyncio.create_task(self._worker())
    
    def stop(self) -> None:
        """停止工作器"""
        self.running = False

    def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作器统计信息"""
        total_tasks = len(self.tasks)
        running_tasks = sum(1 for task in self.tasks.values() if task.is_running)
        total_runs = sum(task.total_runs for task in self.tasks.values())
        total_failures = sum(task.failed_runs for task in self.tasks.values())
        
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds() / 3600,  # 小时
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "queued_tasks": self.task_queue.qsize(),
            "total_runs": total_runs,
            "total_failures": total_failures,
            "success_rate": ((total_runs - total_failures) / total_runs * 100) if total_runs > 0 else 0,
            "memory_usage": self.profiler.get_memory_usage(),
            "cpu_usage": self.profiler.get_cpu_usage()
        }

def background_task(
    name: str,
    interval: Optional[int] = None,
    max_retries: int = 3,
    retry_delay: int = 5
):
    """后台任务装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            worker = BackgroundWorker()
            worker.add_task(
                name=name,
                func=func,
                args=args,
                kwargs=kwargs,
                interval=interval,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            return await worker._run_task(name)
        return wrapper
    return decorator

# 创建后台工作器实例
worker = BackgroundWorker() 