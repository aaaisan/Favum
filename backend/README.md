# Forum 论坛系统

一个基于 FastAPI 和 SQLAlchemy 构建的现代化论坛系统。

## 功能特点

- 用户管理
  - 用户注册、登录、注销
  - 基于角色的权限管理
  - 用户信息管理
  
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
- PostgreSQL
- Node.js 14+ (用于前端)

## 安装步骤

1. 克隆项目

```bash
git clone https://github.com/yourusername/forum.git
cd forum
```

2. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

4. 安装前端依赖

```bash
cd frontend
npm install
```

## 配置

1. 复制环境变量示例文件

```bash
cp .env.example .env
```

2. 修改 `.env` 文件中的配置：

```ini
# API配置
API_V1_PREFIX=/api/v1
PROJECT_NAME=Forum
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/forum

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

2. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload
```

3. 启动 Celery Worker

```bash
cd backend
celery -A app.core.celery_config worker --loglevel=info
```

4. 启动 Celery Beat（用于定时任务）

```bash
cd backend
celery -A app.core.celery_config beat --loglevel=info
```

5. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

现在可以访问以下地址：

- 后端 API: <http://localhost:8000>
- API 文档: <http://localhost:8000/docs>
- 前端应用: <http://localhost:3000>

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
| `/register` | POST | 注册新用户 | 无 | UserRegister 对象 | Token 对象，包含 access_token |
| `/login` | POST | 用户登录 | 无 | Login 对象(用户名、密码、验证码) | Token 对象，包含 access_token |
| `/test-token` | POST | 测试令牌有效性 | 有效令牌 | 无 | TokenData 对象，含用户信息 |

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

```
forum/
├── backend/
│   ├── alembic/            # 数据库迁移
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── endpoints/  # 各模块 API 端点
│   │   │   └── router.py   # API 路由注册
│   │   ├── core/           # 核心功能
│   │   │   ├── config.py   # 配置管理
│   │   │   ├── security.py # 安全相关
│   │   │   └── permissions.py # 权限管理
│   │   ├── db/             # 数据库配置
│   │   │   ├── database.py # 数据库连接
│   │   │   ├── models/     # SQLAlchemy 模型
│   │   │   └── repositories/ # 数据访问层
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 业务服务层
│   │   ├── utils/          # 工具函数和类
│   │   │   ├── api_decorators.py # API装饰器
│   │   │   └── captcha.py  # 验证码工具
│   │   ├── tasks/          # Celery 任务
│   │   └── middlewares/    # 中间件
│   ├── tests/              # 测试文件
│   └── requirements.txt    # 依赖文件
└── frontend/               # 前端代码
```

## 主要依赖包

```
fastapi==0.104.1
sqlalchemy==2.0.23
pydantic==2.4.2
alembic==1.12.1
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
emails==0.6
```

## 开发指南

1. 在 `app/models/` 下定义数据模型
2. 在 `app/schemas/` 下定义数据验证模式
3. 在 `app/db/repositories/` 下实现数据访问层
4. 在 `app/services/` 下实现业务逻辑层
5. 在 `app/api/endpoints/` 下实现API端点
6. 在 `app/utils/` 下实现工具函数和类
7. 在 `app/tasks/` 下实现异步任务

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

## 常见错误及解决方案

### 1. 未定义"status"错误

**错误信息**：

```
未定义"status"
```

**原因**：在使用 FastAPI 的 HTTP 状态码（如 `status.HTTP_403_FORBIDDEN`）时，忘记导入 status 模块。

**解决方案**：
在文件顶部添加以下导入语句：

```python
from fastapi import status
```

或者如果已经导入了其他 FastAPI 组件：

```python
from fastapi import HTTPException, Request, status
```

### 2. Redis 反序列化失败

**错误信息**：

```
反序列化失败: Expecting value: line 1 column 1 (char 0)
```

**原因**：Redis 中存储的数据不是有效的 JSON 格式或为空。

**解决方案**：

- 检查缓存写入逻辑，确保存入的是有效的 JSON 数据
- 如果问题持续，可以考虑清空 Redis 缓存：

  ```bash
  redis-cli FLUSHDB
  ```

### 3. 异步与同步 Redis 操作混用

**错误信息**：

```
不允许在异步上下文中使用同步方法
```

**原因**：在异步函数中使用了同步的 Redis 客户端方法。

**解决方案**：

确保在异步上下文中使用异步的 Redis 客户端方法：

```python
# 错误示例
redis_client.get(key)  # 同步方法

# 正确示例
await redis_client.get(key)  # 异步方法
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

项目维护者 - yourname@example.com

项目链接: [https://github.com/yourusername/forum](https://github.com/yourusername/forum)
