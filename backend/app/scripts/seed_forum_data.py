import sys
import os
import asyncio
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(backend_dir)

# 检查并打印当前Python路径以便调试
print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

print("\n尝试导入模块...")

# 尝试多种可能的导入路径
try:
    # 方式1: 直接导入
    from backend.app.db.session import get_db
    from backend.app.db.base import Base
    from backend.app.core.security import get_password_hash
    # 使用Service架构代替CRUD
    from backend.app.services.user_service import UserService
    from backend.app.services.category_service import CategoryService
    from backend.app.services.tag_service import TagService
    from backend.app.services.post_service import PostService
    from backend.app.services.comment_service import CommentService
    from backend.app.schemas import (
        UserCreate, 
        CategoryCreate, 
        TagCreate, 
        PostCreate, 
        CommentCreate
    )
    print("成功使用方式1导入模块")
except ImportError as e:
    print(f"方式1导入失败: {e}")
    try:
        # 方式2: 假设在backend目录下运行
        from app.db.session import get_db
        from app.db.base import Base
        from app.core.security import get_password_hash
        # 使用Service架构代替CRUD
        from app.services.user_service import UserService
        from app.services.category_service import CategoryService
        from app.services.tag_service import TagService
        from app.services.post_service import PostService
        from app.services.comment_service import CommentService
        from app.schemas import (
            UserCreate, 
            CategoryCreate, 
            TagCreate, 
            PostCreate, 
            CommentCreate
        )
        print("成功使用方式2导入模块")
    except ImportError as e:
        print(f"方式2导入失败: {e}")
        try:
            # 方式3: 假设结构可能有所不同
            # 这里我们需要确定实际的导入路径
            print("\n请确认正确的导入路径并手动修改脚本")
            print("项目可能使用了不同的模块结构")
            
            # 列出可能的目录结构，帮助定位问题
            print("\n当前目录结构:")
            for root, dirs, files in os.walk(os.path.join(backend_dir, "backend"), topdown=True, maxdepth=3):
                level = root.replace(backend_dir, "").count(os.sep)
                indent = " " * 4 * level
                print(f"{indent}{os.path.basename(root)}/")
                sub_indent = " " * 4 * (level + 1)
                for file in files[:5]:  # 只显示前5个文件，避免输出过多
                    if not file.startswith("__"):
                        print(f"{sub_indent}{file}")
                if len(files) > 5:
                    print(f"{sub_indent}... 等{len(files)-5}个文件")
            
            raise ImportError("无法导入所需模块，请检查项目结构")
        except Exception as e:
            print(f"无法确定正确的导入路径: {e}")
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
        "bio": "站点管理员",
        "role": "admin",
    },
    {
        "username": "zhang_wei",
        "email": "zhang_wei@example.com",
        "password": "password123",
        "bio": "热爱技术，喜欢分享",
        "role": "user",
    },
    {
        "username": "li_na",
        "email": "li_na@example.com",
        "password": "password123",
        "bio": "设计师，对用户体验和界面设计很感兴趣",
        "role": "user",
    },
    {
        "username": "wang_fang",
        "email": "wang_fang@example.com",
        "password": "password123",
        "bio": "后端开发者，专注于性能优化",
        "role": "user",
    }
]

