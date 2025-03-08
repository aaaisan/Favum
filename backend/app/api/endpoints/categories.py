from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from ...core.decorators.auth import require_roles
from ...core.decorators.auth import validate_token, require_roles
from ...utils.api_decorators import admin_endpoint, public_endpoint
from ...schemas import category as category_schema
from ...services.category_service import CategoryService
from ...core.exceptions import BusinessException

router = APIRouter()

@router.post("/", response_model=category_schema.Category)
@admin_endpoint(custom_message="创建分类失败")
async def create_category(
    request: Request,
    category: category_schema.CategoryCreate
):
    """创建新分类
    
    创建一个新的帖子分类。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category: 分类创建模型，包含分类信息
        
    Returns:
        Category: 创建成功的分类信息
        
    Raises:
        HTTPException: 当权限不足或创建失败时抛出相应错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 创建分类
        result = await category_service.create_category(category.model_dump())
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/", response_model=List[category_schema.Category])
@public_endpoint(cache_ttl=300, custom_message="获取分类列表失败")
async def read_categories(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """获取分类列表
    
    获取所有分类的列表，支持分页。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        List[Category]: 分类列表
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 获取分类列表
        categories, _ = await category_service.get_categories(skip=skip, limit=limit)
        return categories
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{category_id}", response_model=category_schema.Category)
@public_endpoint(cache_ttl=300, custom_message="获取分类详情失败")
async def read_category(
    request: Request,
    category_id: int
):
    """获取分类详情
    
    获取指定分类的详细信息。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        category_id: 分类ID
        
    Returns:
        Category: 分类详细信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 获取分类详情
        category = await category_service.get_category_detail(category_id)
        return category
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.put("/{category_id}", response_model=category_schema.Category)
@admin_endpoint(custom_message="更新分类失败")
async def update_category(
    request: Request,
    category_id: int,
    category: category_schema.CategoryUpdate
):
    """更新分类信息
    
    更新指定分类的信息。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_id: 分类ID
        category: 分类更新模型，包含要更新的信息
        
    Returns:
        Category: 更新后的分类信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 更新分类
        updated_category = await category_service.update_category(
            category_id=category_id,
            data=category.model_dump(exclude_unset=True)
        )
        return updated_category
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{category_id}")
@admin_endpoint(custom_message="删除分类失败")
async def delete_category(
    request: Request,
    category_id: int
):
    """删除分类
    
    删除指定的分类（软删除）。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_id: 要删除的分类ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当分类不存在或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 删除分类
        result = await category_service.delete_category(category_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{category_id}/restore")
@admin_endpoint(custom_message="恢复分类失败")
async def restore_category(
    request: Request,
    category_id: int
):
    """恢复已删除的分类
    
    恢复指定的已删除分类。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复分类
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        category_id: 要恢复的分类ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当分类不存在、未被删除或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 恢复分类
        result = await category_service.restore_category(category_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/reorder")
@admin_endpoint(custom_message="重新排序分类失败")
async def reorder_categories(
    request: Request,
    category_ids: List[int],
    parent_id: Optional[int] = None
):
    """重新排序分类
    
    调整分类的显示顺序。
    支持调整同级分类的顺序，以及移动分类到不同的父分类下。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_ids: 分类ID列表，按照期望的顺序排列
        parent_id: 父分类ID，如果要移动到顶级分类则为None
        
    Returns:
        dict: 包含更新后的分类顺序信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        category_service = CategoryService()
        
        # 重新排序分类
        result = await category_service.reorder_categories(parent_id, category_ids)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        ) 