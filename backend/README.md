# Favum backend

一个基于 FastAPI 和 SQLAlchemy 构建的现代化论坛API后端系统。

## 功能特点

- 用户管理
  - 用户注册、登录、注销
  - 基于角色的权限管理
  - 用户信息管理
  - 邮箱验证功能
  - 密码重置功能
  
- 内容管理
  - 帖子发布、编辑、删除
  - 评论管理
  - 内容分类和标签
  
- 系统特性
  - JWT 认证
  - Redis 缓存
  - Celery 异步任务
  - 速率限制
  - 日志记录
  - 性能监控

## 系统要求

- Python 3.8+
- Redis
- MySQL
- Node.js 14+ (用于前端)

## 安装步骤

1. 克隆项目

```bash
git clone https://git.3ext.com:5585/aaaisan/forum.git
cd forum
```

1. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

1. 安装前端依赖

```bash
cd frontend
npm install
```

## 配置

1. 复制环境变量示例文件

```bash
cp .env.example .env
```

1. 修改 `.env` 文件中的配置：

```ini
# API配置
API_V1_PREFIX=/api/v1
PROJECT_NAME=Forum
BACKEND_CORS_ORIGINS=["http://localhost:8000"]
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/forum

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## 数据库迁移

1. 初始化数据库

```bash
cd backend
alembic upgrade head
```

## 运行项目

1. 启动 Redis 服务器

```bash
redis-server
```

1. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload
```

1. 启动 Celery Worker

```bash
cd backend
celery -A app.core.celery_config worker --loglevel=info
```

1. 启动 Celery Beat（用于定时任务）

```bash
cd backend
celery -A app.core.celery_config beat --loglevel=info
```

1. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

现在可以访问以下地址：

- 后端 API: <http://localhost:8000>
- API 文档: <http://localhost:8000/docs>
- 前端应用: <http://localhost:8080>

## API 文档

启动后端服务后，可以通过以下地址访问 API 文档：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## 目录结构

```txt
backend/
├── alembic/            # 数据库迁移文件
├── app/                # 应用程序主目录
│   ├── api/            # API相关代码
│   │   ├── endpoints/  # API端点定义
│   │   ├── responses/  # API响应模型
│   │   └── router.py   # API路由注册
│   ├── core/           # 核心功能
│   │   ├── config.py   # 配置管理
│   │   ├── decorators/ # 装饰器
│   │   ├── security.py # 安全相关
│   │   └── ...
│   ├── db/             # 数据库相关
│   │   ├── base.py     # 数据库基础设置
│   │   ├── models/     # 数据模型
│   │   └── session.py  # 数据库会话
│   ├── dependencies/   # FastAPI依赖项
│   ├── middlewares/    # 中间件
│   ├── schemas/        # Pydantic模型
│   ├── services/       # 业务逻辑服务
│   ├── tasks/          # Celery异步任务
│   └── utils/          # 实用工具函数
└── requirements.txt    # 项目依赖
```

## API文档

本节提供了论坛系统所有API端点的完整文档，包括访问路径、方法、参数和用途。

### 认证相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/auth/check-username/{username}` | GET | 检查用户名是否可用 | 公开 | 路径参数: username | 用户名状态 |
| `/api/v1/auth/check-email/{email}` | GET | 检查邮箱是否可用 | 公开 | 路径参数: email | 邮箱状态 |
| `/api/v1/auth/register` | POST | 注册新用户 | 公开 | 请求体: 用户信息 | 令牌信息 |
| `/api/v1/auth/login` | POST | 用户登录 | 公开 | 请求体: 登录信息 | 令牌信息 |
| `/api/v1/auth/token` | POST | 获取令牌 | 公开 | 请求体: 登录信息 | 令牌信息 |
| `/api/v1/auth/test-token` | POST | 测试令牌有效性 | 授权用户 | 无 | 令牌数据 |
| `/api/v1/auth/forgot-password` | POST | 发送密码重置邮件 | 公开 | 请求体: 邮箱 | 重置请求结果 |
| `/api/v1/auth/reset-password` | POST | 重置密码 | 公开 | 请求体: 令牌和新密码 | 重置结果 |
| `/api/v1/auth/verify-email` | POST | 发送邮箱验证链接 | 授权用户 | 请求体: 邮箱 | 验证请求结果 |
| `/api/v1/auth/verify-email/{token}` | GET | 验证邮箱 | 公开 | 路径参数: token | 验证结果 |

