from datetime import datetime
from typing import Dict, Any, Union

def format_dates(obj: Dict[str, Any], date_fields: list = None) -> Dict[str, Any]:
    """格式化对象中的日期时间字段为ISO格式字符串
    
    Args:
        obj: 要处理的字典对象
        date_fields: 要处理的日期字段列表，默认为['created_at', 'updated_at', 'deleted_at']
        
    Returns:
        Dict[str, Any]: 处理后的字典对象，日期字段被转换为ISO格式字符串
    """
    if not isinstance(obj, dict):
        return obj
        
    # 默认处理的日期字段
    if date_fields is None:
        date_fields = ['created_at', 'updated_at', 'deleted_at']
    
    # 复制一份，避免修改原对象
    result = obj.copy()
    
    # 处理顶层日期字段
    for field in date_fields:
        if isinstance(result.get(field), datetime):
            result[field] = result[field].isoformat()
    
    # 处理嵌套对象中的日期字段
    for key, value in result.items():
        if isinstance(value, dict):
            result[key] = format_dates(value, date_fields)
        elif isinstance(value, list):
            result[key] = [format_dates(item, date_fields) if isinstance(item, dict) else item for item in value]
    
    return result

def format_post_dates(post: Dict[str, Any]) -> Dict[str, Any]:
    """格式化帖子对象中的日期时间字段
    
    处理帖子对象及其嵌套对象（如分类、标签等）中的日期时间字段，
    将其转换为ISO格式字符串，便于JSON序列化。
    
    Args:
        post: 帖子字典对象
        
    Returns:
        Dict[str, Any]: 处理后的帖子对象，日期字段被转换为ISO格式字符串
    """
    return format_dates(post) 