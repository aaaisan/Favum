from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException, Request, status
from typing import List
from typing import List, Optional
from ...schemas.section import SectionCreate, Section, SectionUpdate
from ...schemas import post as post_schema
from ...services.section_service import SectionService
from ...core.exceptions import BusinessException
from ...utils.api_decorators import public_endpoint, admin_endpoint

router = APIRouter()

@router.post("/", response_model=Section)
@admin_endpoint(custom_message="创建版块失败")
async def create_section(
    request: Request,
    section: SectionCreate
):
    """创建新版块
    
    创建一个新的论坛版块。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section: 版块创建模型，包含版块信息
        
    Returns:
        Section: 创建成功的版块信息
        
    Raises:
        HTTPException: 当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 创建版块
        result = await section_service.create_section(section.model_dump())
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/", response_model=List[Section])
@public_endpoint(cache_ttl=300, custom_message="获取版块列表失败")
async def read_sections(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """获取版块列表
    
    获取所有论坛版块的列表，支持分页。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        List[Section]: 版块列表
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 获取版块列表
        sections, _ = await section_service.get_sections(skip=skip, limit=limit)
        return sections
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{section_id}", response_model=Section)
@public_endpoint(cache_ttl=300, custom_message="获取版块详情失败")
async def read_section(
    request: Request,
    section_id: int
):
    """获取版块详情
    
    获取指定版块的详细信息。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        
    Returns:
        Section: 版块详细信息
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 获取版块详情
        section = await section_service.get_section_detail(section_id)
        return section
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.put("/{section_id}", response_model=Section)
@admin_endpoint(custom_message="更新版块失败")
async def update_section(
    request: Request,
    section_id: int,
    section: SectionUpdate
):
    """更新版块信息
    
    更新指定版块的信息。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        section: 版块更新模型，包含要更新的信息
        
    Returns:
        Section: 更新后的版块信息
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 更新版块
        updated_section = await section_service.update_section(
            section_id=section_id,
            data=section.model_dump(exclude_unset=True)
        )
        return updated_section
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{section_id}/moderators/{user_id}")
@admin_endpoint(custom_message="添加版主失败")
async def add_moderator(
    request: Request,
    section_id: int,
    user_id: int
):
    """添加版主
    
    为指定版块添加一个版主。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        user_id: 要添加为版主的用户ID
        
    Returns:
        dict: 操作结果信息
        
    Raises:
        HTTPException: 当版块或用户不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 添加版主
        result = await section_service.add_moderator(section_id, user_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{section_id}/moderators/{user_id}")
@admin_endpoint(custom_message="移除版主失败")
async def remove_moderator(
    request: Request,
    section_id: int,
    user_id: int
):
    """移除版主
    
    从指定版块中移除一个版主。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        user_id: 要移除的版主用户ID
        
    Returns:
        dict: 操作结果信息
        
    Raises:
        HTTPException: 当版块不存在或用户不是版主时抛出相应错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 移除版主
        result = await section_service.remove_moderator(section_id, user_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{section_id}/posts", response_model=List[post_schema.Post])
@public_endpoint(cache_ttl=300, custom_message="获取版块帖子失败")
async def get_section_posts(
    request: Request,
    section_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取版块的所有帖子
    
    获取指定版块下的所有帖子，支持分页。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        skip: 跳过的记录数，用于分页
        limit: 每页记录数，默认20条
        
    Returns:
        List[Post]: 帖子列表
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 获取版块帖子
        posts, _ = await section_service.get_section_posts(
            section_id=section_id,
            skip=skip,
            limit=limit
        )
        return posts
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{section_id}")
@admin_endpoint(custom_message="删除版块失败")
async def delete_section(
    request: Request,
    section_id: int
):
    """删除版块
    
    删除指定的版块（软删除）。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section_id: 要删除的版块ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当版块不存在或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 删除版块
        result = await section_service.delete_section(section_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{section_id}/restore")
@admin_endpoint(custom_message="恢复版块失败")
async def restore_section(
    request: Request,
    section_id: int
):
    """恢复已删除的版块
    
    恢复指定的已删除版块。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复版块
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        section_id: 要恢复的版块ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当版块不存在、未被删除或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 恢复版块
        result = await section_service.restore_section(section_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{section_id}/moderators/{user_id}/restore")
@admin_endpoint(custom_message="恢复版主失败")
async def restore_moderator(
    request: Request,
    section_id: int,
    user_id: int
):
    """恢复已移除的版主
    
    恢复指定版块中已被移除的版主。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        user_id: 要恢复的版主用户ID
        
    Returns:
        dict: 操作结果信息
        
    Raises:
        HTTPException: 当版块不存在或记录不存在时抛出相应错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 恢复版主
        result = await section_service.restore_moderator(section_id, user_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{section_id}/moderators")
@public_endpoint(cache_ttl=300, custom_message="获取版主列表失败")
async def get_section_moderators(
    request: Request,
    section_id: int
):
    """获取版块的版主列表
    
    获取指定版块的所有版主用户。
    此接口对所有用户开放，结果将被缓存5分钟。
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        
    Returns:
        List[Dict]: 版主用户列表
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误
    """
    try:
        # 使用Service架构
        section_service = SectionService()
        
        # 获取版主列表
        moderators = await section_service.get_section_moderators(section_id)
        return moderators
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        ) 