### 用户相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/users` | POST | 创建新用户 | 管理员 | 请求体: 用户信息 | 用户信息 |
| `/api/v1/users` | GET | 获取用户列表 | 授权用户 | 查询参数: skip, limit, sort, order | 用户列表 |
| `/api/v1/users/me` | GET | 获取当前用户信息 | 授权用户 | 无 | 用户信息 |
| `/api/v1/users/{user_id}` | GET | 获取特定用户信息 | 授权用户 | 路径参数: user_id | 用户信息 |
| `/api/v1/users/{user_id}` | PUT | 更新用户信息 | 用户本人/管理员 | 路径参数: user_id, 请求体: 更新信息 | 更新后的用户信息 |
| `/api/v1/users/{user_id}` | DELETE | 删除用户 | 管理员 | 路径参数: user_id | 删除结果 |
| `/api/v1/users/{user_id}/restore` | POST | 恢复已删除用户 | 管理员 | 路径参数: user_id | 恢复的用户信息 |
| `/api/v1/users/me/profile` | GET | 获取个人资料 | 授权用户 | 无 | 用户资料 |
| `/api/v1/users/{user_id}/posts` | GET | 获取用户的帖子 | 授权用户 | 路径参数: user_id, 查询参数: skip, limit | 帖子列表 |
| `/api/v1/users/me/favorites` | GET | 获取当前用户收藏的帖子 | 授权用户 | 查询参数: skip, limit | 帖子列表 |
| `/api/v1/users/{user_id}/favorites` | GET | 获取指定用户收藏的帖子 | 授权用户 | 路径参数: user_id, 查询参数: skip, limit | 帖子列表 |

### 帖子相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/posts` | POST | 创建新帖子 | 授权用户 | 请求体: 帖子信息 | 创建的帖子 |
| `/api/v1/posts` | GET | 获取帖子列表 | 公开 | 查询参数: skip, limit, filter, sort | 帖子列表 |
| `/api/v1/posts/{post_id}` | GET | 获取帖子详情 | 公开 | 路径参数: post_id | 帖子详情 |
| `/api/v1/posts/{post_id}` | PUT | 更新帖子 | 作者/管理员 | 路径参数: post_id, 请求体: 更新信息 | 更新后的帖子 |
| `/api/v1/posts/{post_id}` | DELETE | 删除帖子 | 作者/管理员 | 路径参数: post_id | 删除结果 |
| `/api/v1/posts/{post_id}/restore` | POST | 恢复已删除帖子 | 管理员 | 路径参数: post_id | 恢复的帖子 |
| `/api/v1/posts/{post_id}/visibility` | PATCH | 更改帖子可见性 | 管理员 | 路径参数: post_id, 请求体: is_hidden | 更新后的帖子 |
| `/api/v1/posts/{post_id}/vote` | POST | 对帖子投票 | 授权用户 | 路径参数: post_id, 请求体: vote_type | 投票结果 |
| `/api/v1/posts/{post_id}/votes` | GET | 获取帖子投票统计 | 公开 | 路径参数: post_id | 投票统计 |
| `/api/v1/posts/{post_id}/favorite` | POST | 收藏帖子 | 授权用户 | 路径参数: post_id | 收藏结果 |
| `/api/v1/posts/{post_id}/favorite` | DELETE | 取消收藏帖子 | 授权用户 | 路径参数: post_id | 取消结果 |
| `/api/v1/posts/{post_id}/favorite/status` | GET | 获取收藏状态 | 授权用户 | 路径参数: post_id | 是否已收藏 |
| `/api/v1/posts/{post_id}/comments` | GET | 获取帖子评论 | 公开 | 路径参数: post_id, 查询参数: skip, limit | 评论列表 |

