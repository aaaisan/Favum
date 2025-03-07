import os
import sys
import asyncio
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

print("\n加载环境变量...")
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件中的环境变量

print("\n尝试导入模块...")

# 导入最基本的模块和密码加密的函数
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """获取密码的哈希值"""
    return pwd_context.hash(password)

# 导入项目中的模型和数据库会话
from app.db.database import engine, SessionLocal, Base
from app.db.models import User, Category, Tag, Post, Comment, post_tags, UserRole, Section

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
        "role": "admin",
    },
    {
        "username": "zhang_wei",
        "email": "zhang_wei@example.com",
        "password": "password123",
        "role": "user",
    },
    {
        "username": "li_na",
        "email": "li_na@example.com",
        "password": "password123",
        "role": "user",
    },
    {
        "username": "wang_fang",
        "email": "wang_fang@example.com",
        "password": "password123",
        "role": "user",
    }
]

CATEGORIES = [
    {
        "name": "技术讨论",
        "description": "关于编程、软件开发和技术相关的讨论",
        "order": 1
    },
    {
        "name": "产品设计",
        "description": "关于产品设计、用户体验和界面设计的讨论",
        "order": 2
    },
    {
        "name": "职业发展",
        "description": "关于求职、面试、职业规划等话题的讨论",
        "order": 3
    },
    {
        "name": "项目分享",
        "description": "分享你的项目、代码或创意作品",
        "order": 4
    },
    {
        "name": "问答求助",
        "description": "技术问题求助和解答",
        "order": 5
    },
    {
        "name": "行业动态",
        "description": "讨论IT行业新闻、趋势和事件",
        "order": 6
    },
    {
        "name": "闲聊灌水",
        "description": "轻松话题，交友聊天",
        "order": 7
    }
]

SECTIONS = [
    {
        "name": "主论坛",
        "description": "论坛主版块，包含所有主题讨论"
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
        "content": "FastAPI是一个现代、快速（高性能）的Web框架，用于构建API，基于Python 3.6+的标准类型提示。它的主要特点是：\n\n- 速度非常快：性能与NodeJS和Go相当，基于Starlette和Pydantic\n- 快速编码：它允许约300-500%的功能开发速度增长\n- 更少的错误：减少约40%人为（开发者）导致的错误\n- 直观：强大的编辑器支持，补全无处不在，减少调试时间\n- 简单：设计简单易用，读文档的时间更少\n- 短：代码重复最小化，每个参数声明具有多个功能\n\n在这篇文章中，我将介绍如何使用FastAPI构建一个高性能的API服务，包括数据验证、依赖注入、身份验证等关键特性。",
        "user_email": "admin@example.com",
        "category_name": "技术讨论",
        "section_name": "主论坛",
        "vote_count": 45,
        "tag_names": ["FastAPI", "性能优化", "Python"]
    },
    {
        "title": "Vue.js 3组合式API使用指南",
        "content": "Vue.js 3的组合式API提供了一种全新的方式来组织和重用组件逻辑。与Vue 2的选项式API相比，组合式API更加灵活，允许开发者根据逻辑关注点而不是选项类型组织代码。\n\n在这篇文章中，我将介绍组合式API的核心概念，如setup、ref、reactive、computed和watch等，并通过实际例子展示如何使用这些功能来构建高效、可维护的组件。\n\n我们还将讨论如何创建和使用自定义组合函数（Composables）来重用组件逻辑，以及如何在大型应用中有效地组织这些函数。",
        "user_email": "li_na@example.com",
        "category_name": "技术讨论",
        "section_name": "主论坛",
        "vote_count": 38,
        "tag_names": ["Vue.js", "JavaScript"]
    },
    {
        "title": "2023年前端面试常见问题及答案",
        "content": "对于寻找前端开发工作的开发者来说，了解当前的面试趋势和准备常见问题的答案是至关重要的。在这篇文章中，我将分享2023年前端开发面试中最常见的问题，以及如何准备这些问题的答案。\n\n涵盖的主题包括：\n\n- JavaScript基础知识和ES6+特性\n- 框架特定问题（React、Vue、Angular）\n- CSS布局和响应式设计\n- Web性能优化技术\n- 状态管理解决方案\n- 前端安全最佳实践\n- 系统设计问题\n\n此外，我还将提供一些面试策略和技巧，帮助你在面试过程中表现出色，展示你的技能和经验。",
        "user_email": "zhang_wei@example.com",
        "category_name": "职业发展",
        "section_name": "主论坛",
        "vote_count": 120,
        "tag_names": ["JavaScript", "Vue.js", "React", "求职", "面试"]
    },
    {
        "title": "用户体验设计中的心理学原理",
        "content": "优秀的用户体验设计不仅仅是关于美观的界面，更是关于理解用户的心理和行为模式。了解基本的心理学原理可以帮助设计师创造更有效、更令人愉悦的用户体验。\n\n在这篇文章中，我将探讨以下几个对UX设计至关重要的心理学原理：\n\n- 格式塔原理（接近性、相似性、连续性等）\n- 希克定律（选择增加时决策时间增加）\n- 菲茨定律（点击目标的大小与距离关系）\n- 认知负荷理论\n- 锚定效应\n- 确认偏误\n- 峰终定律\n\n通过实际的设计案例，我将展示如何应用这些原理来改善用户体验，提高用户参与度和满意度。",
        "user_email": "li_na@example.com",
        "category_name": "产品设计",
        "section_name": "主论坛",
        "vote_count": 88,
        "tag_names": ["UI设计", "UX研究", "产品管理"]
    },
    {
        "title": "构建高可用的微服务架构",
        "content": "微服务架构已经成为构建大型、复杂应用程序的流行方法，但它也带来了许多新的挑战，尤其是在高可用性方面。在这篇文章中，我将分享我在构建和维护高可用微服务系统中获得的经验和最佳实践。\n\n主要内容包括：\n\n- 微服务设计原则与模式\n- 服务发现与注册\n- 负载均衡策略\n- 断路器模式与故障隔离\n- 分布式跟踪与监控\n- 自动扩展与自我修复\n- 一致性与最终一致性权衡\n- 数据管理策略\n\n我将使用实际案例来说明这些概念，并提供具体的实现建议，帮助你设计和构建更加可靠、可伸缩的微服务系统。",
        "user_email": "wang_fang@example.com",
        "category_name": "技术讨论",
        "section_name": "主论坛",
        "vote_count": 72,
        "tag_names": ["性能优化", "数据库", "云服务"]
    }
]

