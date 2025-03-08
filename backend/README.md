# Forum 论坛系统

一个基于 FastAPI 和 SQLAlchemy 构建的现代化论坛系统。

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
git clone https://github.com/yourusername/forum.git
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
BACKEND_CORS_ORIGINS=["http://localhost:8080"]
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

## API 接口概览

### 基础 API 路径

所有 API 路由都以 `/api/v1` 为前缀。

### 认证 API (`/api/v1/auth`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/check-username/{username}` | GET | 检查用户名是否可用 | 无 | 路径参数: username | `{"message": "用户名可用"}` |
| `/check-email/{email}` | GET | 检查邮箱是否可用 | 无 | 路径参数: email | `{"message": "邮箱可用"}` |
| `/register` | POST | 注册新用户 | 无 | UserRegister 对象 | TokenResponse 对象 |
| `/login` | POST | 用户登录 | 无 | Login 对象 | TokenResponse 对象 |
| `/test-token` | POST | 测试令牌有效性 | 有效令牌 | 无 | TokenDataResponse 对象 |
| `/forgot-password` | POST | 请求密码重置邮件 | 无 | PasswordResetRequest 对象 | PasswordResetRequestResponse 对象 |
| `/reset-password` | POST | 重置用户密码 | 无 | PasswordReset 对象 | PasswordResetResponse 对象 |
| `/verify-email` | POST | 验证用户邮箱 | 无 | EmailVerification 对象 | EmailVerificationResponse 对象 |
| `/verify-email/{token}` | GET | 通过链接验证邮箱 | 无 | 路径参数: token, 查询参数: email | EmailVerificationRedirectResponse 对象 |

### 用户 API (`/api/v1/users`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新用户 | 无 | UserCreate 对象 | User 对象 |
| `/` | GET | 获取所有用户列表 | 管理员 | 查询参数: skip, limit, sort_by, sort_order | User 对象列表 |
| `/{user_id}` | GET | 获取指定用户详情 | 管理员或本人 | 路径参数: user_id | User 对象 |
| `/{user_id}` | PUT | 更新用户信息 | 管理员或本人 | 路径参数: user_id, UserUpdate 对象 | User 对象 |
| `/{user_id}` | DELETE | 删除(软删除)用户 | 管理员或本人 | 路径参数: user_id | 成功消息 |
| `/{user_id}/restore` | POST | 恢复已删除用户 | 管理员 | 路径参数: user_id | 成功消息 |
| `/me/profile` | GET | 获取当前用户资料 | 认证用户 | 无 | UserProfile 对象 |
| `/{user_id}/posts` | GET | 获取用户的帖子 | 无 | 路径参数: user_id | Post 对象列表 |
| `/me/favorites` | GET | 获取当前用户收藏 | 认证用户 | 查询参数: skip, limit | Post 对象列表 |
| `/{user_id}/favorites` | GET | 获取指定用户收藏 | 无 | 路径参数: user_id, 查询参数: skip, limit | Post 对象列表 |

### 帖子 API (`/api/v1/posts`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新帖子 | 认证用户 | PostCreate 对象 | Post 对象 |
| `/` | GET | 获取帖子列表 | 无 | 查询参数: skip, limit, sort_by, category_id, tag_id 等 | Post 对象列表 |
| `/{post_id}` | GET | 获取帖子详情 | 无 | 路径参数: post_id | PostDetail 对象 |
| `/{post_id}` | PUT | 更新帖子 | 作者或管理员 | 路径参数: post_id, PostUpdate 对象 | Post 对象 |
| `/{post_id}` | DELETE | 删除帖子 | 作者或管理员 | 路径参数: post_id | 成功消息 |
| `/{post_id}/restore` | POST | 恢复已删除帖子 | 作者或管理员 | 路径参数: post_id | 成功消息 |
| `/{post_id}/comments` | GET | 获取帖子的评论 | 无 | 路径参数: post_id, 查询参数: skip, limit | Comment 对象列表 |
| `/{post_id}/vote` | POST | 对帖子投票 | 认证用户 | 路径参数: post_id, Vote 对象 | 更新后的投票信息 |
| `/{post_id}/votes` | GET | 获取帖子投票数 | 无 | 路径参数: post_id | 投票统计信息 |
| `/{post_id}/favorite` | POST | 收藏帖子 | 认证用户 | 路径参数: post_id | 成功消息 |
| `/{post_id}/unfavorite` | POST | 取消收藏帖子 | 认证用户 | 路径参数: post_id | 成功消息 |
| `/{post_id}/visibility` | PUT | 切换帖子可见性 | 作者或管理员 | 路径参数: post_id | 更新后的帖子信息 |

