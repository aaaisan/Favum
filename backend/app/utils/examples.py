"""
示例模块

提供使用各种装饰器和工具的示例代码。
"""

import math
import time
from typing import Dict, List, Optional

from ..core.decorators import (
    memo, 
    async_memo, 
    timed_memo, 
    typed_memo
)

#
# 基本内存缓存示例
#
@memo(maxsize=128)
def fibonacci(n: int) -> int:
    """
    计算斐波那契数列第n项（递归版本）
    
    使用内存缓存优化重复计算，避免指数级时间复杂度。
    
    Args:
        n: 位置索引
        
    Returns:
        第n个斐波那契数
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def fibonacci_demo():
    """演示基本内存缓存的效果"""
    # 不使用缓存的版本（只用于对比，实际会非常慢）
    def fib_nocache(n):
        if n <= 1:
            return n
        return fib_nocache(n-1) + fib_nocache(n-2)
    
    # 使用缓存版本
    print("计算斐波那契数列第30项")
    
    start = time.time()
    result = fibonacci(30)
    cached_time = time.time() - start
    print(f"使用缓存: 结果={result}, 耗时={cached_time:.6f}秒")
    
    # 查看缓存统计
    cache_info = fibonacci.cache_info()
    print(f"缓存统计: {cache_info}")
    
    # 再次调用（应该直接从缓存返回）
    start = time.time()
    result = fibonacci(30)
    second_time = time.time() - start
    print(f"再次调用: 结果={result}, 耗时={second_time:.6f}秒")
    
    # 清除缓存
    fibonacci.cache_clear()
    print("缓存已清除")
    
    # 清除后再次调用
    start = time.time()
    result = fibonacci(30)
    after_clear_time = time.time() - start
    print(f"清除后调用: 结果={result}, 耗时={after_clear_time:.6f}秒")
    
    print(f"缓存统计: {fibonacci.cache_info()}")

#
# 异步函数缓存示例
#
@async_memo(maxsize=100)
async def fetch_user_profile(user_id: int) -> Dict:
    """
    获取用户资料（模拟异步API调用）
    
    使用异步缓存装饰器优化重复API请求。
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户资料字典
    """
    # 模拟API延迟
    await time.sleep(1.0)
    
    # 模拟数据
    return {
        "id": user_id,
        "name": f"用户{user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": "2023-01-01T00:00:00Z"
    }

#
# 带过期时间的缓存示例
#
@timed_memo(ttl=60)  # 缓存1分钟
def get_user_count() -> int:
    """
    获取系统用户数量（模拟昂贵的数据库查询）
    
    使用带过期时间的缓存装饰器，确保数据每分钟更新一次。
    
    Returns:
        用户数量
    """
    # 模拟耗时查询
    time.sleep(0.5)
    
    # 模拟数据
    return 12345

#
# 类型敏感缓存示例
#
@typed_memo()
def calculate_area(radius: float) -> float:
    """
    计算圆的面积
    
    使用类型敏感的缓存，确保不同类型的参数使用不同的缓存。
    
    Args:
        radius: 圆的半径
        
    Returns:
        圆的面积
    """
    print(f"计算半径为{radius}的圆面积")
    return math.pi * radius * radius

def typed_cache_demo():
    """演示类型敏感缓存的效果"""
    # 使用整数调用
    area1 = calculate_area(5)
    print(f"半径5的圆面积: {area1}")
    
    # 使用相同值的浮点数调用
    area2 = calculate_area(5.0)
    print(f"半径5.0的圆面积: {area2}")
    
    # 查看缓存统计
    print(f"缓存统计: {calculate_area.cache_info()}")

#
# 复杂计算缓存示例
#
@memo(maxsize=256)
def prime_factors(n: int) -> List[int]:
    """
    计算一个数的所有质因数
    
    使用内存缓存优化重复计算。
    
    Args:
        n: 要分解的数
        
    Returns:
        所有质因数的列表
    """
    print(f"计算{n}的质因数分解")
    
    factors = []
    d = 2
    
    while n > 1:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
        if d*d > n:
            if n > 1:
                factors.append(n)
            break
            
    return factors

def complex_calculation_demo():
    """演示复杂计算缓存的效果"""
    # 第一次调用
    start = time.time()
    factors = prime_factors(9876543210)
    first_time = time.time() - start
    print(f"9876543210的质因数: {factors}")
    print(f"第一次调用耗时: {first_time:.6f}秒")
    
    # 第二次调用（从缓存中获取）
    start = time.time()
    factors = prime_factors(9876543210)
    second_time = time.time() - start
    print(f"第二次调用耗时: {second_time:.6f}秒")
    print(f"性能提升: {first_time/second_time:.2f}倍")
    
    # 查看缓存统计
    print(f"缓存统计: {prime_factors.cache_info()}")

if __name__ == "__main__":
    fibonacci_demo()
    print("\n" + "-"*50 + "\n")
    typed_cache_demo()
    print("\n" + "-"*50 + "\n")
    complex_calculation_demo() 