### 评论相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/comments` | POST | 创建评论 | 授权用户 | 请求体: 评论信息 | 创建的评论 |
| `/api/v1/comments/{comment_id}` | GET | 获取评论详情 | 公开 | 路径参数: comment_id | 评论详情 |
| `/api/v1/comments/{comment_id}` | PUT | 更新评论 | 作者/管理员 | 路径参数: comment_id, 请求体: 更新内容 | 更新后的评论 |
| `/api/v1/comments/{comment_id}` | DELETE | 删除评论 | 作者/管理员 | 路径参数: comment_id | 删除结果 |
| `/api/v1/comments/{comment_id}/restore` | POST | 恢复已删除评论 | 管理员 | 路径参数: comment_id | 恢复的评论 |
| `/api/v1/comments/post/{post_id}` | GET | 获取帖子的评论 | 公开 | 路径参数: post_id, 查询参数: skip, limit | 评论列表 |

### 分类相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/categories` | POST | 创建分类 | 管理员 | 请求体: 分类信息 | 创建的分类 |
| `/api/v1/categories` | GET | 获取分类列表 | 公开 | 查询参数: skip, limit | 分类列表 |
| `/api/v1/categories/{category_id}` | GET | 获取分类详情 | 公开 | 路径参数: category_id | 分类详情 |
| `/api/v1/categories/{category_id}` | PUT | 更新分类 | 管理员 | 路径参数: category_id, 请求体: 更新信息 | 更新后的分类 |
| `/api/v1/categories/{category_id}` | DELETE | 删除分类 | 管理员 | 路径参数: category_id | 删除结果 |
| `/api/v1/categories/{category_id}/restore` | POST | 恢复已删除分类 | 管理员 | 路径参数: category_id | 恢复的分类 |
| `/api/v1/categories/reorder` | POST | 重新排序分类 | 管理员 | 请求体: category_ids, parent_id | 排序后的分类列表 |

### 版块相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/sections` | POST | 创建版块 | 管理员 | 请求体: 版块信息 | 创建的版块 |
| `/api/v1/sections` | GET | 获取版块列表 | 公开 | 查询参数: skip, limit | 版块列表 |
| `/api/v1/sections/{section_id}` | GET | 获取版块详情 | 公开 | 路径参数: section_id | 版块详情 |
| `/api/v1/sections/{section_id}` | PUT | 更新版块 | 管理员 | 路径参数: section_id, 请求体: 更新信息 | 更新后的版块 |
| `/api/v1/sections/{section_id}` | DELETE | 删除版块 | 管理员 | 路径参数: section_id | 删除结果 |
| `/api/v1/sections/{section_id}/restore` | POST | 恢复已删除版块 | 管理员 | 路径参数: section_id | 恢复的版块 |
| `/api/v1/sections/{section_id}/moderators/{user_id}` | POST | 添加版主 | 管理员 | 路径参数: section_id, user_id | 操作结果 |
| `/api/v1/sections/{section_id}/moderators/{user_id}` | DELETE | 移除版主 | 管理员 | 路径参数: section_id, user_id | 操作结果 |
| `/api/v1/sections/{section_id}/moderators/{user_id}/restore` | POST | 恢复版主 | 管理员 | 路径参数: section_id, user_id | 操作结果 |
| `/api/v1/sections/{section_id}/moderators` | GET | 获取版块版主 | 公开 | 路径参数: section_id | 用户列表 |
| `/api/v1/sections/{section_id}/posts` | GET | 获取版块帖子 | 公开 | 路径参数: section_id, 查询参数: skip, limit | 帖子列表 |