CATEGORIES = [
    {
        "name": "技术讨论",
        "description": "关于编程、软件开发和技术相关的讨论",
        "color": "#3b82f6"
    },
    {
        "name": "产品设计",
        "description": "关于产品设计、用户体验和界面设计的讨论",
        "color": "#10b981"
    },
    {
        "name": "职业发展",
        "description": "关于求职、面试、职业规划等话题的讨论",
        "color": "#f59e0b"
    },
    {
        "name": "项目分享",
        "description": "分享你的项目、代码或创意作品",
        "color": "#8b5cf6"
    },
    {
        "name": "问答求助",
        "description": "技术问题求助和解答",
        "color": "#ef4444"
    },
    {
        "name": "行业动态",
        "description": "讨论IT行业新闻、趋势和事件",
        "color": "#ec4899"
    },
    {
        "name": "闲聊灌水",
        "description": "轻松话题，交友聊天",
        "color": "#6366f1"
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
        "view_count": 1250,
        "vote_count": 45,
        "tag_names": ["FastAPI", "性能优化", "Python"]
    },
    {
        "title": "Vue.js 3组合式API使用指南",
        "content": "Vue.js 3的组合式API提供了一种全新的方式来组织和重用组件逻辑。与Vue 2的选项式API相比，组合式API更加灵活，允许开发者根据逻辑关注点而不是选项类型组织代码。\n\n在这篇文章中，我将介绍组合式API的核心概念，如setup、ref、reactive、computed和watch等，并通过实际例子展示如何使用这些功能来构建高效、可维护的组件。\n\n我们还将讨论如何创建和使用自定义组合函数（Composables）来重用组件逻辑，以及如何在大型应用中有效地组织这些函数。",
        "user_email": "li_na@example.com",
        "category_name": "技术讨论",
        "view_count": 980,
        "vote_count": 38,
        "tag_names": ["Vue.js", "JavaScript"]
    },
    {
        "title": "2023年前端面试常见问题及答案",
        "content": "对于寻找前端开发工作的开发者来说，了解当前的面试趋势和准备常见问题的答案是至关重要的。在这篇文章中，我将分享2023年前端开发面试中最常见的问题，以及如何准备这些问题的答案。\n\n涵盖的主题包括：\n\n- JavaScript基础知识和ES6+特性\n- 框架特定问题（React、Vue、Angular）\n- CSS布局和响应式设计\n- Web性能优化技术\n- 状态管理解决方案\n- 前端安全最佳实践\n- 系统设计问题\n\n此外，我还将提供一些面试策略和技巧，帮助你在面试过程中表现出色，展示你的技能和经验。",
        "user_email": "zhang_wei@example.com",
        "category_name": "职业发展",
        "view_count": 2450,
        "vote_count": 120,
        "tag_names": ["JavaScript", "Vue.js", "React", "求职", "面试"]
    },
    {
        "title": "用户体验设计中的心理学原理",
        "content": "优秀的用户体验设计不仅仅是关于美观的界面，更是关于理解用户的心理和行为模式。了解基本的心理学原理可以帮助设计师创造更有效、更令人愉悦的用户体验。\n\n在这篇文章中，我将探讨以下几个对UX设计至关重要的心理学原理：\n\n- 格式塔原理（接近性、相似性、连续性等）\n- 希克定律（选择增加时决策时间增加）\n- 菲茨定律（点击目标的大小与距离关系）\n- 认知负荷理论\n- 锚定效应\n- 确认偏误\n- 峰终定律\n\n通过实际的设计案例，我将展示如何应用这些原理来改善用户体验，提高用户参与度和满意度。",
        "user_email": "li_na@example.com",
        "category_name": "产品设计",
        "view_count": 1850,
        "vote_count": 88,
        "tag_names": ["UI设计", "UX研究", "产品管理"]
    },
    {
        "title": "构建高可用的微服务架构",
        "content": "微服务架构已经成为构建大型、复杂应用程序的流行方法，但它也带来了许多新的挑战，尤其是在高可用性方面。在这篇文章中，我将分享我在构建和维护高可用微服务系统中获得的经验和最佳实践。\n\n主要内容包括：\n\n- 微服务设计原则与模式\n- 服务发现与注册\n- 负载均衡策略\n- 断路器模式与故障隔离\n- 分布式跟踪与监控\n- 自动扩展与自我修复\n- 一致性与最终一致性权衡\n- 数据管理策略\n\n我将使用实际案例来说明这些概念，并提供具体的实现建议，帮助你设计和构建更加可靠、可伸缩的微服务系统。",
        "user_email": "wang_fang@example.com",
        "category_name": "技术讨论",
        "view_count": 1550,
        "vote_count": 72,
        "tag_names": ["性能优化", "数据库", "云服务"]
    }
]

