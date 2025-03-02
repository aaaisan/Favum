from typing import Any, Callable, Dict, Optional
from time import time
from functools import wraps
import tracemalloc
from contextlib import contextmanager
import psutil
import os
from datetime import datetime

from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)

class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self._process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        memory = self._process.memory_info()
        return {
            "rss": memory.rss / 1024 / 1024,  # MB
            "vms": memory.vms / 1024 / 1024,  # MB
            "percent": self._process.memory_percent()
        }
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用情况"""
        return self._process.cpu_percent(interval=0.1)
    
    @contextmanager
    def memory_tracker(self, name: str):
        """内存追踪上下文管理器"""
        tracemalloc.start()
        start_snapshot = tracemalloc.take_snapshot()
        
        try:
            yield
        finally:
            end_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            stats = end_snapshot.compare_to(start_snapshot, 'lineno')
            total = sum(stat.size_diff for stat in stats)
            
            if total > settings.MEMORY_THRESHOLD:
                logger.warning(
                    f"内存使用超过阈值",
                    extra={
                        "operation": name,
                        "memory_diff": total / 1024,  # KB
                        "top_stats": [
                            (
                                stat.traceback.format()[-1],
                                stat.size_diff / 1024
                            )
                            for stat in stats[:3]
                        ]
                    }
                )
    
    @contextmanager
    def time_tracker(self, name: str):
        """时间追踪上下文管理器"""
        start_time = time()
        start_cpu = self._process.cpu_percent()
        
        try:
            yield
        finally:
            end_time = time()
            end_cpu = self._process.cpu_percent()
            
            duration = end_time - start_time
            if duration > settings.SLOW_API_THRESHOLD:
                logger.warning(
                    f"操作执行时间过长",
                    extra={
                        "operation": name,
                        "duration": f"{duration:.3f}s",
                        "cpu_usage": f"{end_cpu - start_cpu:.1f}%"
                    }
                )

class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.profiler = Profiler()
        self._start_time = datetime.now()
    
    def get_uptime(self) -> float:
        """获取运行时间（小时）"""
        return (datetime.now() - self._start_time).total_seconds() / 3600
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        memory = self.profiler.get_memory_usage()
        return {
            "uptime": self.get_uptime(),
            "memory": memory,
            "cpu": self.profiler.get_cpu_usage(),
            "timestamp": datetime.now().isoformat()
        }

def profile_performance(name: Optional[str] = None):
    """性能分析装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation_name = name or func.__name__
            profiler = Profiler()
            
            with profiler.time_tracker(operation_name), \
                 profiler.memory_tracker(operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

# 创建性能指标收集器实例
metrics = PerformanceMetrics() 