### 标签相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/tags` | POST | 创建标签 | 管理员 | 请求体: 标签信息 | 创建的标签 |
| `/api/v1/tags` | GET | 获取标签列表 | 公开 | 查询参数: skip, limit | 标签列表 |
| `/api/v1/tags/{tag_id}` | GET | 获取标签详情 | 公开 | 路径参数: tag_id | 标签详情 |
| `/api/v1/tags/{tag_id}` | PUT | 更新标签 | 管理员 | 路径参数: tag_id, 请求体: 更新信息 | 更新后的标签 |
| `/api/v1/tags/{tag_id}` | DELETE | 删除标签 | 管理员 | 路径参数: tag_id | 删除结果 |
| `/api/v1/tags/{tag_id}/restore` | POST | 恢复已删除标签 | 管理员 | 路径参数: tag_id | 恢复的标签 |
| `/api/v1/tags/{tag_id}/update-stats` | POST | 更新标签统计信息 | 管理员 | 路径参数: tag_id | 更新后的标签 |
| `/api/v1/tags/{tag_id}/posts` | GET | 获取标签关联的帖子 | 公开 | 路径参数: tag_id, 查询参数: skip, limit | 帖子列表 |
| `/api/v1/tags/{tag_id}/related` | GET | 获取关联标签 | 公开 | 路径参数: tag_id, 查询参数: limit | 标签列表 |
| `/api/v1/tags/trending-list` | GET | 获取热门标签 | 公开 | 查询参数: days, limit | 标签列表 |
| `/api/v1/tags/popular` | GET | 获取流行标签 | 公开 | 查询参数: limit | 标签列表 |
| `/api/v1/tags/recent` | GET | 获取最近标签 | 公开 | 查询参数: limit | 标签列表 |
| `/api/v1/tags/search` | GET | 搜索标签 | 公开 | 查询参数: q, skip, limit | 标签列表 |
| `/api/v1/tags/recommendations` | POST | 获取标签推荐 | 公开 | 请求体: keywords, user_id | 标签列表 |

### 验证码相关 API

| 端点 | 方法 | 描述 | 权限 | 参数 | 返回 |
|-----|-----|------|-----|-----|-----|
| `/api/v1/captcha/generate` | GET | 生成验证码 | 公开 | 无 | 验证码信息 |
| `/api/v1/captcha/verify/{captcha_id}` | POST | 验证验证码 | 公开 | 路径参数: captcha_id, 请求体: 验证码 | 验证结果 |

### API认证

大多数API需要认证，认证使用JWT令牌实现。获取令牌的流程如下：

1. 调用 `/api/v1/auth/login` 或 `/api/v1/auth/register` 获取访问令牌
2. 在后续请求的头部添加认证信息：`Authorization: Bearer {token}`

### 权限级别

系统定义了以下权限级别：

- **公开**: 无需认证即可访问
- **授权用户**: 需要有效的认证令牌
- **用户本人**: 只能操作自己的资源
- **管理员**: 需要管理员权限
- **作者/管理员**: 资源作者或管理员

### 通用查询参数

- `skip`: 分页起始位置，默认0
- `limit`: 每页记录数，默认因API而异
- `sort`: 排序字段
- `order`: 排序方向，asc(升序)或desc(降序)

### 错误处理

所有API使用统一的错误响应格式：

```json
{
  "error": {
    "code": "错误代码",
    "message": "错误描述",
    "status_code": 状态码,
    "details": {} // 可选的详细信息
  }
}
```

## API 请求示例

以下是各API端点的完整使用示例：

### 认证相关API示例

#### 检查用户名是否可用

```bash
curl -X GET "http://localhost:8000/api/v1/auth/check-username/testuser"
```

#### 检查邮箱是否可用

```bash
curl -X GET "http://localhost:8000/api/v1/auth/check-email/test@example.com"
```

#### 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "Password123!",
    "captcha_id": "abc123",
    "captcha_code": "XYZ123"
  }'
```

#### 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "Password123!",
    "captcha_id": "def456",
    "captcha_code": "ABC789"
  }'
```

#### 测试令牌有效性

```bash
curl -X POST "http://localhost:8000/api/v1/auth/test-token" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 请求密码重置

```bash
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### 重置密码

```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r",
    "new_password": "NewPassword456!"
  }'
```

#### 发送邮箱验证链接

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### 通过链接验证邮箱

```bash
curl -X GET "http://localhost:8000/api/v1/auth/verify-email/EMAIL_VERIFICATION_TOKEN?email=user@example.com"
```

### 用户相关API示例

#### 创建新用户(管理员权限)

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser2",
    "email": "newuser2@example.com",
    "password": "Password123!",
    "role": "user"
  }'
