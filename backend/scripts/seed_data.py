import os
import sys
import asyncio
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import random

# 添加项目根目录到Python路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目中的数据库模型和连接
from database import engine, get_db, Base
from models import User, Post, Comment, Category, Tag, post_tags

# 导入用于密码哈希的工具
from passlib.context import CryptContext

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 获取随机日期
def get_random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# 种子数据
USERS = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "bio": "站点管理员",
        "avatar": None,
        "role": "admin",
        "post_count": 10,
        "comment_count": 25,
        "like_count": 130
    },
    {
        "id": 2,
        "username": "zhang_wei",
        "email": "zhang_wei@example.com",
        "password": "password123",
        "bio": "热爱技术，喜欢分享",
        "avatar": None,
        "role": "user",
        "post_count": 8,
        "comment_count": 42,
        "like_count": 95
    },
    {
        "id": 3,
        "username": "li_na",
        "email": "li_na@example.com",
        "password": "password123",
        "bio": "设计师，对用户体验和界面设计很感兴趣",
        "avatar": None,
        "role": "user",
        "post_count": 15,
        "comment_count": 56,
        "like_count": 210
    },
    {
        "id": 4,
        "username": "wang_fang",
        "email": "wang_fang@example.com",
        "password": "password123",
        "bio": "后端开发者，专注于性能优化",
        "avatar": None,
        "role": "user",
        "post_count": 20,
        "comment_count": 35,
        "like_count": 180
    }
]

CATEGORIES = [
    {
        "id": 1,
        "name": "技术讨论",
        "description": "关于编程、软件开发和技术相关的讨论",
        "color": "#3b82f6"
    },
    {
        "id": 2,
        "name": "产品设计",
        "description": "关于产品设计、用户体验和界面设计的讨论",
        "color": "#10b981"
    },
    {
        "id": 3,
        "name": "职业发展",
        "description": "关于求职、面试、职业规划等话题的讨论",
        "color": "#f59e0b"
    },
    {
        "id": 4,
        "name": "项目分享",
        "description": "分享你的项目、代码或创意作品",
        "color": "#8b5cf6"
    },
    {
        "id": 5,
        "name": "问答求助",
        "description": "技术问题求助和解答",
        "color": "#ef4444"
    },
    {
        "id": 6,
        "name": "行业动态",
        "description": "讨论IT行业新闻、趋势和事件",
        "color": "#ec4899"
    },
    {
        "id": 7,
        "name": "闲聊灌水",
        "description": "轻松话题，交友聊天",
        "color": "#6366f1"
    }
]

TAGS = [
    {"id": 1, "name": "Python"},
    {"id": 2, "name": "JavaScript"},
    {"id": 3, "name": "Vue.js"},
    {"id": 4, "name": "React"},
    {"id": 5, "name": "FastAPI"},
    {"id": 6, "name": "数据库"},
    {"id": 7, "name": "UI设计"},
    {"id": 8, "name": "UX研究"},
    {"id": 9, "name": "性能优化"},
    {"id": 10, "name": "求职"},
    {"id": 11, "name": "面试"},
    {"id": 12, "name": "云服务"},
    {"id": 13, "name": "开源项目"},
    {"id": 14, "name": "人工智能"},
    {"id": 15, "name": "产品管理"}
]