COMMENTS = [
    {
        "content": "非常详细的教程，感谢分享！我最近也在学习FastAPI，这篇文章对我帮助很大。",
        "user_email": "zhang_wei@example.com",
        "post_title": "使用FastAPI构建高性能API",
        "likes": 8
    },
    {
        "content": "我有一个问题，在处理大量并发请求时，FastAPI和Flask相比有多大的性能提升？有没有具体的benchmark数据？",
        "user_email": "wang_fang@example.com",
        "post_title": "使用FastAPI构建高性能API",
        "likes": 5
    },
    {
        "content": "组合式API确实提供了更好的代码组织方式，但对于习惯了选项式API的开发者来说，学习曲线还是有点陡峭。不过你的解释很清晰，谢谢！",
        "user_email": "admin@example.com",
        "post_title": "Vue.js 3组合式API使用指南",
        "likes": 12
    },
    {
        "content": "峰终定律在设计用户旅程时特别重要，我在我们的产品中应用了这个原理，用户满意度确实有所提高。建议可以添加一些关于如何在表单设计中应用这个原理的具体例子。",
        "user_email": "zhang_wei@example.com",
        "post_title": "用户体验设计中的心理学原理",
        "likes": 15
    },
    {
        "content": "这篇文章正是我需要的！下周有几场前端面试，这些题目和答案帮我梳理了很多知识点。特别是关于状态管理的部分，讲得很全面。",
        "user_email": "li_na@example.com",
        "post_title": "2023年前端面试常见问题及答案",
        "likes": 20
    },
    {
        "content": "关于断路器模式的部分讲得很好，但我想知道在实际项目中，你是使用像Hystrix这样的库还是自己实现的断路器逻辑？",
        "user_email": "admin@example.com",
        "post_title": "构建高可用的微服务架构",
        "likes": 7
    }
]

