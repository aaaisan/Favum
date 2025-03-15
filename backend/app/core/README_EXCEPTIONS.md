# 异常处理机制

本文档描述了项目中的异常处理机制，包括异常类层次结构、异常处理函数和建议的最佳实践。

## 异常层次结构

项目中的异常分为两大类：

1. **FastAPI异常**: 继承自`HTTPException`的异常，直接生成HTTP响应。
   - `APIError`: 自定义API异常的基类
   - `PermissionError`: 权限不足异常

2. **业务异常**: 继承自`BusinessError`的异常，表示业务逻辑错误。
   - `NotFoundError`: 资源不存在
   - `ValidationError`: 数据验证失败
   - `AuthenticationError`: 身份验证失败
   - `PermissionDeniedError`: 权限不足
   - `RateLimitError`: 请求频率限制
   - `ResourceConflictError`: 资源冲突
   - `RequestDataError`: 请求数据错误

## 异常处理工具

项目提供了以下用于异常处理的工具函数和装饰器：

### 1. `handle_business_exception`

将业务异常转换为HTTP异常，根据异常类型选择适当的HTTP状态码。

```python
try:
    result = await service.do_something()
except BusinessException as e:
    handle_business_exception(e)
```

以下是异常类型到HTTP状态码的映射：

- `NotFoundError`: 404 Not Found
- `AuthenticationError`: 401 Unauthorized
- `PermissionDeniedError`/`PermissionError`: 403 Forbidden
- `ValidationError`: 422 Unprocessable Entity
- `RateLimitError`: 429 Too Many Requests
- `ResourceConflictError`: 409 Conflict
- `RequestDataError`: 400 Bad Request

### 2. `handle_database_exception`

处理数据库相关异常，识别常见的数据库错误模式并提供用户友好的错误消息。

```python
try:
    result = await db.execute(query)
except Exception as e:
    if "db" in str(e).lower():
        handle_database_exception(e)
    raise
```

### 3. `with_error_handling`装饰器

一个全面的异常处理装饰器，可以直接应用于API端点函数，处理所有类型的异常。

```python
@router.get("/resource/{id}")
@public_endpoint()
@with_error_handling(default_error_message="获取资源失败")
async def get_resource(id: int):
    # 直接编写业务逻辑，无需try/except
    return await service.get_resource(id)
```

## 最佳实践

1. **使用`with_error_handling`装饰器**

   对于新的端点，优先使用`with_error_handling`装饰器进行异常处理，这样可以减少样板代码。

2. **抛出具体的业务异常**

   在服务层抛出具体的业务异常而不是通用的`Exception`，以便提供更精确的错误处理：

   ```python
   if not resource:
       raise NotFoundError(code="resource_not_found", message="资源不存在")
   ```

3. **提供有意义的错误代码和消息**

   为每个异常提供有意义的错误代码和消息，便于客户端识别和处理：

   ```python
   raise ValidationError(
       code="invalid_format",
       message="无效的日期格式，应为YYYY-MM-DD",
       field="birth_date"
   )
   ```

4. **日志记录**

   在处理异常时记录足够的上下文信息，便于调试和故障排除：

   ```python
   logger.error(f"处理用户 {user_id} 的请求时失败: {str(e)}", exc_info=True)
   ```

5. **安全考虑**

   不要在错误响应中包含敏感信息，如数据库凭据、内部路径或详细的堆栈跟踪。

## 示例

### 服务层抛出异常

```python
async def get_user(user_id: int):
    user = await db.fetch_one(query)
    if not user:
        raise NotFoundError(
            code="user_not_found",
            message=f"用户 {user_id} 不存在"
        )
    return user
```

### API层处理异常

简洁版(推荐):

```python
@router.get("/users/{user_id}")
@public_endpoint()
@with_error_handling(default_error_message="获取用户信息失败")
async def get_user(user_id: int, user_service: UserService = Depends()):
    return await user_service.get_user(user_id)
```

详细版:

```python
@router.get("/users/{user_id}")
@public_endpoint()
async def get_user(user_id: int, user_service: UserService = Depends()):
    try:
        return await user_service.get_user(user_id)
    except BusinessException as e:
        handle_business_exception(e)
    except Exception as e:
        logger.error(f"获取用户 {user_id} 失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"message": "获取用户信息失败", "error_code": "INTERNAL_ERROR"}
        )
```