POSTS = [
    {
        "id": 1,
        "title": "使用FastAPI构建高性能API",
        "content": "FastAPI是一个现代、快速（高性能）的Web框架，用于构建API，基于Python 3.6+的标准类型提示。它的主要特点是：\n\n- 速度非常快：性能与NodeJS和Go相当，基于Starlette和Pydantic\n- 快速编码：它允许约300-500%的功能开发速度增长\n- 更少的错误：减少约40%人为（开发者）导致的错误\n- 直观：强大的编辑器支持，补全无处不在，减少调试时间\n- 简单：设计简单易用，读文档的时间更少\n- 短：代码重复最小化，每个参数声明具有多个功能\n\n在这篇文章中，我将介绍如何使用FastAPI构建一个高性能的API服务，包括数据验证、依赖注入、身份验证等关键特性。",
        "userId": 1,
        "categoryId": 1,
        "view_count": 1250,
        "comment_count": 18,
        "vote_count": 45,
        "tags": [5, 9, 1]
    },
    {
        "id": 2,
        "title": "Vue.js 3组合式API使用指南",
        "content": "Vue.js 3的组合式API提供了一种全新的方式来组织和重用组件逻辑。与Vue 2的选项式API相比，组合式API更加灵活，允许开发者根据逻辑关注点而不是选项类型组织代码。\n\n在这篇文章中，我将介绍组合式API的核心概念，如setup、ref、reactive、computed和watch等，并通过实际例子展示如何使用这些功能来构建高效、可维护的组件。\n\n我们还将讨论如何创建和使用自定义组合函数（Composables）来重用组件逻辑，以及如何在大型应用中有效地组织这些函数。",
        "userId": 3,
        "categoryId": 1,
        "view_count": 980,
        "comment_count": 12,
        "vote_count": 38,
        "tags": [3, 2]
    },
    {
        "id": 3,
        "title": "2023年前端面试常见问题及答案",
        "content": "对于寻找前端开发工作的开发者来说，了解当前的面试趋势和准备常见问题的答案是至关重要的。在这篇文章中，我将分享2023年前端开发面试中最常见的问题，以及如何准备这些问题的答案。\n\n涵盖的主题包括：\n\n- JavaScript基础知识和ES6+特性\n- 框架特定问题（React、Vue、Angular）\n- CSS布局和响应式设计\n- Web性能优化技术\n- 状态管理解决方案\n- 前端安全最佳实践\n- 系统设计问题\n\n此外，我还将提供一些面试策略和技巧，帮助你在面试过程中表现出色，展示你的技能和经验。",
        "userId": 2,
        "categoryId": 3,
        "view_count": 2450,
        "comment_count": 35,
        "vote_count": 120,
        "tags": [2, 3, 4, 10, 11]
    },
    {
        "id": 4,
        "title": "用户体验设计中的心理学原理",
        "content": "优秀的用户体验设计不仅仅是关于美观的界面，更是关于理解用户的心理和行为模式。了解基本的心理学原理可以帮助设计师创造更有效、更令人愉悦的用户体验。\n\n在这篇文章中，我将探讨以下几个对UX设计至关重要的心理学原理：\n\n- 格式塔原理（接近性、相似性、连续性等）\n- 希克定律（选择增加时决策时间增加）\n- 菲茨定律（点击目标的大小与距离关系）\n- 认知负荷理论\n- 锚定效应\n- 确认偏误\n- 峰终定律\n\n通过实际的设计案例，我将展示如何应用这些原理来改善用户体验，提高用户参与度和满意度。",
        "userId": 3,
        "categoryId": 2,
        "view_count": 1850,
        "comment_count": 22,
        "vote_count": 88,
        "tags": [7, 8, 15]
    },
    {
        "id": 5,
        "title": "构建高可用的微服务架构",
        "content": "微服务架构已经成为构建大型、复杂应用程序的流行方法，但它也带来了许多新的挑战，尤其是在高可用性方面。在这篇文章中，我将分享我在构建和维护高可用微服务系统中获得的经验和最佳实践。\n\n主要内容包括：\n\n- 微服务设计原则与模式\n- 服务发现与注册\n- 负载均衡策略\n- 断路器模式与故障隔离\n- 分布式跟踪与监控\n- 自动扩展与自我修复\n- 一致性与最终一致性权衡\n- 数据管理策略\n\n我将使用实际案例来说明这些概念，并提供具体的实现建议，帮助你设计和构建更加可靠、可伸缩的微服务系统。",
        "userId": 4,
        "categoryId": 1,
        "view_count": 1550,
        "comment_count": 16,
        "vote_count": 72,
        "tags": [9, 6, 12]
    }
]

