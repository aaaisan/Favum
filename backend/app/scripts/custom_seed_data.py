import sys
import os
import asyncio
from datetime import datetime, timedelta
import random
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy import text

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(backend_dir)

print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

print("\n尝试导入模块...")

# 自定义密码哈希函数，避免循环导入
def get_password_hash(password: str) -> str:
    """简单的密码哈希函数，仅用于数据种子"""
    return hashlib.sha256(password.encode()).hexdigest()

# 尝试多种可能的导入路径
try:
    from app.db.database import get_db, Base
    from app.db.models import (
        User, Category, Tag, Section, Post, Comment, 
        PostVote, PostFavorite, SectionModerator, 
        post_tags, UserRole, VoteType
    )
    print("成功导入模块")
except ImportError as e:
    print(f"导入失败: {e}")
    try:
        from backend.app.db.database import get_db, Base
        from backend.app.db.models import (
            User, Category, Tag, Section, Post, Comment, 
            PostVote, PostFavorite, SectionModerator, 
            post_tags, UserRole, VoteType
        )
        print("成功导入模块(使用backend前缀)")
    except ImportError as e:
        print(f"导入失败(使用backend前缀): {e}")
        raise

# 获取随机日期
def get_random_date(start_date, end_date):
    """生成两个日期之间的随机日期"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# 种子数据
USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "is_active": True
    },
    {
        "username": "技术达人",
        "email": "tech_master@example.com",
        "password": "password123",
        "role": UserRole.USER,
        "is_active": True
    },
    {
        "username": "前端专家",
        "email": "frontend_pro@example.com",
        "password": "password123", 
        "role": UserRole.USER,
        "is_active": True
    },
    {
        "username": "算法工程师",
        "email": "algorithm_dev@example.com",
        "password": "password123",
        "role": UserRole.USER,
        "is_active": True
    },
    {
        "username": "产品经理",
        "email": "product_mgr@example.com",
        "password": "password123",
        "role": UserRole.USER,
        "is_active": True
    },
    {
        "username": "设计师小王",
        "email": "designer_wang@example.com",
        "password": "password123",
        "role": UserRole.USER,
        "is_active": True
    },
    {
        "username": "版主大人",
        "email": "moderator@example.com",
        "password": "password123",
        "role": UserRole.MODERATOR,
        "is_active": True
    }
]

SECTIONS = [
    {
        "name": "技术区",
        "description": "技术相关讨论"
    },
    {
        "name": "交流区",
        "description": "生活、职场交流"
    },
    {
        "name": "创意区",
        "description": "创意、灵感分享"
    }
]

CATEGORIES = [
    {
        "name": "技术讨论",
        "description": "关于编程、软件开发和技术相关的讨论",
        "order": 1,
        "parent_id": None
    },
    {
        "name": "产品设计",
        "description": "关于产品设计、用户体验和界面设计的讨论",
        "order": 2,
        "parent_id": None
    },
    {
        "name": "职业发展",
        "description": "关于求职、面试、职业规划等话题的讨论",
        "order": 3,
        "parent_id": None
    },
    {
        "name": "项目分享",
        "description": "分享你的项目、代码或创意作品",
        "order": 4,
        "parent_id": None
    },
    {
        "name": "问答求助",
        "description": "技术问题求助和解答",
        "order": 5,
        "parent_id": None
    },
    {
        "name": "前端开发",
        "description": "前端技术讨论",
        "order": 1,
        "parent_id": 1  # 父分类为"技术讨论"
    },
    {
        "name": "后端开发",
        "description": "后端技术讨论",
        "order": 2,
        "parent_id": 1  # 父分类为"技术讨论"
    }
]

TAGS = [
    {"name": "Python"},
    {"name": "JavaScript"},
    {"name": "Vue.js"},
    {"name": "React"},
    {"name": "FastAPI"},
    {"name": "数据库"},
    {"name": "UI设计"},
    {"name": "UX研究"},
    {"name": "性能优化"},
    {"name": "求职"},
    {"name": "面试"},
    {"name": "云服务"},
    {"name": "开源项目"},
    {"name": "人工智能"},
    {"name": "产品管理"}
]

POSTS = [
    {
        "title": "使用FastAPI构建高性能API",
        "content": "FastAPI是一个现代、快速（高性能）的Web框架，用于构建API，基于Python 3.6+的标准类型提示。它的主要特点是：速度非常快、快速编码、更少的错误、直观的、易于学习、简短的、健壮的、基于标准。本文将详细介绍如何使用FastAPI构建高性能的API服务。",
        "author_id": 1,  # admin
        "section_id": 1,  # 技术区
        "category_id": 1,  # 技术讨论
        "tag_ids": [1, 5, 9],  # Python, FastAPI, 性能优化
        "created_at": datetime(2025, 2, 20, 22, 27, 5),
        "is_hidden": False,
        "vote_count": 48
    },
    {
        "title": "Vue.js 3组合式API使用指南",
        "content": "Vue.js 3引入了组合式API，提供了更灵活的逻辑重用和代码组织方式。本文将详细介绍如何使用Vue 3的组合式API，包括setup函数、响应式引用、计算属性、侦听器等核心概念的使用方法和最佳实践。",
        "author_id": 2,  # 技术达人
        "section_id": 1,  # 技术区
        "category_id": 6,  # 前端开发
        "tag_ids": [2, 3],  # JavaScript, Vue.js
        "created_at": datetime(2025, 2, 22, 14, 15, 30),
        "is_hidden": False,
        "vote_count": 37
    },
    {
        "title": "2025年前端面试常见问题及答案",
        "content": "本文汇总了2025年前端开发面试中最常见的问题和推荐答案，包括JavaScript基础、框架使用、性能优化、工程化等方面的内容。希望能帮助即将参加面试的前端开发者做好准备。",
        "author_id": 3,  # 前端专家
        "section_id": 2,  # 交流区
        "category_id": 3,  # 职业发展
        "tag_ids": [2, 10, 11],  # JavaScript, 求职, 面试
        "created_at": datetime(2025, 2, 25, 9, 45, 12),
        "is_hidden": False,
        "vote_count": 62
    },
    {
        "title": "算法学习路线图：从入门到精通",
        "content": "本文提供了一个完整的算法学习路线图，从基础数据结构开始，经过排序算法、搜索算法，一直到高级的图论算法、动态规划等，适合不同阶段的学习者。",
        "author_id": 4,  # 算法工程师
        "section_id": 1,  # 技术区
        "category_id": 1,  # 技术讨论
        "tag_ids": [1, 14],  # Python, 人工智能
        "created_at": datetime(2025, 3, 1, 10, 30, 20),
        "is_hidden": False,
        "vote_count": 25
    },
    {
        "title": "程序员如何有效提升沟通能力",
        "content": "作为程序员，技术能力很重要，但沟通能力同样不可或缺。本文分享了程序员提升沟通能力的实用技巧和方法，帮助技术人员更好地融入团队合作，提高工作效率。",
        "author_id": 5,  # 产品经理
        "section_id": 2,  # 交流区
        "category_id": 3,  # 职业发展
        "tag_ids": [10, 15],  # 求职, 产品管理
        "created_at": datetime(2025, 3, 5, 16, 20, 45),
        "is_hidden": False,
        "vote_count": 15
    }
]

COMMENTS = [
    {
        "content": "这篇文章非常实用，我已经开始使用FastAPI了！",
        "author_id": 3,  # 前端专家
        "post_id": 1,  # FastAPI文章
        "created_at": datetime(2025, 2, 21, 10, 15, 30)
    },
    {
        "content": "请问FastAPI和Flask相比有什么优势？",
        "author_id": 4,  # 算法工程师
        "post_id": 1,  # FastAPI文章
        "created_at": datetime(2025, 2, 21, 14, 25, 10)
    },
    {
        "content": "FastAPI的性能确实比Flask好很多，而且类型提示很方便。",
        "author_id": 1,  # admin
        "post_id": 1,  # FastAPI文章
        "created_at": datetime(2025, 2, 21, 15, 30, 45)
    },
    {
        "content": "组合式API确实解决了很多复杂组件的代码组织问题。",
        "author_id": 5,  # 产品经理
        "post_id": 2,  # Vue.js文章
        "created_at": datetime(2025, 2, 23, 9, 10, 20)
    },
    {
        "content": "感谢分享，这些面试题对我准备面试很有帮助！",
        "author_id": 6,  # 设计师小王
        "post_id": 3,  # 面试文章
        "created_at": datetime(2025, 2, 26, 11, 5, 15)
    },
    {
        "content": "学习算法确实需要循序渐进，这个路线图很合理。",
        "author_id": 3,  # 前端专家
        "post_id": 4,  # 算法学习文章
        "created_at": datetime(2025, 3, 2, 16, 40, 30)
    },
    {
        "content": "沟通能力确实是很多程序员的短板，这篇文章给了很好的建议。",
        "author_id": 4,  # 算法工程师
        "post_id": 5,  # 沟通能力文章
        "created_at": datetime(2025, 3, 6, 8, 55, 25)
    }
]

VOTES = [
    {"post_id": 1, "user_id": 2, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 21, 11, 20, 15)},
    {"post_id": 1, "user_id": 3, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 21, 16, 45, 30)},
    {"post_id": 1, "user_id": 4, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 22, 9, 30, 45)},
    {"post_id": 2, "user_id": 1, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 23, 10, 15, 20)},
    {"post_id": 2, "user_id": 3, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 24, 14, 25, 10)},
    {"post_id": 3, "user_id": 1, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 26, 15, 30, 45)},
    {"post_id": 3, "user_id": 2, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 27, 9, 10, 20)},
    {"post_id": 3, "user_id": 4, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 2, 28, 11, 5, 15)},
    {"post_id": 4, "user_id": 1, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 3, 2, 16, 40, 30)},
    {"post_id": 4, "user_id": 2, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 3, 3, 8, 55, 25)},
    {"post_id": 5, "user_id": 3, "vote_type": VoteType.UPVOTE, "created_at": datetime(2025, 3, 6, 10, 20, 15)},
    {"post_id": 5, "user_id": 6, "vote_type": VoteType.DOWNVOTE, "created_at": datetime(2025, 3, 7, 14, 45, 30)}
]

FAVORITES = [
    {"user_id": 1, "post_id": 2, "created_at": datetime(2025, 2, 23, 11, 30, 45)},
    {"user_id": 1, "post_id": 3, "created_at": datetime(2025, 2, 26, 16, 20, 10)},
    {"user_id": 2, "post_id": 1, "created_at": datetime(2025, 2, 21, 15, 45, 30)},
    {"user_id": 2, "post_id": 4, "created_at": datetime(2025, 3, 2, 17, 10, 25)},
    {"user_id": 3, "post_id": 1, "created_at": datetime(2025, 2, 22, 9, 15, 40)},
    {"user_id": 3, "post_id": 5, "created_at": datetime(2025, 3, 6, 11, 25, 50)},
    {"user_id": 4, "post_id": 3, "created_at": datetime(2025, 2, 27, 10, 30, 15)},
    {"user_id": 5, "post_id": 2, "created_at": datetime(2025, 2, 24, 14, 50, 20)},
    {"user_id": 6, "post_id": 4, "created_at": datetime(2025, 3, 3, 9, 40, 35)}
]

SECTION_MODERATORS = [
    {"section_id": 1, "user_id": 7},  # 版主大人管理技术区
    {"section_id": 2, "user_id": 7}   # 版主大人管理交流区
]

def clear_all_data(db):
    """清除所有现有数据"""
    print("正在清除现有数据...")
    
    try:
        # 按照外键关系的顺序删除数据
        db.execute(text("DELETE FROM post_favorites"))
        db.execute(text("DELETE FROM post_votes"))
        db.execute(text("DELETE FROM post_tags"))
        db.execute(text("DELETE FROM comments"))
        db.execute(text("DELETE FROM posts"))
        db.execute(text("DELETE FROM section_moderators"))
        db.execute(text("DELETE FROM tags"))
        db.execute(text("DELETE FROM categories"))
        db.execute(text("DELETE FROM sections"))
        db.execute(text("DELETE FROM users"))
        
        db.commit()
        print("所有数据已清除")
    except Exception as e:
        try:
            db.rollback()
        except Exception as rollback_error:
            print(f"回滚事务时出错: {rollback_error}")
        print(f"清除数据时出错: {e}")
        raise

def seed_data(db):
    """插入种子数据"""
    print("开始插入种子数据...")
    
    # 创建用户
    users_map = {}
    print("\n创建用户...")
    for i, user_data in enumerate(USERS, 1):
        hashed_password = get_password_hash(user_data["password"])
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            role=user_data["role"],
            is_active=user_data["is_active"],
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()
        users_map[i] = user.id  # 将原始索引映射到实际ID
        print(f"  - 创建用户: {user.username} (ID: {user.id}, 映射: {i} -> {user.id})")
    
    # 创建板块
    sections_map = {}
    print("\n创建板块...")
    for i, section_data in enumerate(SECTIONS, 1):
        section = Section(
            name=section_data["name"],
            description=section_data["description"],
            created_at=datetime.now()
        )
        db.add(section)
        db.flush()
        sections_map[i] = section.id  # 将原始索引映射到实际ID
        print(f"  - 创建板块: {section.name} (ID: {section.id}, 映射: {i} -> {section.id})")
    
    # 创建分类
    categories_map = {}
    print("\n创建分类...")
    # 先创建父分类
    parent_categories = [c for c in CATEGORIES if c["parent_id"] is None]
    for i, category_data in enumerate(parent_categories, 1):
        category = Category(
            name=category_data["name"],
            description=category_data["description"],
            order=category_data["order"],
            created_at=datetime.now()
        )
        db.add(category)
        db.flush()
        categories_map[i] = category.id  # 将原始索引映射到实际ID
        print(f"  - 创建分类: {category.name} (ID: {category.id}, 映射: {i} -> {category.id})")
    
    # 再创建子分类
    child_categories = [c for c in CATEGORIES if c["parent_id"] is not None]
    for i, category_data in enumerate(child_categories, len(parent_categories) + 1):
        parent_id = categories_map[category_data["parent_id"]]
        category = Category(
            name=category_data["name"],
            description=category_data["description"],
            order=category_data["order"],
            parent_id=parent_id,
            created_at=datetime.now()
        )
        db.add(category)
        db.flush()
        categories_map[i] = category.id  # 将原始索引映射到实际ID
        print(f"  - 创建子分类: {category.name} (父分类ID: {parent_id}, ID: {category.id}, 映射: {i} -> {category.id})")
    
    # 创建标签
    tags_map = {}
    print("\n创建标签...")
    for i, tag_data in enumerate(TAGS, 1):
        tag = Tag(
            name=tag_data["name"],
            created_at=datetime.now()
        )
        db.add(tag)
        db.flush()
        tags_map[i] = tag.id  # 将原始索引映射到实际ID
        print(f"  - 创建标签: {tag.name} (ID: {tag.id}, 映射: {i} -> {tag.id})")
    
    # 创建版主关联
    print("\n分配版主...")
    for mod_data in SECTION_MODERATORS:
        section_id = sections_map[mod_data["section_id"]]
        user_id = users_map[mod_data["user_id"]]
        section_mod = SectionModerator(
            section_id=section_id,
            user_id=user_id
        )
        db.add(section_mod)
        print(f"  - 分配用户ID {user_id} 为板块ID {section_id} 的版主")
    
    # 创建帖子
    posts_map = {}
    print("\n创建帖子...")
    for i, post_data in enumerate(POSTS, 1):
        author_id = users_map[post_data["author_id"]]
        section_id = sections_map[post_data["section_id"]]
        category_id = categories_map[post_data["category_id"]]
        
        post = Post(
            title=post_data["title"],
            content=post_data["content"],
            author_id=author_id,
            section_id=section_id,
            category_id=category_id,
            created_at=post_data["created_at"],
            updated_at=post_data["created_at"],
            is_hidden=post_data["is_hidden"],
            vote_count=post_data["vote_count"]
        )
        db.add(post)
        db.flush()
        posts_map[i] = post.id  # 将原始索引映射到实际ID
        
        # 添加帖子-标签关联
        for tag_idx in post_data["tag_ids"]:
            tag_id = tags_map[tag_idx]
            db.execute(
                post_tags.insert().values(post_id=post.id, tag_id=tag_id)
            )
            # 更新标签的帖子计数
            db.execute(
                text(f"UPDATE tags SET post_count = COALESCE(post_count, 0) + 1 WHERE id = {tag_id}")
            )
        
        print(f"  - 创建帖子: {post.title} (ID: {post.id}, 映射: {i} -> {post.id})")
    
    # 创建评论
    comments_map = {}
    print("\n创建评论...")
    for i, comment_data in enumerate(COMMENTS, 1):
        author_id = users_map[comment_data["author_id"]]
        post_id = posts_map[comment_data["post_id"]]
        
        comment = Comment(
            content=comment_data["content"],
            author_id=author_id,
            post_id=post_id,
            created_at=comment_data["created_at"]
        )
        db.add(comment)
        db.flush()
        comments_map[i] = comment.id  # 将原始索引映射到实际ID
        
        # 注释掉更新帖子的评论计数，因为数据库中没有这个字段
        # db.execute(
        #     text(f"UPDATE posts SET comment_count = COALESCE(comment_count, 0) + 1 WHERE id = {post_id}")
        # )
        
        print(f"  - 创建评论: ID {comment.id} 到帖子 {post_id} (映射: {i} -> {comment.id})")
    
    # 创建投票
    print("\n创建投票...")
    for i, vote_data in enumerate(VOTES, 1):
        post_id = posts_map[vote_data["post_id"]]
        user_id = users_map[vote_data["user_id"]]
        
        vote = PostVote(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_data["vote_type"],
            created_at=vote_data["created_at"]
        )
        db.add(vote)
        print(f"  - 创建投票: 用户 {user_id} 对帖子 {post_id} 的 {vote_data['vote_type']} 投票")
    
    # 创建收藏
    print("\n创建收藏...")
    for i, fav_data in enumerate(FAVORITES, 1):
        post_id = posts_map[fav_data["post_id"]]
        user_id = users_map[fav_data["user_id"]]
        
        favorite = PostFavorite(
            post_id=post_id,
            user_id=user_id,
            created_at=fav_data["created_at"]
        )
        db.add(favorite)
        print(f"  - 创建收藏: 用户 {user_id} 收藏帖子 {post_id}")
    
    # 提交所有更改
    db.commit()
    print("\n所有数据已成功插入!")

def main():
    """主函数，运行种子数据导入"""
    # 解析命令行参数
    clear_data = "--no-clear" not in sys.argv
    
    if clear_data:
        print("警告: 将清除所有现有数据!")
        response = input("确定要继续吗? (y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("操作已取消")
            return
    
    # 获取数据库会话
    try:
        print("尝试连接数据库...")
        db_generator = get_db()
        try:
            db = next(db_generator)
            print("成功获取数据库会话（同步方式）")
        except (TypeError, StopIteration) as e:
            print(f"无法获取数据库会话: {e}")
            raise
        
        # 清除数据（如果需要）
        if clear_data:
            clear_all_data(db)
        
        # 插入新数据
        seed_data(db)
        
    except Exception as e:
        print(f"导入数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            # 尝试关闭数据库连接
            if 'db' in locals():
                db.close()
                print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")

if __name__ == "__main__":
    # 运行主函数
    main() 