```

#### 获取用户列表

```bash
curl -X GET "http://localhost:8000/api/v1/users?skip=0&limit=10&sort=created_at&order=desc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取当前用户信息

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取特定用户信息

```bash
curl -X GET "http://localhost:8000/api/v1/users/46" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 更新用户信息

```bash
curl -X PUT "http://localhost:8000/api/v1/users/46" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "热爱编程，专注于后端开发",
    "avatar_url": "https://example.com/avatars/user46.jpg"
  }'
```

#### 删除用户

```bash
curl -X DELETE "http://localhost:8000/api/v1/users/46" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 恢复已删除用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/46/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 获取个人资料

```bash
curl -X GET "http://localhost:8000/api/v1/users/me/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取用户帖子

```bash
curl -X GET "http://localhost:8000/api/v1/users/46/posts?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取当前用户收藏的帖子

```bash
curl -X GET "http://localhost:8000/api/v1/users/me/favorites?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取指定用户收藏的帖子

```bash
curl -X GET "http://localhost:8000/api/v1/users/46/favorites?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 帖子相关API示例

#### 创建新帖子

```bash
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI学习笔记",
    "content": "这是我学习FastAPI的一些心得体会...",
    "section_id": 12,
    "category_id": 28,
    "tags": [61, 65]
  }'
```

#### 获取帖子列表

```bash
curl -X GET "http://localhost:8000/api/v1/posts?skip=0&limit=10&sort=created_at&order=desc"
```

#### 获取帖子详情

```bash
curl -X GET "http://localhost:8000/api/v1/posts/24"
```

#### 更新帖子

```bash
curl -X PUT "http://localhost:8000/api/v1/posts/24" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容...",
    "category_id": 28,
    "tags": [61, 65]
  }'
```

#### 删除帖子

```bash
curl -X DELETE "http://localhost:8000/api/v1/posts/24" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 恢复已删除帖子

```bash
curl -X POST "http://localhost:8000/api/v1/posts/24/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 更改帖子可见性

```bash
curl -X PATCH "http://localhost:8000/api/v1/posts/24/visibility" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_hidden": true
  }'
```

#### 对帖子投票

```bash
curl -X POST "http://localhost:8000/api/v1/posts/24/vote" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": "upvote"
  }'
```

#### 获取帖子投票统计

```bash
curl -X GET "http://localhost:8000/api/v1/posts/24/votes"
```

#### 收藏帖子

```bash
curl -X POST "http://localhost:8000/api/v1/posts/24/favorite" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 取消收藏帖子

```bash
curl -X DELETE "http://localhost:8000/api/v1/posts/24/favorite" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取收藏状态

```bash
curl -X GET "http://localhost:8000/api/v1/posts/24/favorite/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 获取帖子评论

```bash
curl -X GET "http://localhost:8000/api/v1/posts/24/comments?skip=0&limit=10"
```

### 评论相关API示例

#### 创建评论

```bash
curl -X POST "http://localhost:8000/api/v1/comments" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一条评论",
    "post_id": 24
  }'
```

#### 获取评论详情

```bash
curl -X GET "http://localhost:8000/api/v1/comments/18"
```

#### 更新评论

```bash
curl -X PUT "http://localhost:8000/api/v1/comments/18" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的评论内容"
  }'
```

#### 删除评论

```bash
curl -X DELETE "http://localhost:8000/api/v1/comments/18" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 恢复已删除评论

```bash
curl -X POST "http://localhost:8000/api/v1/comments/18/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 获取帖子的评论

```bash
curl -X GET "http://localhost:8000/api/v1/comments/post/24?skip=0&limit=10"
```

### 分类相关API示例

#### 创建分类

```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "前端技术",
    "description": "前端技术相关讨论",
    "parent_id": 28,
    "order": 3
  }'
```

#### 获取分类列表

```bash
curl -X GET "http://localhost:8000/api/v1/categories?skip=0&limit=100"
```

#### 获取分类详情

```bash
curl -X GET "http://localhost:8000/api/v1/categories/28"
```

#### 更新分类

```bash
curl -X PUT "http://localhost:8000/api/v1/categories/28" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术讨论",
    "description": "关于编程与技术的讨论",
    "order": 1
  }'