async def seed_forum_data(db, clear_existing=False):
    """向数据库添加论坛种子数据"""
    print("开始导入论坛数据...")
    
    # 如果需要清除现有数据，可以在这里操作
    if clear_existing:
        print("清除现有数据...")
        # 这里根据实际的数据库结构清除数据
        # 通常应该按照依赖关系的反序删除
        await db.execute("DELETE FROM post_tags")
        await db.execute("DELETE FROM comments")
        await db.execute("DELETE FROM posts")
        await db.execute("DELETE FROM tags")
        await db.execute("DELETE FROM categories")
        await db.execute("DELETE FROM users")
        await db.commit()
    
    # 创建服务实例
    user_service = UserService()
    category_service = CategoryService()
    tag_service = TagService()
    post_service = PostService()
    comment_service = CommentService()
    
    # 添加用户
    user_db_objects = {}
    for user_data in USERS:
        print(f"添加用户: {user_data['username']}")
        
        # 检查用户是否已存在
        existing_user = await user_service.get_user_by_email(user_data["email"])
        if existing_user:
            print(f"用户 {user_data['username']} 已存在，跳过")
            user_db_objects[user_data["email"]] = existing_user
            continue
        
        # 创建用户
        user_in = UserCreate(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            bio=user_data.get("bio", ""),
            role=user_data.get("role", "user")
        )
        
        created_user = await user_service.create_user(user_in.model_dump())
        user_db_objects[user_data["email"]] = created_user
    
    # 添加分类
    category_db_objects = {}
    for cat_data in CATEGORIES:
        print(f"添加分类: {cat_data['name']}")
        
        # 检查分类是否已存在
        existing_category = await category_service.get_category_by_name(cat_data["name"])
        if existing_category:
            print(f"分类 {cat_data['name']} 已存在，跳过")
            category_db_objects[cat_data["name"]] = existing_category
            continue
        
        # 创建分类
        category_in = CategoryCreate(
            name=cat_data["name"],
            description=cat_data["description"],
            color=cat_data.get("color", "#3b82f6")
        )
        
        created_category = await category_service.create_category(category_in.model_dump())
        category_db_objects[cat_data["name"]] = created_category
    
    # 添加标签
    tag_db_objects = {}
    for tag_data in TAGS:
        print(f"添加标签: {tag_data['name']}")
        
        # 检查标签是否已存在
        existing_tag = await tag_service.get_tag_by_name(tag_data["name"])
        if existing_tag:
            print(f"标签 {tag_data['name']} 已存在，跳过")
            tag_db_objects[tag_data["name"]] = existing_tag
            continue
        
        # 创建标签
        tag_in = TagCreate(
            name=tag_data["name"],
            description=tag_data.get("description", "")
        )
        
        created_tag = await tag_service.create_tag(tag_in.model_dump())
        tag_db_objects[tag_data["name"]] = created_tag
    
    # 添加帖子
    post_db_objects = {}
    for post_data in POSTS:
        print(f"添加帖子: {post_data['title']}")
        
        # 检查帖子是否已存在
        existing_post = await post_service.get_post_by_title(post_data["title"])
        if existing_post:
            print(f"帖子 {post_data['title']} 已存在，跳过")
            post_db_objects[post_data["title"]] = existing_post
            continue
        
        # 获取作者信息
        author_email = post_data["user_email"]
        author = user_db_objects.get(author_email)
        if not author:
            print(f"作者 {author_email} 未找到，跳过帖子创建")
            continue
            
        # 获取分类信息
        category_name = post_data["category_name"]
        category = category_db_objects.get(category_name)
        if not category:
            print(f"分类 {category_name} 未找到，跳过帖子创建")
            continue
            
        # 获取标签信息
        tag_names = post_data["tag_names"]
        tag_ids = []
        for tag_name in tag_names:
            tag = tag_db_objects.get(tag_name)
            if tag:
                tag_ids.append(tag["id"])
            else:
                print(f"标签 {tag_name} 未找到，将被忽略")
        
        # 创建帖子
        post_in = {
            "title": post_data["title"],
            "content": post_data["content"],
            "user_id": author["id"],
            "category_id": category["id"],
            "tags": tag_ids,
            "is_pinned": False,
            "visibility": "public"
        }
        
        created_post = await post_service.create_post(post_in, author["id"])
        post_db_objects[post_data["title"]] = created_post
    
    # 添加评论
    for comment_data in COMMENTS:
        print(f"添加评论到帖子: {comment_data['post_title']}")
        
        # 获取帖子信息
        post_title = comment_data["post_title"]
        post = post_db_objects.get(post_title)
        if not post:
            print(f"帖子 {post_title} 未找到，跳过评论创建")
            continue
            
        # 获取作者信息
        author_email = comment_data["user_email"]
        author = user_db_objects.get(author_email)
        if not author:
            print(f"作者 {author_email} 未找到，跳过评论创建")
            continue
            
        # 创建评论
        comment_in = {
            "content": comment_data["content"],
            "post_id": post["id"],
            "user_id": author["id"]
        }
        
        await comment_service.create_comment(comment_in, author["id"])
        print(f"已添加评论到帖子: {post_title}")
    
    print("论坛数据导入完成")

async def main():
    """主函数，运行种子数据导入"""
    # 解析命令行参数
    clear_data = "--clear" in sys.argv
    
    if clear_data:
        print("警告: 将清除所有现有数据!")
        response = input("确定要继续吗? (y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("操作已取消")
            return
    
    # 获取数据库会话
    try:
        print("尝试连接数据库...")
        # 尝试多种可能的获取数据库会话的方式
        try:
            db_generator = get_db()
            db = next(db_generator)
            print("成功获取数据库会话（同步方式）")
        except (TypeError, StopIteration):
            try:
                db_generator = get_db()
                db = await db_generator.__anext__()
                print("成功获取数据库会话（异步方式）")
            except Exception as e:
                print(f"无法获取数据库会话: {e}")
                
                # 尝试直接连接数据库（假设使用SQLAlchemy）
                print("尝试直接连接数据库...")
                try:
                    from sqlalchemy import create_engine
                    from sqlalchemy.orm import sessionmaker
                    
                    # 尝试读取环境变量中的数据库连接字符串
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()
                    
                    db_url = os.getenv("DATABASE_URL", "sqlite:///./forum.db")
                    engine = create_engine(db_url)
                    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                    db = SessionLocal()
                    print(f"成功直接连接到数据库: {db_url}")
                except Exception as db_err:
                    print(f"无法直接连接数据库: {db_err}")
                    raise
        
        await seed_forum_data(db, clear_existing=clear_data)
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
    # 运行异步主函数
    asyncio.run(main()) 