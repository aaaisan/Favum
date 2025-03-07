import os
import sys
import asyncio
from sqlalchemy.orm import Session
from app.db.database import get_db
sys.path.append('.')
from models.user import User
from models.category import Category
from models.post import Post
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random

def create_sample_data():
    """创建示例数据"""
    print("开始创建示例数据...")
    
    db = next(get_db())
    
    try:
        # 1. 创建一个默认用户
        default_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            bio="站点管理员",
            role="admin"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        print(f"创建用户: {default_user.username}, ID: {default_user.id}")
        
        # 2. 创建一个默认分类
        default_category = Category(
            name="技术讨论",
            description="关于编程、软件开发和技术相关的讨论",
            color="#3b82f6"
        )
        db.add(default_category)
        db.commit()
        db.refresh(default_category)
        print(f"创建分类: {default_category.name}, ID: {default_category.id}")
        
        # 3. 创建5篇测试帖子
        for i in range(1, 6):
            post = Post(
                title=f"测试帖子 {i}",
                content=f"这是测试帖子内容 {i}。这里是一些详细内容...",
                author_id=default_user.id,
                category_id=default_category.id,
                view_count=random.randint(10, 100),
                vote_count=random.randint(0, 20),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(post)
            print(f"创建帖子: {post.title}")
        
        db.commit()
        print("所有数据已创建!")
    except Exception as e:
        db.rollback()
        print(f"创建数据失败: {e}")
    finally:
        db.close()

def main():
    create_sample_data()

if __name__ == "__main__":
    main() 