```

#### 删除分类

```bash
curl -X DELETE "http://localhost:8000/api/v1/categories/35" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 恢复已删除分类

```bash
curl -X POST "http://localhost:8000/api/v1/categories/35/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 重新排序分类

```bash
curl -X POST "http://localhost:8000/api/v1/categories/reorder" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": 28,
    "category_ids": [33, 34, 35]
  }'
```

### 版块相关API示例

#### 创建版块

```bash
curl -X POST "http://localhost:8000/api/v1/sections" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新版块",
    "description": "新版块的描述"
  }'
```

#### 获取版块列表

```bash
curl -X GET "http://localhost:8000/api/v1/sections?skip=0&limit=100"
```

#### 获取版块详情

```bash
curl -X GET "http://localhost:8000/api/v1/sections/12"
```

#### 更新版块

```bash
curl -X PUT "http://localhost:8000/api/v1/sections/12" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术区",
    "description": "技术交流与分享"
  }'
```

#### 删除版块

```bash
curl -X DELETE "http://localhost:8000/api/v1/sections/15" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 恢复已删除版块

```bash
curl -X POST "http://localhost:8000/api/v1/sections/15/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 添加版主

```bash
curl -X POST "http://localhost:8000/api/v1/sections/12/moderators/46" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 移除版主

```bash
curl -X DELETE "http://localhost:8000/api/v1/sections/12/moderators/46" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 恢复版主

```bash
curl -X POST "http://localhost:8000/api/v1/sections/12/moderators/46/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 获取版块版主

```bash
curl -X GET "http://localhost:8000/api/v1/sections/12/moderators"
```

#### 获取版块帖子

```bash
curl -X GET "http://localhost:8000/api/v1/sections/12/posts?skip=0&limit=10"
```

### 标签相关API示例

#### 创建标签

```bash
curl -X POST "http://localhost:8000/api/v1/tags" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "React"
  }'
```

#### 获取标签列表

```bash
curl -X GET "http://localhost:8000/api/v1/tags?skip=0&limit=100"
```

#### 获取标签详情

```bash
curl -X GET "http://localhost:8000/api/v1/tags/61"
```

#### 更新标签

```bash
curl -X PUT "http://localhost:8000/api/v1/tags/61" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python"
  }'
```

#### 删除标签

```bash
curl -X DELETE "http://localhost:8000/api/v1/tags/76" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 恢复已删除标签

```bash
curl -X POST "http://localhost:8000/api/v1/tags/76/restore" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 更新标签统计信息

```bash
curl -X POST "http://localhost:8000/api/v1/tags/61/update-stats" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 获取标签关联的帖子

```bash
curl -X GET "http://localhost:8000/api/v1/tags/61/posts?skip=0&limit=10"
```

#### 获取关联标签

```bash
curl -X GET "http://localhost:8000/api/v1/tags/61/related?limit=5"
```

#### 获取热门标签

```bash
curl -X GET "http://localhost:8000/api/v1/tags/trending-list?days=7&limit=10"
```

#### 获取流行标签

```bash
curl -X GET "http://localhost:8000/api/v1/tags/popular?limit=10"
```

#### 获取最近标签

```bash
curl -X GET "http://localhost:8000/api/v1/tags/recent?limit=10"
```

#### 搜索标签

```bash
curl -X GET "http://localhost:8000/api/v1/tags/search?q=py&skip=0&limit=10"
```

#### 获取标签推荐

```bash
curl -X POST "http://localhost:8000/api/v1/tags/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "web"],
    "user_id": 46
  }'
```

### 验证码相关API示例

#### 生成验证码

```bash
curl -X GET "http://localhost:8000/api/v1/captcha/generate"
```

#### 验证验证码

```bash
curl -X POST "http://localhost:8000/api/v1/captcha/verify/captcha123" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ABC123"
  }'
```

## 许可证

该项目基于 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者 - <aaaisan@gmail.com>

项目链接: [https://git.3ext.com:5585/aaaisan/forum](https://git.3ext.com:5585/aaaisan/forum)