COMMENTS = [
    {
        "id": 1,
        "content": "非常详细的教程，感谢分享！我最近也在学习FastAPI，这篇文章对我帮助很大。",
        "userId": 2,
        "postId": 1,
        "likes": 8
    },
    {
        "id": 2,
        "content": "我有一个问题，在处理大量并发请求时，FastAPI和Flask相比有多大的性能提升？有没有具体的benchmark数据？",
        "userId": 4,
        "postId": 1,
        "likes": 5
    },
    {
        "id": 3,
        "content": "组合式API确实提供了更好的代码组织方式，但对于习惯了选项式API的开发者来说，学习曲线还是有点陡峭。不过你的解释很清晰，谢谢！",
        "userId": 1,
        "postId": 2,
        "likes": 12
    },
    {
        "id": 4,
        "content": "峰终定律在设计用户旅程时特别重要，我在我们的产品中应用了这个原理，用户满意度确实有所提高。建议可以添加一些关于如何在表单设计中应用这个原理的具体例子。",
        "userId": 2,
        "postId": 4,
        "likes": 15
    },
    {
        "id": 5,
        "content": "这篇文章正是我需要的！下周有几场前端面试，这些题目和答案帮我梳理了很多知识点。特别是关于状态管理的部分，讲得很全面。",
        "userId": 3,
        "postId": 3,
        "likes": 20
    },
    {
        "id": 6,
        "content": "关于断路器模式的部分讲得很好，但我想知道在实际项目中，你是使用像Hystrix这样的库还是自己实现的断路器逻辑？",
        "userId": 1,
        "postId": 5,
        "likes": 7
    }
]

# 帖子-标签关系
POST_TAGS = [
    {"post_id": 1, "tag_id": 5},
    {"post_id": 1, "tag_id": 9},
    {"post_id": 1, "tag_id": 1},
    {"post_id": 2, "tag_id": 3},
    {"post_id": 2, "tag_id": 2},
    {"post_id": 3, "tag_id": 2},
    {"post_id": 3, "tag_id": 3},
    {"post_id": 3, "tag_id": 4},
    {"post_id": 3, "tag_id": 10},
    {"post_id": 3, "tag_id": 11},
    {"post_id": 4, "tag_id": 7},
    {"post_id": 4, "tag_id": 8},
    {"post_id": 4, "tag_id": 15},
    {"post_id": 5, "tag_id": 9},
    {"post_id": 5, "tag_id": 6},
    {"post_id": 5, "tag_id": 12}
]