### 评论 API (`/api/v1/comments`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新评论 | 认证用户 | CommentCreate 对象 | Comment 对象 |
| `/{comment_id}` | GET | 获取评论详情 | 无 | 路径参数: comment_id | Comment 对象 |
| `/{comment_id}` | PUT | 更新评论 | 作者或管理员 | 路径参数: comment_id, CommentUpdate 对象 | Comment 对象 |
| `/{comment_id}` | DELETE | 删除评论 | 作者或管理员 | 路径参数: comment_id | 成功消息 |
| `/{comment_id}/restore` | POST | 恢复已删除评论 | 作者或管理员 | 路径参数: comment_id | 成功消息 |
| `/{comment_id}/vote` | POST | 对评论投票 | 认证用户 | 路径参数: comment_id, Vote 对象 | 更新后的投票信息 |
| `/{comment_id}/votes` | GET | 获取评论投票数 | 无 | 路径参数: comment_id | 投票统计信息 |

### 分类 API (`/api/v1/categories`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新分类 | 管理员 | CategoryCreate 对象 | Category 对象 |
| `/` | GET | 获取所有分类 | 无 | 查询参数: skip, limit | Category 对象列表 |
| `/{category_id}` | GET | 获取分类详情 | 无 | 路径参数: category_id | Category 对象 |
| `/{category_id}` | PUT | 更新分类 | 管理员 | 路径参数: category_id, CategoryUpdate 对象 | Category 对象 |
| `/{category_id}` | DELETE | 删除分类 | 管理员 | 路径参数: category_id | 成功消息 |
| `/{category_id}/posts` | GET | 获取分类下的帖子 | 无 | 路径参数: category_id, 查询参数: skip, limit | Post 对象列表 |

### 板块 API (`/api/v1/sections`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新板块 | 管理员 | SectionCreate 对象 | Section 对象 |
| `/` | GET | 获取所有板块 | 无 | 查询参数: skip, limit | Section 对象列表 |
| `/{section_id}` | GET | 获取板块详情 | 无 | 路径参数: section_id | Section 对象 |
| `/{section_id}` | PUT | 更新板块 | 管理员 | 路径参数: section_id, SectionUpdate 对象 | Section 对象 |
| `/{section_id}` | DELETE | 删除板块 | 管理员 | 路径参数: section_id | 成功消息 |
| `/{section_id}/categories` | GET | 获取板块下的分类 | 无 | 路径参数: section_id | Category 对象列表 |

### 标签 API (`/api/v1/tags`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | POST | 创建新标签 | 管理员 | TagCreate 对象 | Tag 对象 |
| `/` | GET | 获取所有标签 | 无 | 查询参数: skip, limit | Tag 对象列表 |
| `/{tag_id}` | GET | 获取标签详情 | 无 | 路径参数: tag_id | Tag 对象 |
| `/{tag_id}` | PUT | 更新标签 | 管理员 | 路径参数: tag_id, TagUpdate 对象 | Tag 对象 |
| `/{tag_id}` | DELETE | 删除标签 | 管理员 | 路径参数: tag_id | 成功消息 |
| `/{tag_id}/posts` | GET | 获取标签下的帖子 | 无 | 路径参数: tag_id, 查询参数: skip, limit | Post 对象列表 |

### 验证码 API (`/api/v1/captcha`)

| 路径 | 方法 | 说明 | 权限要求 | 请求参数 | 返回数据 |
|------|------|------|----------|----------|----------|
| `/` | GET | 生成新验证码 | 无 | 无 | 包含验证码ID和图片的响应 |
| `/{captcha_id}/verify` | POST | 验证验证码 | 无 | 路径参数: captcha_id, 请求体: code | 验证结果 |

## 常见错误码