COMMENTS = [
    {
        "content": "非常详细的教程，感谢分享！我最近也在学习FastAPI，这篇文章对我帮助很大。",
        "user_email": "zhang_wei@example.com",
        "post_title": "使用FastAPI构建高性能API"
    },
    {
        "content": "我有一个问题，在处理大量并发请求时，FastAPI和Flask相比有多大的性能提升？有没有具体的benchmark数据？",
        "user_email": "wang_fang@example.com",
        "post_title": "使用FastAPI构建高性能API"
    },
    {
        "content": "组合式API确实提供了更好的代码组织方式，但对于习惯了选项式API的开发者来说，学习曲线还是有点陡峭。不过你的解释很清晰，谢谢！",
        "user_email": "admin@example.com",
        "post_title": "Vue.js 3组合式API使用指南"
    },
    {
        "content": "峰终定律在设计用户旅程时特别重要，我在我们的产品中应用了这个原理，用户满意度确实有所提高。建议可以添加一些关于如何在表单设计中应用这个原理的具体例子。",
        "user_email": "zhang_wei@example.com",
        "post_title": "用户体验设计中的心理学原理"
    },
    {
        "content": "这篇文章正是我需要的！下周有几场前端面试，这些题目和答案帮我梳理了很多知识点。特别是关于状态管理的部分，讲得很全面。",
        "user_email": "li_na@example.com",
        "post_title": "2023年前端面试常见问题及答案"
    },
    {
        "content": "关于断路器模式的部分讲得很好，但我想知道在实际项目中，你是使用像Hystrix这样的库还是自己实现的断路器逻辑？",
        "user_email": "admin@example.com",
        "post_title": "构建高可用的微服务架构"
    }
]

