# Forum Application

This is a forum application with a Vue.js frontend and Node.js backend.

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file based on the `.env.example` file:
   ```
   cp .env.example .env
   ```

4. Reset the database (clears existing data and seeds with mock data):
   ```
   npm run reset-db
   ```

5. Start the backend server:
   ```
   npm run dev
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## Database Management

The backend includes scripts to manage the database:

- `npm run clear-db` - Clears all data from the database
- `npm run seed` - Seeds the database with mock data
- `npm run reset-db` - Combines both (clear and seed)

## Available API Endpoints

The backend API provides the following endpoints:

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token

### Users
- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get user by ID
- `GET /api/users/:id/posts` - Get posts by user ID

### Posts
- `GET /api/posts` - Get all posts with pagination
- `GET /api/posts/:id` - Get post by ID
- `POST /api/posts` - Create a new post
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/:id/posts` - Get posts by category

### Tags
- `GET /api/tags` - Get all tags
- `GET /api/tags/:id/posts` - Get posts by tag

### Comments
- `GET /api/posts/:id/comments` - Get comments for a post
- `POST /api/posts/:id/comments` - Add a comment to a post

# Forum API 文档

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

### 创建帖子
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