| 错误码 | 状态码 | 说明 |
|--------|--------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `POST_NOT_FOUND` | 404 | 帖子不存在 |
| `COMMENT_NOT_FOUND` | 404 | 评论不存在 |
| `CATEGORY_NOT_FOUND` | 404 | 分类不存在 |
| `SECTION_NOT_FOUND` | 404 | 板块不存在 |
| `TAG_NOT_FOUND` | 404 | 标签不存在 |
| `USERNAME_TAKEN` | 400 | 用户名已被使用 |
| `EMAIL_TAKEN` | 400 | 邮箱已被使用 |
| `INVALID_CREDENTIALS` | 401 | 无效的认证信息 |
| `INSUFFICIENT_PERMISSIONS` | 403 | 权限不足 |
| `INVALID_CAPTCHA` | 400 | 验证码无效或已过期 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超过限制 |

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

## 主要依赖包

```txt
fastapi==0.104.1
sqlalchemy==2.0.23
pydantic==2.4.2
alembic==1.12.1
celery==5.3.4
redis==5.0.1
pymysql==1.1.0
cryptography==41.0.5
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
emails==0.6
```

## API 请求示例

### 用户注册

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

### 用户登录

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

### 请求密码重置

```bash
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### 重置密码

```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r",
    "new_password": "NewPassword456!"
  }'
```

### 验证邮箱

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "token": "3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r"
  }'
```

### 创建帖子

```bash
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "示例帖子",
    "content": "这是一个示例帖子的内容。",
    "category_id": 1,
    "tags": [1, 2, 3]
  }'
```

### 获取帖子列表

```bash
curl -X GET "http://localhost:8000/api/v1/posts?limit=10&skip=0&sort_by=created_at&sort_order=desc"
```

## 贡献指南

1. Fork 该项目
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 许可证

该项目基于 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者 - <yourname@example.com>

