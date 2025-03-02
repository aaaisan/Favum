from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import hashlib
import json
import re
import uuid
from pathlib import Path

def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def to_camel(string: str) -> str:
    """下划线转驼峰"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_snake(string: str) -> str:
    """驼峰转下划线"""
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', string).lower()

def format_datetime(dt: Optional[datetime] = None) -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(d: Optional[date] = None) -> str:
    """格式化日期"""
    if d is None:
        d = date.today()
    return d.strftime("%Y-%m-%d")

def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """将列表分块"""
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def remove_html_tags(text: str) -> str:
    """移除HTML标签"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def truncate_string(text: str, length: int, suffix: str = '...') -> str:
    """截断字符串"""
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix

def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def format_file_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}PB"

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()

def is_safe_filename(filename: str) -> bool:
    """检查文件名是否安全"""
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', filename))

def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    return re.sub(r'[^\w.-]', '_', filename) 