# 数据库导入函数
async def seed_database(clear_existing=False):
    # 创建所有表（如果不存在）
    async with engine.begin() as conn:
        if clear_existing:
            # 删除所有现有数据
            await conn.run_sync(Base.metadata.drop_all)
        # 创建表
        await conn.run_sync(Base.metadata.create_all)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 添加用户
        user_objs = []
        for user_data in USERS:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"用户 {user_data['username']} 已存在，跳过")
                continue
                
            # 哈希密码
            hashed_password = pwd_context.hash(user_data["password"])
            
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                bio=user_data["bio"],
                role=user_data["role"]
            )
            user_objs.append(user)
        
        db.add_all(user_objs)
        db.commit()
        print(f"成功添加 {len(user_objs)} 名用户")
        
        # 添加分类
        category_objs = []
        for cat_data in CATEGORIES:
            existing_category = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if existing_category:
                print(f"分类 {cat_data['name']} 已存在，跳过")
                continue
                
            category = Category(
                id=cat_data["id"],
                name=cat_data["name"],
                description=cat_data["description"],
                color=cat_data["color"]
            )
            category_objs.append(category)
        
        db.add_all(category_objs)
        db.commit()
        print(f"成功添加 {len(category_objs)} 个分类")
        
        # 添加标签
        tag_objs = []
        for tag_data in TAGS:
            existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
            if existing_tag:
                print(f"标签 {tag_data['name']} 已存在，跳过")
                continue
                
            tag = Tag(
                id=tag_data["id"],
                name=tag_data["name"]
            )
            tag_objs.append(tag)
        
        db.add_all(tag_objs)
        db.commit()
        print(f"成功添加 {len(tag_objs)} 个标签")
        
        # 添加帖子
        post_objs = []
        for post_data in POSTS:
            existing_post = db.query(Post).filter(Post.title == post_data["title"]).first()
            if existing_post:
                print(f"帖子 '{post_data['title']}' 已存在，跳过")
                continue
                
            # 获取随机创建时间（过去30天内）
            now = datetime.now()
            created_at = get_random_date(now - timedelta(days=30), now)
            updated_at = created_at
            
            # 随机决定是否更新过
            if random.random() > 0.7:  # 30%的帖子有更新
                updated_at = get_random_date(created_at, now)
            
            post = Post(
                id=post_data["id"],
                title=post_data["title"],
                content=post_data["content"],
                user_id=post_data["userId"],
                category_id=post_data["categoryId"],
                view_count=post_data["view_count"],
                vote_count=post_data["vote_count"],
                created_at=created_at,
                updated_at=updated_at
            )
            post_objs.append(post)
        
        db.add_all(post_objs)
        db.commit()
        print(f"成功添加 {len(post_objs)} 篇帖子")
        
        # 添加评论
        comment_objs = []
        for comment_data in COMMENTS:
            # 获取随机创建时间（与对应帖子的创建时间之后）
            post = db.query(Post).filter(Post.id == comment_data["postId"]).first()
            if not post:
                print(f"找不到ID为 {comment_data['postId']} 的帖子，跳过评论")
                continue
                
            created_at = get_random_date(post.created_at, datetime.now())
            
            comment = Comment(
                id=comment_data["id"],
                content=comment_data["content"],
                user_id=comment_data["userId"],
                post_id=comment_data["postId"],
                likes=comment_data["likes"],
                created_at=created_at,
                updated_at=created_at
            )
            comment_objs.append(comment)
        
        db.add_all(comment_objs)
        db.commit()
        print(f"成功添加 {len(comment_objs)} 条评论")
        
        # 添加帖子-标签关系
        for relation in POST_TAGS:
            post_id = relation["post_id"]
            tag_id = relation["tag_id"]
            
            # 检查帖子和标签是否存在
            post = db.query(Post).filter(Post.id == post_id).first()
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            
            if not post or not tag:
                print(f"找不到帖子ID {post_id} 或标签ID {tag_id}，跳过关系")
                continue
            
            # 检查关系是否已存在
            stmt = post_tags.select().where(
                post_tags.c.post_id == post_id,
                post_tags.c.tag_id == tag_id
            )
            result = db.execute(stmt).first()
            
            if result:
                print(f"帖子 {post_id} 和标签 {tag_id} 的关系已存在，跳过")
                continue
            
            # 添加关系
            stmt = post_tags.insert().values(post_id=post_id, tag_id=tag_id)
            db.execute(stmt)
        
        db.commit()
        print("成功添加帖子-标签关系")
        
        # 更新评论计数
        for post in db.query(Post).all():
            comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
            post.comment_count = comment_count
        
        db.commit()
        print("成功更新所有帖子的评论计数")
        
    except Exception as e:
        db.rollback()
        print(f"导入数据时出错: {str(e)}")
        raise
    finally:
        db.close()

# 运行脚本
if __name__ == "__main__":
    # 检查命令行参数
    clear_data = "--clear" in sys.argv
    
    print("开始导入数据...")
    if clear_data:
        print("将清除所有现有数据")
    
    # 运行异步函数
    asyncio.run(seed_database(clear_existing=clear_data))
    
    print("数据导入完成！") 