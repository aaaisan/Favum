#!/usr/bin/env python
"""
修复用户密码脚本
重新设置用户密码，解决密码哈希不兼容的问题
"""
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 直接使用passlib进行密码哈希，避免循环导入
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """获取密码的哈希值"""
    return pwd_context.hash(password)

from app.db.database import SessionLocal
from app.db.models import User

def fix_user_passwords():
    """修复用户密码"""
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 修复admin用户密码
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            # 重新哈希admin123密码
            admin.hashed_password = get_password_hash("admin123")
            print(f"已重置用户 {admin.username} 的密码")
        else:
            print("找不到admin用户")
            
        # 可以在这里添加其他需要修复的用户密码
        
        # 提交更改
        db.commit()
        print("用户密码修复完成")
    except Exception as e:
        db.rollback()
        print(f"修复密码时出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("开始修复用户密码...")
    fix_user_passwords() 