def create_tables():
    """创建所有数据库表"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("表创建完成")

def seed_forum_data(clear_existing=False):
    """向数据库添加论坛种子数据"""
    print("开始导入论坛数据...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 如果需要清除现有数据，可以在这里操作
        if clear_existing:
            print("清除现有数据...")
            # 这里根据实际的数据库结构清除数据
            # 通常应该按照依赖关系的反序删除
            db.query(Comment).delete()
            db.execute(post_tags.delete())
            db.query(Post).delete()
            db.query(Tag).delete()
            db.query(Category).delete()
            db.query(Section).delete()
            db.query(User).delete()
            db.commit()
            print("现有数据已清除")
        
        # 添加用户
        user_db_objects = {}
        for user_data in USERS:
            username = user_data["username"]
            email = user_data["email"]
            print(f"添加用户: {username}")
            
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"用户 {username} 已存在，跳过")
                user_db_objects[email] = existing_user
                continue
            
            # 创建用户
            hashed_password = get_password_hash(user_data["password"])
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=user_data.get("role", "user"),
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            user_db_objects[email] = user
        
        # 添加论坛版块
        section_db_objects = {}
        for section_data in SECTIONS:
            name = section_data["name"]
            print(f"添加版块: {name}")
            
            # 检查版块是否已存在
            existing_section = db.query(Section).filter(Section.name == name).first()
            if existing_section:
                print(f"版块 {name} 已存在，跳过")
                section_db_objects[name] = existing_section
                continue
            
            # 创建版块
            section = Section(
                name=name,
                description=section_data["description"]
            )
            
            db.add(section)
            db.commit()
            db.refresh(section)
            section_db_objects[name] = section
        
        # 添加分类
        category_db_objects = {}
        for cat_data in CATEGORIES:
            name = cat_data["name"]
            print(f"添加分类: {name}")
            
            # 检查分类是否已存在
            existing_category = db.query(Category).filter(Category.name == name).first()
            if existing_category:
                print(f"分类 {name} 已存在，跳过")
                category_db_objects[name] = existing_category
                continue
            
            # 创建分类
            category = Category(
                name=name,
                description=cat_data["description"],
                order=cat_data.get("order", 0)
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            category_db_objects[name] = category
        
        # 添加标签
        tag_db_objects = {}
        for tag_data in TAGS:
            name = tag_data["name"]
            print(f"添加标签: {name}")
            
            # 检查标签是否已存在
            existing_tag = db.query(Tag).filter(Tag.name == name).first()
            if existing_tag:
                print(f"标签 {name} 已存在，跳过")
                tag_db_objects[name] = existing_tag
                continue
            
            # 创建标签
            tag = Tag(name=name)
            
            db.add(tag)
            db.commit()
            db.refresh(tag)
            tag_db_objects[name] = tag
        
        # 添加帖子
        post_db_objects = {}
        
        for post_data in POSTS:
            title = post_data["title"]
            print(f"添加帖子: {title}")
            
            # 检查帖子是否已存在
            existing_post = db.query(Post).filter(Post.title == title).first()
            if existing_post:
                print(f"帖子 '{title}' 已存在，跳过")
                post_db_objects[title] = existing_post
                continue
            
            # 获取用户
            user = user_db_objects.get(post_data["user_email"])
            if not user:
                print(f"找不到用户 {post_data['user_email']}，跳过帖子")
                continue
            
            # 获取分类
            category = category_db_objects.get(post_data["category_name"])
            if not category:
                print(f"找不到分类 {post_data['category_name']}，跳过帖子")
                continue
            
            # 获取版块
            section = section_db_objects.get(post_data["section_name"])
            if not section:
                print(f"找不到版块 {post_data['section_name']}，跳过帖子")
                continue
            
            # 随机创建时间
            now = datetime.now()
            created_at = get_random_date(now - timedelta(days=30), now)
            
            # 创建帖子
            post = Post(
                title=title,
                content=post_data["content"],
                author_id=user.id,
                category_id=category.id,
                section_id=section.id,
                vote_count=post_data.get("vote_count", 0),
                created_at=created_at,
                updated_at=created_at
            )
            
            db.add(post)
            db.commit()
            db.refresh(post)
            post_db_objects[title] = post
            
            # 添加标签关联
            for tag_name in post_data["tag_names"]:
                tag = tag_db_objects.get(tag_name)
                if tag:
                    # 使用SQLAlchemy的表达式语言插入到关联表
                    db.execute(
                        post_tags.insert().values(
                            post_id=post.id,
                            tag_id=tag.id
                        )
                    )
                else:
                    print(f"找不到标签 {tag_name}，跳过")
            
            db.commit()
        
        # 添加评论
        for comment_data in COMMENTS:
            content = comment_data["content"]
            print(f"添加评论: '{content[:30]}...'")
            
            # 获取用户
            user = user_db_objects.get(comment_data["user_email"])
            if not user:
                print(f"找不到用户 {comment_data['user_email']}，跳过评论")
                continue
            
            # 获取帖子
            post = post_db_objects.get(comment_data["post_title"])
            if not post:
                print(f"找不到帖子 '{comment_data['post_title']}'，跳过评论")
                continue
            
            # 随机创建时间（晚于帖子创建时间）
            created_at = get_random_date(post.created_at, datetime.now())
            
            # 创建评论
            comment = Comment(
                content=content,
                author_id=user.id,
                post_id=post.id,
                created_at=created_at
            )
            
            db.add(comment)
            db.commit()
            
            # 更新帖子的评论计数 - 通过手动计算
            comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
            if hasattr(post, 'comment_count'):
                # 如果帖子模型有comment_count字段
                db.execute(
                    f"UPDATE posts SET comment_count = {comment_count} WHERE id = {post.id}"
                )
                db.commit()
        
        print("论坛数据导入完成")
    except Exception as e:
        db.rollback()
        print(f"导入数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """主函数，运行种子数据导入"""
    # 解析命令行参数
    clear_data = "--clear" in sys.argv
    
    if clear_data:
        print("警告: 将清除所有现有数据!")
        response = input("确定要继续吗? (y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("操作已取消")
            return
    
    # 创建表（如果不存在）
    create_tables()
    
    # 导入数据
    seed_forum_data(clear_existing=clear_data)

if __name__ == "__main__":
    main() 