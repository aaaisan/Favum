from typing import Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.expression import select
from sqlalchemy import and_, or_

from .models import Base, User
from ..core.exceptions import NotFoundError

class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def get_by_id(
        db: Session,
        model: Any,
        id: Any,
        options: Optional[List[Any]] = None,
        error_detail: Optional[str] = None
    ) -> Any:
        """通过ID获取记录"""
        query = select(model).where(model.id == id)
        if options:
            for option in options:
                query = query.options(option)
        
        result = db.execute(query).scalar_one_or_none()
        if not result and error_detail:
            raise NotFoundError(detail=error_detail)
        return result
    
    @staticmethod
    def get_multi(
        db: Session,
        model: Any,
        *,
        skip: int = 0,
        limit: int = 100,
        options: Optional[List[Any]] = None,
        filters: Optional[List[Any]] = None
    ) -> List[Any]:
        """获取多条记录"""
        query = select(model)
        
        if filters:
            query = query.where(and_(*filters))
        
        if options:
            for option in options:
                query = query.options(option)
        
        return list(db.execute(query.offset(skip).limit(limit)).scalars())
    
    @staticmethod
    def get_by_field(
        db: Session,
        model: Any,
        field_name: str,
        value: Any,
        options: Optional[List[Any]] = None
    ) -> Optional[Any]:
        """通过字段获取记录"""
        query = select(model).where(getattr(model, field_name) == value)
        if options:
            for option in options:
                query = query.options(option)
        return db.execute(query).scalar_one_or_none()

class UserQuery:
    """用户查询优化器"""
    
    @staticmethod
    def get_user_with_posts(db: Session, user_id: int):
        """获取用户及其帖子"""
        return QueryOptimizer.get_by_id(
            db,
            User,
            user_id,
            options=[joinedload(User.posts)],
            error_detail="用户不存在"
        )
    
    @staticmethod
    def get_user_with_comments(db: Session, user_id: int):
        """获取用户及其评论"""
        return QueryOptimizer.get_by_id(
            db,
            User,
            user_id,
            options=[joinedload(User.comments)],
            error_detail="用户不存在"
        )
    
    @staticmethod
    def get_user_posts(
        db: Session, 
        user_id: int, 
        skip: int = 0,
        limit: int = 20,
        include_section: bool = True
    ) -> List[Any]:
        """
        获取用户发布的所有帖子
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_section: 是否包含版块信息
            
        Returns:
            List[Any]: 帖子列表
            
        Raises:
            NotFoundError: 当用户不存在时抛出
        """
        # 导入必要的模型，避免循环导入
        from .models import Post
        
        # 验证用户是否存在
        user = QueryOptimizer.get_by_id(
            db, 
            User, 
            user_id,
            error_detail=f"ID为{user_id}的用户不存在"
        )
        
        # 准备过滤条件
        filters = [Post.user_id == user_id]
        
        # 准备连接选项
        options = []
        if include_section:
            options.append(joinedload(Post.section))
        
        # 查询帖子
        posts = QueryOptimizer.get_multi(
            db,
            Post,
            skip=skip,
            limit=limit,
            filters=filters,
            options=options
        )
        
        return posts

class BoardQuery:
    """版块查询优化器"""
    
    @staticmethod
    def get_board_posts(
        db: Session, 
        board_id: int, 
        skip: int = 0,
        limit: int = 20,
        include_user: bool = True
    ) -> List[Any]:
        """
        获取指定版块的所有帖子
        
        Args:
            db: 数据库会话
            board_id: 版块ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_user: 是否包含用户信息
            
        Returns:
            List[Any]: 帖子列表
            
        Raises:
            NotFoundError: 当版块不存在时抛出
        """
        # 导入必要的模型，避免循环导入
        from .models import Post, Board
        
        # 验证版块是否存在
        board = QueryOptimizer.get_by_id(
            db, 
            Board, 
            board_id,
            error_detail=f"ID为{board_id}的版块不存在"
        )
        
        # 准备过滤条件
        filters = [Post.board_id == board_id]
        
        # 准备连接选项
        options = []
        if include_user:
            options.append(joinedload(Post.user))
        
        # 查询帖子
        posts = QueryOptimizer.get_multi(
            db,
            Post,
            skip=skip,
            limit=limit,
            filters=filters,
            options=options
        )
        
        return posts 