项目链接: [https://github.com/yourusername/forum](https://github.com/yourusername/forum)

## Forum API 文档

## 概述

本文档提供了Forum API的所有端点信息，包括路径、作用和使用方法。

## 目录

- [认证相关](#认证相关)
- [用户相关](#用户相关)
- [帖子相关](#帖子相关)
- [评论相关](#评论相关)
- [分类相关](#分类相关)
- [版块相关](#版块相关)
- [标签相关](#标签相关)

## 认证相关

### 登录获取令牌

- **路径**: `/api/v1/auth/token`
- **方法**: POST
- **作用**: 获取JWT访问令牌，用于后续请求的认证
- **请求参数**:
  - `username`: 用户名
  - `password`: 密码
- **响应格式**:

  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/token" \
       -H "Content-Type: application/x-www-form-urlencoded" \
       -d "username=admin&password=admin123"
  ```

### 刷新令牌

- **路径**: `/api/v1/auth/refresh`
- **方法**: POST
- **作用**: 使用刷新令牌获取新的访问令牌
- **请求头**:
  - `Authorization`: Bearer {refresh_token}
- **响应格式**:

  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
       -H "Authorization: Bearer {refresh_token}"
  ```

## 用户相关

### 获取当前用户信息

- **路径**: `/api/v1/users/me`
- **方法**: GET
- **作用**: 获取当前认证用户的信息
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "id": 46,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "role": "admin",
    "created_at": "2025-03-05T16:15:30",
    "updated_at": "2025-03-05T16:15:30"
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/users/me" \
       -H "Authorization: Bearer {access_token}"
  ```

### 获取当前用户资料

- **路径**: `/api/v1/users/me/profile`
- **方法**: GET
- **作用**: 获取当前认证用户的详细资料
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "id": 46,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "role": "admin",
    "bio": "系统管理员，负责论坛维护工作",
    "avatar_url": "https://example.com/avatars/admin.jpg",
    "created_at": "2025-03-05T16:15:30",
    "updated_at": "2025-03-05T16:15:30",
    "profile": {
      "bio": "系统管理员",
      "avatar_url": "https://example.com/avatar.jpg",
      "location": "北京"
    }
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/users/me/profile" \
       -H "Authorization: Bearer {access_token}"
  ```

### 获取特定用户的帖子

- **路径**: `/api/v1/users/{user_id}/posts`
- **方法**: GET
- **作用**: 获取指定用户发布的帖子列表
- **请求参数**:
  - `skip` (可选): 跳过的记录数，默认为0
  - `limit` (可选): 返回的最大记录数，默认为20
- **响应格式**:

  ```json
  [
    {
      "id": 24,
      "title": "使用FastAPI构建高性能API",
      "content": "FastAPI是一个现代、快速（高性能）的Web框架...",
      "author_id": 46,
      "category_id": 28,
      "created_at": "2025-02-20T22:27:05",
      "updated_at": "2025-02-20T22:27:05",
      "vote_count": 48
    },
    // 更多帖子...
  ]
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/users/46/posts?skip=0&limit=10" \
       -H "Authorization: Bearer {access_token}"
  ```

### 更新用户信息

- **路径**: `/api/v1/users/{user_id}`
- **方法**: PUT
- **作用**: 更新指定ID的用户信息
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "username": "更新后的用户名",
    "email": "newemail@example.com",
    "bio": "用户的个人简介信息",
    "avatar_url": "https://example.com/avatars/new_avatar.jpg"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 46,
    "username": "更新后的用户名",
    "email": "newemail@example.com",
    "bio": "用户的个人简介信息",
    "avatar_url": "https://example.com/avatars/new_avatar.jpg",
    "is_active": true,
    "role": "user",
    "created_at": "2025-02-20T22:27:05",
    "updated_at": "2025-03-08T11:50:15"
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/users/46" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "bio": "用户的个人简介信息",
            "avatar_url": "https://example.com/avatars/new_avatar.jpg"
          }'
  ```

## 帖子相关

### 获取所有帖子

- **路径**: `/api/v1/posts`
- **方法**: GET
- **作用**: 获取所有帖子列表
- **请求参数**:
  - `skip` (可选): 跳过的记录数，默认为0
  - `limit` (可选): 返回的最大记录数，默认为20
  - `category_id` (可选): 按分类ID筛选
  - `tag_id` (可选): 按标签ID筛选
  - `sort` (可选): 排序方式，可选值为`created_at`、`vote_count`等
  - `order` (可选): 排序顺序，可选值为`asc`、`desc`
- **响应格式**:

  ```json
  {
    "posts": [
      {
        "id": 28,
        "title": "程序员如何有效提升沟通能力",
        "content": "作为程序员，技术能力很重要，但沟通能力同样不可或缺...",
        "author_id": 50,
        "category_id": 30,
        "created_at": "2025-03-05T16:20:45",
        "updated_at": "2025-03-05T16:20:45",
        "vote_count": 15,
        "category": {
          "id": 30,
          "name": "职业发展",
          "created_at": "2025-03-05T18:16:28"
        },
        "tags": [
          {
            "id": 70,
            "name": "求职",
            "created_at": "2025-03-05T18:16:28"
          },
          {
            "id": 75,
            "name": "产品管理",
            "created_at": "2025-03-05T18:16:28"
          }
        ]
      },
      // 更多帖子...
    ]
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/posts?skip=0&limit=10&sort=created_at&order=desc"
  ```

### 获取特定帖子

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: GET
- **作用**: 获取指定ID的帖子详情
- **响应格式**:

  ```json
  {
    "id": 24,
    "title": "使用FastAPI构建高性能API",
    "content": "FastAPI是一个现代、快速（高性能）的Web框架...",
    "author_id": 46,
    "category_id": 28,
    "created_at": "2025-02-20T22:27:05",
    "updated_at": "2025-02-20T22:27:05",
    "vote_count": 48,
    "author": {
      "id": 46,
      "username": "admin"
    },
    "category": {
      "id": 28,
      "name": "技术讨论"
    },
    "tags": [
      {
        "id": 61,
        "name": "Python"
      },
      {
        "id": 65,
        "name": "FastAPI"
      }
    ]
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/posts/24"
  ```

### 发帖

- **路径**: `/api/v1/posts`
- **方法**: POST
- **作用**: 创建新帖子
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "title": "新帖子标题",
    "content": "帖子内容...",
    "category_id": 28,
    "tags": [61, 65]
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 29,
    "title": "新帖子标题",
    "content": "帖子内容...",
    "author_id": 46,
    "category_id": 28,
    "created_at": "2025-03-08T11:45:30",
    "updated_at": "2025-03-08T11:45:30",
    "vote_count": 0
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/posts" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "title": "新帖子标题",
            "content": "帖子内容...",
            "category_id": 28,
            "tags": [61, 65]
          }'
  ```

### 更新帖子

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: PUT
- **作用**: 更新指定ID的帖子
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "title": "更新后的标题",
    "content": "更新后的内容...",
    "category_id": 28,
    "tags": [61, 65]
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 24,
    "title": "更新后的标题",
    "content": "更新后的内容...",
    "author_id": 46,
    "category_id": 28,
    "created_at": "2025-02-20T22:27:05",
    "updated_at": "2025-03-08T11:50:15",
    "vote_count": 48
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/posts/24" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "title": "更新后的标题",
            "content": "更新后的内容...",
            "category_id": 28,
            "tags": [61, 65]
          }'
  ```

### 删除帖子

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: DELETE
- **作用**: 删除指定ID的帖子
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "message": "帖子已成功删除"
  }
  ```

- **使用示例**:

  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/posts/24" \
       -H "Authorization: Bearer {access_token}"
  ```

## 评论相关

### 获取帖子的评论

- **路径**: `/api/v1/posts/{post_id}/comments`
- **方法**: GET
- **作用**: 获取指定帖子的所有评论
- **请求参数**:
  - `skip` (可选): 跳过的记录数，默认为0
  - `limit` (可选): 返回的最大记录数，默认为20
- **响应格式**:

  ```json
  [
    {
      "id": 18,
      "content": "FastAPI的性能确实比Flask好很多，而且类型提示很方便。",
      "author_id": 46,
      "post_id": 24,
      "created_at": "2025-02-21T15:30:45"
    },
    {
      "id": 17,
      "content": "请问FastAPI和Flask相比有什么优势？",
      "author_id": 49,
      "post_id": 24,
      "created_at": "2025-02-21T14:25:10"
    }
  ]
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/posts/24/comments?skip=0&limit=10"
  ```

### 创建评论

- **路径**: `/api/v1/posts/{post_id}/comments`
- **方法**: POST
- **作用**: 为指定帖子创建新评论
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "content": "这是一条新评论"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 19,
    "content": "这是一条新评论",
    "author_id": 46,
    "post_id": 24,
    "created_at": "2025-03-08T12:05:20"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/posts/24/comments" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{"content": "这是一条新评论"}'
  ```

### 更新评论

- **路径**: `/api/v1/comments/{comment_id}`
- **方法**: PUT
- **作用**: 更新指定ID的评论
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "content": "更新后的评论内容"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 18,
    "content": "更新后的评论内容",
    "author_id": 46,
    "post_id": 24,
    "created_at": "2025-02-21T15:30:45",
    "updated_at": "2025-03-08T12:10:30"
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/comments/18" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{"content": "更新后的评论内容"}'
  ```

### 删除评论

- **路径**: `/api/v1/comments/{comment_id}`
- **方法**: DELETE
- **作用**: 删除指定ID的评论
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "message": "评论已成功删除"
  }
  ```

- **使用示例**:

  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/comments/18" \
       -H "Authorization: Bearer {access_token}"
  ```

## 分类相关

### 获取所有分类

- **路径**: `/api/v1/categories`
- **方法**: GET
- **作用**: 获取所有分类列表，包括层级结构
- **响应格式**:

  ```json
  [
    {
      "id": 28,
      "name": "技术讨论",
      "description": "关于编程、软件开发和技术相关的讨论",
      "parent_id": null,
      "order": 1,
      "created_at": "2025-03-05T18:16:28",
      "children": [
        {
          "id": 33,
          "name": "前端开发",
          "description": "前端技术讨论",
          "parent_id": 28,
          "order": 1,
          "created_at": "2025-03-05T18:16:28",
          "children": []
        },
        {
          "id": 34,
          "name": "后端开发",
          "description": "后端技术讨论",
          "parent_id": 28,
          "order": 2,
          "created_at": "2025-03-05T18:16:28",
          "children": []
        }
      ]
    },
    // 更多分类...
  ]
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/categories"
  ```

### 获取特定分类

- **路径**: `/api/v1/categories/{category_id}`
- **方法**: GET
- **作用**: 获取指定ID的分类详情
- **响应格式**:

  ```json
  {
    "id": 28,
    "name": "技术讨论",
    "description": "关于编程、软件开发和技术相关的讨论",
    "parent_id": null,
    "order": 1,
    "created_at": "2025-03-05T18:16:28",
    "children": [
      {
        "id": 33,
        "name": "前端开发",
        "description": "前端技术讨论",
        "parent_id": 28,
        "order": 1,
        "created_at": "2025-03-05T18:16:28"
      },
      {
        "id": 34,
        "name": "后端开发",
        "description": "后端技术讨论",
        "parent_id": 28,
        "order": 2,
        "created_at": "2025-03-05T18:16:28"
      }
    ]
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/categories/28"
  ```

### 创建分类

- **路径**: `/api/v1/categories`
- **方法**: POST
- **作用**: 创建新分类
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "新分类",
    "description": "新分类的描述",
    "parent_id": null,
    "order": 6
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 35,
    "name": "新分类",
    "description": "新分类的描述",
    "parent_id": null,
    "order": 6,
    "created_at": "2025-03-08T12:25:10"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/categories" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "name": "新分类",
            "description": "新分类的描述",
            "parent_id": null,
            "order": 6
          }'
  ```

### 更新分类

- **路径**: `/api/v1/categories/{category_id}`
- **方法**: PUT
- **作用**: 更新指定ID的分类
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "更新后的分类名",
    "description": "更新后的描述",
    "parent_id": null,
    "order": 6
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 35,
    "name": "更新后的分类名",
    "description": "更新后的描述",
    "parent_id": null,
    "order": 6,
    "created_at": "2025-03-08T12:25:10",
    "updated_at": "2025-03-08T12:30:20"
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/categories/35" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "name": "更新后的分类名",
            "description": "更新后的描述",
            "parent_id": null,
            "order": 6
          }'
  ```

### 删除分类

- **路径**: `/api/v1/categories/{category_id}`
- **方法**: DELETE
- **作用**: 删除指定ID的分类
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "message": "分类已成功删除"
  }
  ```

- **使用示例**:

  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/categories/35" \
       -H "Authorization: Bearer {access_token}"
  ```

## 版块相关

### 获取所有版块

- **路径**: `/api/v1/sections`
- **方法**: GET
- **作用**: 获取所有版块列表
- **响应格式**:

  ```json
  [
    {
      "id": 12,
      "name": "技术区",
      "description": "技术相关讨论",
      "created_at": "2025-03-05T18:16:28"
    },
    {
      "id": 13,
      "name": "交流区",
      "description": "生活、职场交流",
      "created_at": "2025-03-05T18:16:28"
    },
    {
      "id": 14,
      "name": "创意区",
      "description": "创意、灵感分享",
      "created_at": "2025-03-05T18:16:28"
    }
  ]
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/sections"
  ```

### 获取特定版块

- **路径**: `/api/v1/sections/{section_id}`
- **方法**: GET
- **作用**: 获取指定ID的版块详情
- **响应格式**:

  ```json
  {
    "id": 12,
    "name": "技术区",
    "description": "技术相关讨论",
    "created_at": "2025-03-05T18:16:28",
    "categories": [
      {
        "id": 28,
        "name": "技术讨论",
        "description": "关于编程、软件开发和技术相关的讨论"
      },
      // 更多分类...
    ]
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/sections/12"
  ```

### 创建版块

- **路径**: `/api/v1/sections`
- **方法**: POST
- **作用**: 创建新版块
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "新版块",
    "description": "新版块的描述"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 15,
    "name": "新版块",
    "description": "新版块的描述",
    "created_at": "2025-03-08T12:45:30"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/sections" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "name": "新版块",
            "description": "新版块的描述"
          }'
  ```

### 更新版块

- **路径**: `/api/v1/sections/{section_id}`
- **方法**: PUT
- **作用**: 更新指定ID的版块
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "更新后的版块名",
    "description": "更新后的描述"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 15,
    "name": "更新后的版块名",
    "description": "更新后的描述",
    "created_at": "2025-03-08T12:45:30",
    "updated_at": "2025-03-08T12:50:15"
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/sections/15" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{
            "name": "更新后的版块名",
            "description": "更新后的描述"
          }'
  ```

### 删除版块

- **路径**: `/api/v1/sections/{section_id}`
- **方法**: DELETE
- **作用**: 删除指定ID的版块
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "message": "版块已成功删除"
  }
  ```

- **使用示例**:

  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/sections/15" \
       -H "Authorization: Bearer {access_token}"
  ```

## 标签相关

### 获取所有标签

- **路径**: `/api/v1/tags`
- **方法**: GET
- **作用**: 获取所有标签列表
- **响应格式**:

  ```json
  [
    {
      "id": 61,
      "name": "Python",
      "created_at": "2025-03-05T18:16:28"
    },
    {
      "id": 62,
      "name": "JavaScript",
      "created_at": "2025-03-05T18:16:28"
    },
    // 更多标签...
  ]
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/tags"
  ```

### 获取特定标签

- **路径**: `/api/v1/tags/{tag_id}`
- **方法**: GET
- **作用**: 获取指定ID的标签详情
- **响应格式**:

  ```json
  {
    "id": 61,
    "name": "Python",
    "created_at": "2025-03-05T18:16:28",
    "post_count": 5
  }
  ```

- **使用示例**:

  ```bash
  curl -X GET "http://localhost:8000/api/v1/tags/61"
  ```

### 创建标签

- **路径**: `/api/v1/tags`
- **方法**: POST
- **作用**: 创建新标签
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "新标签"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 76,
    "name": "新标签",
    "created_at": "2025-03-08T13:05:45"
  }
  ```

- **使用示例**:

  ```bash
  curl -X POST "http://localhost:8000/api/v1/tags" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{"name": "新标签"}'
  ```

### 更新标签

- **路径**: `/api/v1/tags/{tag_id}`
- **方法**: PUT
- **作用**: 更新指定ID的标签
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **请求体**:

  ```json
  {
    "name": "更新后的标签名"
  }
  ```

- **响应格式**:

  ```json
  {
    "id": 76,
    "name": "更新后的标签名",
    "created_at": "2025-03-08T13:05:45",
    "updated_at": "2025-03-08T13:10:20"
  }
  ```

- **使用示例**:

  ```bash
  curl -X PUT "http://localhost:8000/api/v1/tags/76" \
       -H "Authorization: Bearer {access_token}" \
       -H "Content-Type: application/json" \
       -d '{"name": "更新后的标签名"}'
  ```

### 删除标签

- **路径**: `/api/v1/tags/{tag_id}`
- **方法**: DELETE
- **作用**: 删除指定ID的标签
- **请求头**:
  - `Authorization`: Bearer {access_token}
- **响应格式**:

  ```json
  {
    "message": "标签已成功删除"
  }
  ```

- **使用示例**:

  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/tags/76" \
       -H "Authorization: Bearer {access_token}"
  ```

## 最近更新

### 2024-04-10: 添加邮箱验证和密码重置功能

- 实现了用户注册后的邮箱验证功能，提高账户安全性
- 添加了密码重置功能，允许用户通过邮箱重置密码
- 创建了精美的HTML邮件模板，支持验证和重置邮件
- 使用Redis实现了安全的令牌存储和验证机制
- 实现了防止邮箱探测的安全措施
- 所有功能均支持异步处理，通过Celery任务队列发送邮件

**相关API端点：**

1. 邮箱验证：
   - `POST /api/v1/auth/verify-email` - 通过POST请求验证邮箱
   - `GET /api/v1/auth/verify-email/{token}?email={email}` - 通过邮件链接验证邮箱

2. 密码重置：
   - `POST /api/v1/auth/forgot-password` - 请求密码重置邮件
   - `POST /api/v1/auth/reset-password` - 使用令牌重置密码

### 2024-04-01: 添加用户头像和简介字段

- 在用户数据库模型中添加了`avatar_url`和`bio`字段
- 更新了用户相关的API端点，支持头像和简介信息的获取和更新
- 创建了数据库迁移脚本，用于将新字段添加到现有数据库中
- 修复了BaseRepository中的to_dict方法问题，添加了model_to_dict方法
- 更新了UserService中的update_user方法，添加了current_user_id参数
- 修改了用户API端点中的update_user方法，将update_data参数改为user_data

**用户头像和简介字段说明：**

- `avatar_url`: 用户头像的URL地址，类型为VARCHAR(255)，可为空
- `bio`: 用户个人简介，类型为TEXT，可为空

**相关API端点：**

1. 获取用户资料：`GET /api/v1/users/me/profile` - 返回包含头像和简介的用户资料
2. 更新用户信息：`PUT /api/v1/users/{user_id}` - 支持更新头像和简介信息

**示例请求：**

```bash
# 更新用户头像和简介
curl -X PUT "http://localhost:8000/api/v1/users/46" \
     -H "Authorization: Bearer {access_token}" \
     -H "Content-Type: application/json" \
     -d '{
          "bio": "热爱技术，专注于Web开发和人工智能",
          "avatar_url": "https://example.com/avatars/user46.jpg"
        }'
```

**示例响应：**

```json
{
  "username": "admin",
  "email": "admin@example.com",
  "bio": "热爱技术，专注于Web开发和人工智能",
  "avatar_url": "https://example.com/avatars/user46.jpg",
  "id": 46,
  "is_active": true,
  "role": "admin",
  "created_at": "2025-03-05T18:16:28",
  "updated_at": "2025-03-08T04:12:39"
}
```

**获取用户资料示例：**

```bash
# 获取当前用户资料
curl -X GET "http://localhost:8000/api/v1/users/me/profile" \
     -H "Authorization: Bearer {access_token}"
```

**响应示例：**

```json
{
  "username": "admin",
  "email": "admin@example.com",
  "bio": "系统管理员，负责论坛维护工作",
  "avatar_url": "https://example.com/avatars/admin.jpg",
  "id": 46,
  "is_active": true,
  "role": "admin",
  "created_at": "2025-03-05T18:16:28",
  "updated_at": "2025-03-08T04:12:39",
  "post_count": 1,
  "comment_count": 1,
  "last_login": null,
  "join_date": "2025-03-05T18:16:28",
  "reputation": 0,
  "badges": []
}
```

## 响应模型结构

项目使用了模块化的响应模型结构，每种资源类型都有独立的响应模型文件：

- `app/api/responses/base.py` - 基础响应模型
- `app/api/responses/auth.py` - 认证相关响应
- `app/api/responses/user.py` - 用户相关响应
- `app/api/responses/post.py` - 帖子相关响应
- `app/api/responses/comment.py` - 评论相关响应
- `app/api/responses/category.py` - 分类相关响应
- `app/api/responses/section.py` - 板块相关响应
- `app/api/responses/tag.py` - 标签相关响应

## 装饰器系统

项目实现了一套强大的装饰器系统，用于简化API开发：

- `rate_limit` - 请求速率限制
- `cache_response` - 响应缓存
- `validate_permissions` - 权限验证
- `log_activity` - 活动日志记录
- `error_handler` - 统一错误处理
- `transaction` - 数据库事务管理

### 装饰器示例

```python
@router.get("/{post_id}", response_model=post_schema.Post)
@rate_limit(limit=100, window=60)  # 每60秒限制100次请求
@cache_response(expire=300)        # 缓存结果5分钟
@log_activity("查看帖子")          # 记录用户活动
async def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # 业务逻辑...
```

## 性能优化

本项目实现了多种性能优化措施：

1. **响应缓存**: 使用Redis缓存API响应，减少数据库负载。
2. **速率限制**: 使用装饰器对API请求进行速率限制，防止滥用。
3. **异步处理**: 对耗时操作使用异步任务处理。
4. **连接池**: 数据库和Redis使用连接池管理资源。
5. **延迟加载**: ORM模型使用延迟加载优化查询性能。

## 安全措施

1. **JWT认证**: 使用JWT进行API认证。
2. **密码哈希**: 使用Argon2或Bcrypt进行密码哈希。
3. **CORS保护**: 配置合适的CORS策略。
4. **速率限制**: 防止暴力破解攻击。
5. **中间件保护**: 使用多层安全中间件。
6. **CAPTCHA验证**: 防止自动化工具滥用。

## 开发指南

### 添加新的API端点

1. 在 `app/api/endpoints/` 中创建或更新相应的路由文件
2. 在 `app/api/responses/` 中定义相应的响应模型
3. 在 `app/db/models/` 中更新数据库模型（如需要）
4. 在 `app/schemas/` 中定义请求验证模式
5. 在 `app/services/` 中实现业务逻辑
6. 在 `app/api/router.py` 中注册新的路由

### 代码风格

- 使用 Black 格式化代码
- 使用 isort 排序导入
- 使用 flake8 检查代码质量
- 使用 mypy 进行类型检查
