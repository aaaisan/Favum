"""
枚举工具模块

提供处理枚举类型的工具函数，简化枚举值的使用和验证。
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

T = TypeVar('T', bound='Enum')

def safe_enum_parse(enum_class: Type[T], value: Any, default: Optional[T] = None) -> Optional[T]:
    """
    安全解析枚举值
    
    Args:
        enum_class: 枚举类
        value: 要解析的值
        default: 解析失败时的默认值
        
    Returns:
        解析后的枚举值或默认值
    
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        # 成功解析
        color = safe_enum_parse(Color, "red")  # 返回 Color.RED
        
        # 解析失败，返回默认值
        color = safe_enum_parse(Color, "yellow", default=Color.RED)  # 返回 Color.RED
        
        # 解析失败，返回None
        color = safe_enum_parse(Color, "yellow")  # 返回 None
        ```
    """
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default

def enum_to_dict(enum_class: Type[Enum]) -> Dict[str, Any]:
    """
    将枚举类转换为字典
    
    Args:
        enum_class: 枚举类
        
    Returns:
        包含枚举名称和值的字典
        
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        colors = enum_to_dict(Color)
        # 返回 {"RED": "red", "GREEN": "green", "BLUE": "blue"}
        ```
    """
    return {item.name: item.value for item in enum_class}

def enum_values(enum_class: Type[Enum]) -> List[Any]:
    """
    获取枚举类的所有值
    
    Args:
        enum_class: 枚举类
        
    Returns:
        枚举值列表
        
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        values = enum_values(Color)
        # 返回 ["red", "green", "blue"]
        ```
    """
    return [item.value for item in enum_class]

def enum_names(enum_class: Type[Enum]) -> List[str]:
    """
    获取枚举类的所有名称
    
    Args:
        enum_class: 枚举类
        
    Returns:
        枚举名称列表
        
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        names = enum_names(Color)
        # 返回 ["RED", "GREEN", "BLUE"]
        ```
    """
    return [item.name for item in enum_class]

def is_valid_enum(enum_class: Type[Enum], value: Any) -> bool:
    """
    检查值是否为有效的枚举值
    
    Args:
        enum_class: 枚举类
        value: 要检查的值
        
    Returns:
        是否为有效的枚举值
        
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        is_valid_enum(Color, "red")  # 返回 True
        is_valid_enum(Color, "yellow")  # 返回 False
        ```
    """
    return safe_enum_parse(enum_class, value) is not None

def get_enum_by_name(enum_class: Type[T], name: str, default: Optional[T] = None) -> Optional[T]:
    """
    根据枚举名称获取枚举项
    
    Args:
        enum_class: 枚举类
        name: 枚举名称
        default: 找不到时的默认值
        
    Returns:
        枚举项或默认值
        
    Example:
        ```python
        from enum import Enum
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            
        get_enum_by_name(Color, "RED")  # 返回 Color.RED
        get_enum_by_name(Color, "YELLOW", default=Color.RED)  # 返回 Color.RED
        ```
    """
    try:
        return enum_class[name]
    except (KeyError, ValueError):
        return default 