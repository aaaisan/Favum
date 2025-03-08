import asyncio
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.post import Post
from app.db.models.comment import Comment
from app.db.models.category import Category
from app.db.models.section import Section
from app.db.models.tag import Tag

async def query_users():
    """查询用户表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print('\n用户数据:')
        print('-' * 80)
        for user in users:
            print(f'ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}')

async def query_posts():
    """查询帖子表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Post))
        posts = result.scalars().all()
        
        print('\n帖子数据:')
        print('-' * 80)
        for post in posts:
            print(f'ID: {post.id}, 标题: {post.title}, 作者ID: {post.author_id}, 分类ID: {post.category_id}')

async def query_comments():
    """查询评论表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Comment))
        comments = result.scalars().all()
        
        print('\n评论数据:')
        print('-' * 80)
        for comment in comments:
            print(f'ID: {comment.id}, 内容: {comment.content[:30]}..., 作者ID: {comment.author_id}, 帖子ID: {comment.post_id}')

async def query_categories():
    """查询分类表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        
        print('\n分类数据:')
        print('-' * 80)
        for category in categories:
            print(f'ID: {category.id}, 名称: {category.name}, 描述: {category.description}')

async def query_sections():
    """查询版块表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Section))
        sections = result.scalars().all()
        
        print('\n版块数据:')
        print('-' * 80)
        for section in sections:
            print(f'ID: {section.id}, 名称: {section.name}, 描述: {section.description}')

async def query_tags():
    """查询标签表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tag))
        tags = result.scalars().all()
        
        print('\n标签数据:')
        print('-' * 80)
        for tag in tags:
            print(f'ID: {tag.id}, 名称: {tag.name}')

async def main():
    """查询数据库中的所有表"""
    await query_users()
    await query_posts()
    await query_comments()
    await query_categories()
    await query_sections()
    await query_tags()

if __name__ == "__main__":
    asyncio.run(main()) 