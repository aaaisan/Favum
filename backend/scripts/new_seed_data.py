import os
import sys
import asyncio
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any, Optional
from passlib.context import CryptContext
import logging
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入项目模块
try:
    from app.db.database import get_db, SessionLocal, Base
    from app.db.models import User, Category, Tag, Post, Comment, Section, post_tags, UserRole, PostVote, VoteType
    from app.core.config import settings
    logger.info("成功导入项目模块")
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """获取密码的哈希值"""
    return pwd_context.hash(password)

def get_random_date(start_date, end_date):
    """生成两个日期之间的随机日期"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# 种子数据定义
USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "role": UserRole.ADMIN,
    },
    {
        "username": "zhang_wei",
        "email": "zhang_wei@example.com",
        "password": "password123",
        "role": UserRole.USER,
    },
    {
        "username": "li_na",
        "email": "li_na@example.com",
        "password": "password123",
        "role": UserRole.USER,
    },
    {
        "username": "wang_fang",
        "email": "wang_fang@example.com",
        "password": "password123",
        "role": UserRole.USER,
    },
    {
        "username": "zhao_ming",
        "email": "zhao_ming@example.com",
        "password": "password123",
        "role": UserRole.MODERATOR,
    }
]

SECTIONS = [
    {
        "name": "主论坛",
        "description": "主要讨论区，包含所有一般性话题"
    },
    {
        "name": "技术专区",
        "description": "专注于技术相关讨论的版块"
    },
    {
        "name": "休闲娱乐",
        "description": "轻松话题，交友聊天的地方"
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
        "author_username": "admin",
        "category_name": "技术讨论",
        "section_name": "技术专区",
        "tag_names": ["FastAPI", "性能优化", "Python"]
    },
    {
        "title": "Vue.js 3组合式API使用指南",
        "content": "Vue.js 3的组合式API提供了一种全新的方式来组织和重用组件逻辑。与Vue 2的选项式API相比，组合式API更加灵活，允许开发者根据逻辑关注点而不是选项类型组织代码。\n\n在这篇文章中，我将介绍组合式API的核心概念，如setup、ref、reactive、computed和watch等，并通过实际例子展示如何使用这些功能来构建高效、可维护的组件。\n\n我们还将讨论如何创建和使用自定义组合函数（Composables）来重用组件逻辑，以及如何在大型应用中有效地组织这些函数。",
        "author_username": "li_na",
        "category_name": "技术讨论",
        "section_name": "技术专区",
        "tag_names": ["Vue.js", "JavaScript"]
    },
    {
        "title": "2023年前端面试常见问题及答案",
        "content": "对于寻找前端开发工作的开发者来说，了解当前的面试趋势和准备常见问题的答案是至关重要的。在这篇文章中，我将分享2023年前端开发面试中最常见的问题，以及如何准备这些问题的答案。\n\n涵盖的主题包括：\n\n- JavaScript基础知识和ES6+特性\n- 框架特定问题（React、Vue、Angular）\n- CSS布局和响应式设计\n- Web性能优化技术\n- 状态管理解决方案\n- 前端安全最佳实践\n- 系统设计问题\n\n此外，我还将提供一些面试策略和技巧，帮助你在面试过程中表现出色，展示你的技能和经验。",
        "author_username": "zhang_wei",
        "category_name": "职业发展",
        "section_name": "主论坛",
        "tag_names": ["JavaScript", "Vue.js", "React", "求职", "面试"]
    },
    {
        "title": "用户体验设计中的心理学原理",
        "content": "优秀的用户体验设计不仅仅是关于美观的界面，更是关于理解用户的心理和行为模式。了解基本的心理学原理可以帮助设计师创造更有效、更令人愉悦的用户体验。\n\n在这篇文章中，我将探讨以下几个对UX设计至关重要的心理学原理：\n\n- 格式塔原理（接近性、相似性、连续性等）\n- 希克定律（选择增加时决策时间增加）\n- 菲茨定律（点击目标的大小与距离关系）\n- 认知负荷理论\n- 锚定效应\n- 确认偏误\n- 峰终定律\n\n通过实际的设计案例，我将展示如何应用这些原理来改善用户体验，提高用户参与度和满意度。",
        "author_username": "li_na",
        "category_name": "产品设计",
        "section_name": "主论坛",
        "tag_names": ["UI设计", "UX研究", "产品管理"]
    },
    {
        "title": "构建高可用的微服务架构",
        "content": "微服务架构已经成为构建大型、复杂应用程序的流行方法，但它也带来了许多新的挑战，尤其是在高可用性方面。在这篇文章中，我将分享我在构建和维护高可用微服务系统中获得的经验和最佳实践。\n\n主要内容包括：\n\n- 微服务设计原则与模式\n- 服务发现与注册\n- 负载均衡策略\n- 断路器模式与故障隔离\n- 分布式跟踪与监控\n- 自动扩展与自我修复\n- 一致性与最终一致性权衡\n- 数据管理策略\n\n我将使用实际案例来说明这些概念，并提供具体的实现建议，帮助你设计和构建更加可靠、可伸缩的微服务系统。",
        "author_username": "wang_fang",
        "category_name": "技术讨论",
        "section_name": "技术专区",
        "tag_names": ["性能优化", "数据库", "云服务"]
    },
    {
        "title": "人工智能在前端开发中的应用",
        "content": "人工智能技术正在改变各个行业，前端开发也不例外。在这篇文章中，我将探讨AI如何融入现代前端开发流程，提高开发效率和用户体验。\n\n我们将讨论以下几个主题：\n\n1. AI辅助代码生成与补全工具\n2. 智能UI组件与设计系统\n3. 用户行为分析与个性化体验\n4. 语音识别与自然语言处理在前端的应用\n5. AI驱动的测试和调试工具\n6. 未来发展趋势\n\n通过具体案例，我将展示如何在实际项目中整合这些AI技术，并分享实施过程中的经验和教训。",
        "author_username": "zhao_ming",
        "category_name": "技术讨论",
        "section_name": "主论坛",
        "tag_names": ["人工智能", "JavaScript", "UI设计"]
    },
    {
        "title": "从初级到高级开发者的进阶路线",
        "content": "在软件开发领域，从初级进阶到高级开发者不仅仅是时间的积累，更需要有意识地提升各方面能力。本文将分享一条实用的进阶路线图，帮助初中级开发者规划职业成长。\n\n关键成长阶段包括：\n\n1. 扎实的基础知识与计算机科学原理\n2. 核心编程能力与代码质量意识\n3. 系统设计与架构能力\n4. 技术广度与跨领域知识\n5. 沟通与协作能力\n6. 技术领导力\n7. 业务敏感度与商业思维\n\n每个阶段我都会提供具体的学习资源、实践项目建议和评估标准，帮助你确认当前所处的阶段并找到下一步的发展方向。",
        "author_username": "admin",
        "category_name": "职业发展",
        "section_name": "主论坛",
        "tag_names": ["职业发展", "编程"]
    }
]

COMMENTS = [
    {
        "content": "非常详细的教程，感谢分享！我最近也在学习FastAPI，这篇文章对我帮助很大。",
        "author_username": "zhang_wei",
        "post_title": "使用FastAPI构建高性能API"
    },
    {
        "content": "我有一个问题，在处理大量并发请求时，FastAPI和Flask相比有多大的性能提升？有没有具体的benchmark数据？",
        "author_username": "wang_fang",
        "post_title": "使用FastAPI构建高性能API"
    },
    {
        "content": "组合式API确实提供了更好的代码组织方式，但对于习惯了选项式API的开发者来说，学习曲线还是有点陡峭。不过你的解释很清晰，谢谢！",
        "author_username": "admin",
        "post_title": "Vue.js 3组合式API使用指南"
    },
    {
        "content": "峰终定律在设计用户旅程时特别重要，我在我们的产品中应用了这个原理，用户满意度确实有所提高。建议可以添加一些关于如何在表单设计中应用这个原理的具体例子。",
        "author_username": "zhang_wei",
        "post_title": "用户体验设计中的心理学原理"
    },
    {
        "content": "关于断路器模式，你有没有推荐的开源实现？我正在构建一个微服务系统，需要一个可靠的断路器解决方案。",
        "author_username": "li_na",
        "post_title": "构建高可用的微服务架构"
    },
    {
        "content": "虽然AI在前端的应用很有前景，但我担心过度依赖AI工具会影响开发者对底层技术的理解。你认为开发者应该如何平衡使用这些工具和深入学习基础知识？",
        "author_username": "wang_fang",
        "post_title": "人工智能在前端开发中的应用"
    },
    {
        "content": "这篇文章来得正是时候，我正在准备前端面试。关于状态管理解决方案，能否详细解释一下在大型应用中Pinia相比Vuex的优势？",
        "author_username": "zhao_ming",
        "post_title": "2023年前端面试常见问题及答案"
    },
    {
        "content": "非常感谢分享这个进阶路线图！我特别认同技术广度与深度需要平衡的观点。你能分享一下你是如何在工作中兼顾这两者的吗？",
        "author_username": "li_na",
        "post_title": "从初级到高级开发者的进阶路线"
    }
]

VOTES = [
    {"post_title": "使用FastAPI构建高性能API", "username": "zhang_wei", "vote_type": VoteType.UPVOTE},
    {"post_title": "使用FastAPI构建高性能API", "username": "li_na", "vote_type": VoteType.UPVOTE},
    {"post_title": "使用FastAPI构建高性能API", "username": "zhao_ming", "vote_type": VoteType.UPVOTE},
    {"post_title": "Vue.js 3组合式API使用指南", "username": "admin", "vote_type": VoteType.UPVOTE},
    {"post_title": "Vue.js 3组合式API使用指南", "username": "wang_fang", "vote_type": VoteType.UPVOTE},
    {"post_title": "2023年前端面试常见问题及答案", "username": "li_na", "vote_type": VoteType.UPVOTE},
    {"post_title": "2023年前端面试常见问题及答案", "username": "zhao_ming", "vote_type": VoteType.UPVOTE},
    {"post_title": "用户体验设计中的心理学原理", "username": "zhang_wei", "vote_type": VoteType.UPVOTE},
    {"post_title": "用户体验设计中的心理学原理", "username": "wang_fang", "vote_type": VoteType.UPVOTE},
    {"post_title": "构建高可用的微服务架构", "username": "admin", "vote_type": VoteType.UPVOTE},
    {"post_title": "构建高可用的微服务架构", "username": "li_na", "vote_type": VoteType.UPVOTE},
    {"post_title": "人工智能在前端开发中的应用", "username": "wang_fang", "vote_type": VoteType.UPVOTE},
    {"post_title": "人工智能在前端开发中的应用", "username": "zhang_wei", "vote_type": VoteType.UPVOTE},
    {"post_title": "从初级到高级开发者的进阶路线", "username": "li_na", "vote_type": VoteType.UPVOTE},
    {"post_title": "从初级到高级开发者的进阶路线", "username": "zhao_ming", "vote_type": VoteType.UPVOTE}
]

def seed_database(clear_existing: bool = False):
    """向数据库中填充种子数据"""
    # 使用同步会话进行数据库操作
    db = SessionLocal()
    
    try:
        logger.info("开始填充数据库...")
        
        # 如果需要清除现有数据
        if clear_existing:
            logger.info("清除所有现有数据...")
            clear_all_data(db)
        
        # 创建用户
        users_map = create_users(db)
        
        # 创建版块
        sections_map = create_sections(db)
        
        # 创建分类
        categories_map = create_categories(db)
        
        # 创建标签
        tags_map = create_tags(db)
        
        # 创建帖子并关联标签
        posts_map = create_posts(db, users_map, categories_map, sections_map, tags_map)
        
        # 创建评论
        create_comments(db, posts_map, users_map)
        
        # 添加投票
        create_votes(db, posts_map, users_map)
        
        # 更新统计数据
        update_statistics(db)
        
        logger.info("数据填充完成！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"填充数据时出错: {str(e)}")
        raise
    finally:
        db.close()

def clear_all_data(db: Session):
    """清除数据库中的所有现有数据"""
    try:
        # 按依赖关系顺序删除
        db.execute("DELETE FROM post_votes")
        db.execute("DELETE FROM post_favorites")
        db.execute("DELETE FROM post_tags")
        db.execute("DELETE FROM comments")
        db.execute("DELETE FROM posts")
        db.execute("DELETE FROM section_moderators")
        db.execute("DELETE FROM tags")
        db.execute("DELETE FROM categories")
        db.execute("DELETE FROM sections")
        db.execute("DELETE FROM users")
        db.commit()
        logger.info("成功清除所有现有数据")
    except Exception as e:
        db.rollback()
        logger.error(f"清除数据时出错: {str(e)}")
        raise

def create_users(db: Session) -> Dict[str, User]:
    """创建用户并返回用户名到用户对象的映射"""
    users_map = {}
    
    for user_data in USERS:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            logger.info(f"用户 {user_data['username']} 已存在，跳过")
            users_map[user_data["username"]] = existing_user
            continue
        
        # 创建新用户
        hashed_password = get_password_hash(user_data["password"])
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            role=user_data["role"],
            is_active=True,
            created_at=datetime.now() - timedelta(days=random.randint(10, 60))
        )
        
        db.add(user)
        db.flush()  # 获取生成的ID
        
        users_map[user_data["username"]] = user
        logger.info(f"创建用户: {user_data['username']}")
    
    db.commit()
    logger.info(f"成功创建 {len(users_map)} 名用户")
    return users_map

def create_sections(db: Session) -> Dict[str, Section]:
    """创建版块并返回版块名到版块对象的映射"""
    sections_map = {}
    
    for section_data in SECTIONS:
        # 检查版块是否已存在
        existing_section = db.query(Section).filter(Section.name == section_data["name"]).first()
        
        if existing_section:
            logger.info(f"版块 {section_data['name']} 已存在，跳过")
            sections_map[section_data["name"]] = existing_section
            continue
        
        # 创建新版块
        section = Section(
            name=section_data["name"],
            description=section_data["description"],
            created_at=datetime.now() - timedelta(days=random.randint(30, 90))
        )
        
        db.add(section)
        db.flush()  # 获取生成的ID
        
        sections_map[section_data["name"]] = section
        logger.info(f"创建版块: {section_data['name']}")
    
    db.commit()
    logger.info(f"成功创建 {len(sections_map)} 个版块")
    return sections_map

def create_categories(db: Session) -> Dict[str, Category]:
    """创建分类并返回分类名到分类对象的映射"""
    categories_map = {}
    
    for category_data in CATEGORIES:
        # 检查分类是否已存在
        existing_category = db.query(Category).filter(Category.name == category_data["name"]).first()
        
        if existing_category:
            logger.info(f"分类 {category_data['name']} 已存在，跳过")
            categories_map[category_data["name"]] = existing_category
            continue
        
        # 创建新分类
        category = Category(
            name=category_data["name"],
            description=category_data["description"],
            order=category_data["order"],
            created_at=datetime.now() - timedelta(days=random.randint(30, 90))
        )
        
        db.add(category)
        db.flush()  # 获取生成的ID
        
        categories_map[category_data["name"]] = category
        logger.info(f"创建分类: {category_data['name']}")
    
    db.commit()
    logger.info(f"成功创建 {len(categories_map)} 个分类")
    return categories_map

def create_tags(db: Session) -> Dict[str, Tag]:
    """创建标签并返回标签名到标签对象的映射"""
    tags_map = {}
    
    for tag_data in TAGS:
        # 检查标签是否已存在
        existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
        
        if existing_tag:
            logger.info(f"标签 {tag_data['name']} 已存在，跳过")
            tags_map[tag_data["name"]] = existing_tag
            continue
        
        # 创建新标签
        tag = Tag(
            name=tag_data["name"],
            created_at=datetime.now() - timedelta(days=random.randint(30, 90))
        )
        
        db.add(tag)
        db.flush()  # 获取生成的ID
        
        tags_map[tag_data["name"]] = tag
        logger.info(f"创建标签: {tag_data['name']}")
    
    db.commit()
    logger.info(f"成功创建 {len(tags_map)} 个标签")
    return tags_map

def create_posts(db: Session, users_map: Dict[str, User], categories_map: Dict[str, Category], 
                 sections_map: Dict[str, Section], tags_map: Dict[str, Tag]) -> Dict[str, Post]:
    """创建帖子并返回帖子标题到帖子对象的映射"""
    posts_map = {}
    
    for post_data in POSTS:
        # 检查帖子是否已存在
        existing_post = db.query(Post).filter(Post.title == post_data["title"]).first()
        
        if existing_post:
            logger.info(f"帖子 '{post_data['title']}' 已存在，跳过")
            posts_map[post_data["title"]] = existing_post
            continue
        
        # 获取作者、分类和版块
        author = users_map.get(post_data["author_username"])
        category = categories_map.get(post_data["category_name"])
        section = sections_map.get(post_data["section_name"])
        
        if not author or not category or not section:
            logger.warning(f"找不到帖子 '{post_data['title']}' 的作者、分类或版块，跳过")
            continue
        
        # 生成随机创建时间（过去30天内）
        now = datetime.now()
        created_at = get_random_date(now - timedelta(days=30), now)
        
        # 创建新帖子
        post = Post(
            title=post_data["title"],
            content=post_data["content"],
            author_id=author.id,
            category_id=category.id,
            section_id=section.id,
            created_at=created_at,
            updated_at=created_at,
            vote_count=0  # 初始投票数为0，后面会更新
        )
        
        db.add(post)
        db.flush()  # 获取生成的ID
        
        # 添加标签
        for tag_name in post_data["tag_names"]:
            tag = tags_map.get(tag_name)
            if tag:
                post.tags.append(tag)
        
        posts_map[post_data["title"]] = post
        logger.info(f"创建帖子: '{post_data['title']}'")
    
    db.commit()
    logger.info(f"成功创建 {len(posts_map)} 篇帖子")
    return posts_map

def create_comments(db: Session, posts_map: Dict[str, Post], users_map: Dict[str, User]):
    """创建评论"""
    for comment_data in COMMENTS:
        # 获取帖子和作者
        post = posts_map.get(comment_data["post_title"])
        author = users_map.get(comment_data["author_username"])
        
        if not post or not author:
            logger.warning(f"找不到评论的帖子或作者，跳过")
            continue
        
        # 生成随机创建时间（帖子创建时间之后）
        created_at = get_random_date(post.created_at, datetime.now())
        
        # 创建新评论
        comment = Comment(
            content=comment_data["content"],
            author_id=author.id,
            post_id=post.id,
            created_at=created_at
        )
        
        db.add(comment)
    
    db.commit()
    logger.info(f"成功创建 {len(COMMENTS)} 条评论")

def create_votes(db: Session, posts_map: Dict[str, Post], users_map: Dict[str, User]):
    """创建投票"""
    for vote_data in VOTES:
        # 获取帖子和用户
        post = posts_map.get(vote_data["post_title"])
        user = users_map.get(vote_data["username"])
        
        if not post or not user:
            logger.warning(f"找不到投票的帖子或用户，跳过")
            continue
        
        # 检查是否已有投票记录
        existing_vote = db.query(PostVote).filter(
            PostVote.post_id == post.id,
            PostVote.user_id == user.id
        ).first()
        
        if existing_vote:
            logger.info(f"用户 {vote_data['username']} 已对帖子 '{vote_data['post_title']}' 投票，跳过")
            continue
        
        # 创建新投票
        vote = PostVote(
            post_id=post.id,
            user_id=user.id,
            vote_type=vote_data["vote_type"],
            created_at=datetime.now() - timedelta(days=random.randint(0, 10))
        )
        
        db.add(vote)
        
        # 更新帖子的投票计数
        if vote_data["vote_type"] == VoteType.UPVOTE:
            post.vote_count += 1
        elif vote_data["vote_type"] == VoteType.DOWNVOTE:
            post.vote_count -= 1
    
    db.commit()
    logger.info(f"成功创建 {len(VOTES)} 条投票")

def update_statistics(db: Session):
    """更新统计数据，如帖子数、评论数等"""
    # 更新帖子的评论计数
    posts = db.query(Post).all()
    for post in posts:
        comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
        post.comment_count = comment_count
    
    # 更新标签的帖子计数
    tags = db.query(Tag).all()
    for tag in tags:
        post_count = db.query(post_tags).filter(post_tags.c.tag_id == tag.id).count()
        tag.post_count = post_count
        tag.last_used_at = datetime.now() - timedelta(days=random.randint(0, 30))
    
    db.commit()
    logger.info("成功更新统计数据")

# 运行脚本
if __name__ == "__main__":
    # 检查命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description="论坛数据库种子脚本")
    parser.add_argument("--clear", action="store_true", help="清除所有现有数据")
    
    args = parser.parse_args()
    
    print("开始导入数据...")
    if args.clear:
        print("将清除所有现有数据")
        response = input("确定要清除所有数据吗？这个操作不可逆！(y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("操作已取消")
            sys.exit(0)
    
    # 运行函数
    seed_database(clear_existing=args.clear)
    
    print("数据导入完成！") 