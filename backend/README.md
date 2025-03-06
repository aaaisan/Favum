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

## 目录结构

```
forum/
├── backend/
│   ├── alembic/            # 数据库迁移
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心功能
│   │   ├── crud/           # 数据库操作
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 业务逻辑
│   │   ├── tasks/          # Celery 任务
│   │   └── utils/          # 工具函数
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

### 添加新的 API 端点

1. 在 `app/api/endpoints/` 下创建新的路由文件
2. 在 `app/api/api_v1/api.py` 中注册路由
3. 在 `app/schemas/` 下创建相应的 Pydantic 模型
4. 在 `app/crud/` 下实现数据库操作
5. 在 `app/services/` 下实现业务逻辑

### 添加新的 Celery 任务

1. 在 `app/tasks/` 下创建新的任务文件
2. 在 `app/core/celery_config.py` 中注册任务

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
TypeError: object NoneType can't be used in 'await' expression
```

**原因**：混用同步和异步的 Redis 客户端方法。

**解决方案**：

- 对于同步 Redis 客户端，直接调用方法：`redis_client.get(key)`
- 对于异步 Redis 客户端，使用 await：`await redis_client.get(key)`
- 确保项目中统一使用一种方式

## 测试

运行测试：

```bash
cd backend
pytest
```

生成测试覆盖率报告：

```bash
pytest --cov=app --cov-report=html
```

## 部署

1. 构建前端

```bash
cd frontend
npm run build
```

2. 使用 Docker 部署（推荐）

```bash
docker-compose up -d
```

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 联系方式

- 项目维护者：[Your Name](mailto:your.email@example.com)
- 项目主页：[GitHub](https://github.com/yourusername/forum)

## 致谢

感谢所有为这个项目做出贡献的开发者！

## 软删除设计

### 特性

1. **数据保留**: 被"删除"的数据实际上仍然保留在数据库中
2. **删除标记**: 使用`is_deleted`布尔字段标记记录是否被删除
3. **删除时间**: 主要实体（用户、帖子、评论等）包含`deleted_at`时间戳，记录删除时间
4. **查询过滤**: 所有默认查询自动过滤掉已删除的记录
5. **恢复机制**: 支持将已删除的记录恢复到正常状态

### 优势

1. **数据安全**: 防止意外删除导致的数据丢失
2. **审计跟踪**: 保留操作历史，有助于审计和合规
3. **数据恢复**: 允许恢复误删的数据
4. **减少级联影响**: 避免外键约束引起的问题
5. **统计分析**: 删除的数据仍可用于历史统计分析

### 实现步骤

1. 所有表添加`is_deleted`布尔字段，默认为`false`
2. 主要实体表添加`deleted_at`时间戳字段
3. 修改所有查询方法，默认过滤掉已删除记录
4. 修改删除操作，实现软删除而非物理删除
5. 添加恢复功能，允许将软删除的记录恢复
6. 保留物理删除方法仅用于特殊情况和管理员权限

### 恢复功能

恢复功能允许将已删除的记录恢复到正常状态：

1. **基础层实现**: 
   - 仓储层: `BaseRepository.restore(id)`
   - 服务层: `BaseService.restore(id)`
   - CRUD层: `CRUDBase.restore(id)`

2. **API接口**:
   - 通用恢复接口: `POST /{resource}/{id}/restore`
   - 用户恢复接口: `POST /users/{user_id}/restore`

3. **权限控制**:
   - 恢复操作通常需要管理员权限
   - 使用角色限制确保只有管理员可以执行恢复操作

4. **最佳实践**:
   - 恢复前验证记录是否存在且已被删除
   - 清除`deleted_at`时间戳
   - 设置`is_deleted`为`false`
   - 提供明确的成功/失败消息

## 点赞和收藏功能

### 点赞功能

点赞功能允许用户对帖子表达喜欢或不喜欢，增强用户互动体验。

#### 功能特点

1. **双向投票**: 支持点赞（upvote）和反对（downvote）两种操作
2. **投票切换**: 用户可以在不同投票类型间切换，或取消已有投票
3. **投票统计**: 实时统计并显示帖子的净赞数（赞成数减去反对数）
4. **前端提示**: 根据操作结果提供清晰的反馈消息

#### 数据模型

点赞功能基于以下数据模型：

```python
# 投票类型枚举
class VoteType(enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

# 投票记录表
class PostVote(Base):
    __tablename__ = "post_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    post = relationship("Post", back_populates="votes")
    user = relationship("User", back_populates="post_votes")
    
    # 唯一约束：一个用户对一个帖子只能有一个投票
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uix_user_post_vote'),
    )
```

#### 实现逻辑

点赞功能的核心逻辑包括：

1. **创建投票**: 当用户首次对帖子投票时创建新记录
2. **更新投票**: 当用户更改投票类型时更新记录
3. **删除投票**: 当用户取消投票时删除记录
4. **更新计数**: 每次投票操作后更新帖子的总赞数

#### 使用方法

前端应用可以通过以下方式实现点赞功能：

1. **获取帖子赞数**:
   ```javascript
   // 获取帖子赞数
   async function getVoteCount(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/votes`);
     return await response.json();
   }
   ```

2. **用户投票**:
   ```javascript
   // 用户点赞
   async function upvotePost(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/vote`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         'Authorization': `Bearer ${userToken}`
       },
       body: JSON.stringify({ vote_type: 'upvote' })
     });
     return await response.json();
   }
   
   // 用户反对
   async function downvotePost(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/vote`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         'Authorization': `Bearer ${userToken}`
       },
       body: JSON.stringify({ vote_type: 'downvote' })
     });
     return await response.json();
   }
   ```

3. **处理响应**:
   ```javascript
   // 处理投票响应
   function handleVoteResponse(response) {
     if (response.success) {
       // 更新UI显示
       updateVoteCount(response.vote_count);
       showMessage(response.message); // 例如："点赞成功"、"取消点赞"等
     } else {
       // 处理错误
       showError(response.message);
     }
   }
   ```

### 收藏功能

收藏功能允许用户保存感兴趣的帖子，方便后续查看。

#### 功能特点

1. **添加收藏**: 用户可以将感兴趣的帖子添加到个人收藏列表
2. **取消收藏**: 支持从收藏列表中移除帖子
3. **收藏状态**: 可查询帖子的收藏状态
4. **收藏列表**: 用户可查看自己的收藏列表
5. **公开收藏**: 其他用户可查看用户的公开收藏

#### 数据模型

收藏功能基于以下数据模型：

```python
# 收藏记录表
class PostFavorite(Base):
    __tablename__ = "post_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    post = relationship("Post", back_populates="favorites")
    user = relationship("User", back_populates="favorites")
    
    # 唯一约束：一个用户不能重复收藏同一个帖子
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uix_user_post_favorite'),
    )
```

#### 实现逻辑

收藏功能的核心逻辑包括：

1. **添加收藏**: 创建用户与帖子之间的收藏关系记录
2. **取消收藏**: 删除用户与帖子之间的收藏关系记录
3. **检查状态**: 查询是否存在收藏关系记录
4. **查询列表**: 获取用户收藏的所有帖子

#### 使用方法

前端应用可以通过以下方式实现收藏功能：

1. **检查收藏状态**:
   ```javascript
   // 检查帖子是否已收藏
   async function checkFavoriteStatus(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/favorite/status`, {
       headers: {
         'Authorization': `Bearer ${userToken}`
       }
     });
     return await response.json();
   }
   ```

2. **添加收藏**:
   ```javascript
   // 收藏帖子
   async function favoritePost(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/favorite`, {
       method: 'POST',
       headers: {
         'Authorization': `Bearer ${userToken}`
       }
     });
     return await response.json();
   }
   ```

3. **取消收藏**:
   ```javascript
   // 取消收藏
   async function unfavoritePost(postId) {
     const response = await fetch(`/api/v1/posts/${postId}/favorite`, {
       method: 'DELETE',
       headers: {
         'Authorization': `Bearer ${userToken}`
       }
     });
     return await response.json();
   }
   ```

4. **获取收藏列表**:
   ```javascript
   // 获取当前用户的收藏列表
   async function getUserFavorites() {
     const response = await fetch('/api/v1/users/me/favorites', {
       headers: {
         'Authorization': `Bearer ${userToken}`
       }
     });
     return await response.json();
   }
   ```

### 前端集成示例

以下是如何在前端页面中集成点赞和收藏功能的示例：

```jsx
// React组件示例
function PostActions({ post, userToken }) {
  const [voteCount, setVoteCount] = useState(post.vote_count);
  const [isFavorited, setIsFavorited] = useState(false);
  const [userVote, setUserVote] = useState(null); // 'upvote', 'downvote', 或 null
  
  // 初始化加载
  useEffect(() => {
    checkFavoriteStatus(post.id).then(status => setIsFavorited(status));
    // 这里可以添加获取用户当前投票状态的逻辑
  }, [post.id]);
  
  // 处理点赞
  const handleUpvote = async () => {
    const response = await upvotePost(post.id);
    if (response.success) {
      setVoteCount(response.vote_count);
      setUserVote(userVote === 'upvote' ? null : 'upvote');
      showToast(response.message);
    }
  };
  
  // 处理反对
  const handleDownvote = async () => {
    const response = await downvotePost(post.id);
    if (response.success) {
      setVoteCount(response.vote_count);
      setUserVote(userVote === 'downvote' ? null : 'downvote');
      showToast(response.message);
    }
  };
  
  // 处理收藏
  const handleFavorite = async () => {
    if (isFavorited) {
      const response = await unfavoritePost(post.id);
      if (response.success) {
        setIsFavorited(false);
        showToast(response.message);
      }
    } else {
      const response = await favoritePost(post.id);
      if (response.success) {
        setIsFavorited(true);
        showToast(response.message);
      }
    }
  };
  
  return (
    <div className="post-actions">
      <div className="vote-actions">
        <button 
          className={`upvote ${userVote === 'upvote' ? 'active' : ''}`}
          onClick={handleUpvote}
        >
          <ThumbUpIcon /> 赞
        </button>
        <span className="vote-count">{voteCount}</span>
        <button 
          className={`downvote ${userVote === 'downvote' ? 'active' : ''}`}
          onClick={handleDownvote}
        >
          <ThumbDownIcon /> 踩
        </button>
      </div>
      
      <button 
        className={`favorite ${isFavorited ? 'active' : ''}`}
        onClick={handleFavorite}
      >
        <BookmarkIcon /> {isFavorited ? '已收藏' : '收藏'}
      </button>
    </div>
  );
}
```

### 最佳实践

1. **错误处理**: 前端应妥善处理API调用可能出现的错误情况
2. **加载状态**: 在API调用期间显示加载状态，提升用户体验
3. **反馈信息**: 操作后显示清晰的成功/失败提示
4. **缓存状态**: 可以在本地缓存用户的投票和收藏状态，减少API调用
5. **权限检查**: 对需要登录的操作先检查用户是否已登录
6. **响应式更新**: 操作后立即更新UI，不等待页面刷新

## API接口详细说明

本节详细说明系统中各个API端点的用法、所需权限和返回值。

### 用户相关接口

#### 1. 获取用户列表

- **路径**: `/api/v1/users/`
- **方法**: `GET`
- **权限**: 需要登录，且必须是管理员或超级管理员
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 用户对象数组
- **说明**: 获取系统中的用户列表，支持分页

#### 2. 获取用户详情

- **路径**: `/api/v1/users/{user_id}`
- **方法**: `GET`
- **权限**: 需要登录，且必须是自己、版主或管理员
- **返回值**: 用户对象
- **说明**: 获取指定ID的用户详细信息

#### 3. 创建用户

- **路径**: `/api/v1/users/`
- **方法**: `POST`
- **权限**: 无（公开接口）
- **请求体**: 
  ```json
  {
    "username": "用户名",
    "email": "邮箱地址",
    "password": "密码",
    "full_name": "全名"
  }
  ```
- **返回值**: 创建的用户对象
- **说明**: 创建新用户账号

#### 4. 更新用户信息

- **路径**: `/api/v1/users/{user_id}`
- **方法**: `PUT`
- **权限**: 需要登录，且必须是自己或管理员
- **请求体**: 
  ```json
  {
    "username": "新用户名",
    "email": "新邮箱",
    "full_name": "新全名",
    "is_active": true
  }
  ```
- **返回值**: 更新后的用户对象
- **说明**: 更新指定ID的用户信息

#### 5. 获取当前用户收藏列表

- **路径**: `/api/v1/users/me/favorites`
- **方法**: `GET`
- **权限**: 需要登录
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 
  ```json
  {
    "items": [帖子对象数组],
    "total": 帖子总数
  }
  ```
- **说明**: 获取当前登录用户的收藏帖子列表

#### 6. 获取指定用户的收藏列表

- **路径**: `/api/v1/users/{user_id}/favorites`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 
  ```json
  {
    "items": [帖子对象数组],
    "total": 帖子总数
  }
  ```
- **说明**: 获取指定用户的公开收藏帖子列表

### 认证相关接口

#### 1. 用户注册

- **路径**: `/api/v1/auth/register`
- **方法**: `POST`
- **权限**: 无（公开接口）
- **请求体**: 
  ```json
  {
    "username": "用户名",
    "email": "邮箱地址",
    "password": "密码",
    "captcha_id": "验证码ID",
    "captcha_code": "验证码内容"
  }
  ```
- **返回值**: 
  ```json
  {
    "access_token": "JWT令牌",
    "token_type": "bearer"
  }
  ```
- **说明**: 创建新用户并返回访问令牌

#### 2. 用户登录

- **路径**: `/api/v1/auth/login`
- **方法**: `POST`
- **权限**: 无（公开接口）
- **请求体**: 
  ```json
  {
    "username": "用户名",
    "password": "密码",
    "captcha_id": "验证码ID",
    "captcha_code": "验证码内容"
  }
  ```
- **返回值**: 
  ```json
  {
    "access_token": "JWT令牌",
    "token_type": "bearer"
  }
  ```
- **说明**: 验证用户凭据并返回访问令牌

### 帖子相关接口

#### 1. 获取帖子列表

- **路径**: `/api/v1/posts/`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 帖子对象数组
- **说明**: 获取系统中的帖子列表，支持分页

#### 2. 获取帖子详情

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **返回值**: 帖子对象
- **说明**: 获取指定ID的帖子详细信息

#### 3. 创建帖子

- **路径**: `/api/v1/posts/`
- **方法**: `POST`
- **权限**: 需要登录
- **请求体**: 
  ```json
  {
    "title": "帖子标题",
    "content": "帖子内容",
    "category_id": 1,
    "author_id": 1,
    "section_id": 1,
    "tag_ids": [1, 2, 3]
  }
  ```
- **返回值**: 创建的帖子对象
- **说明**: 创建新帖子

#### 4. 更新帖子

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: `PUT`
- **权限**: 需要登录，且必须是帖子作者、版主或管理员
- **请求体**: 
  ```json
  {
    "title": "更新的标题",
    "content": "更新的内容",
    "category_id": 1,
    "tag_ids": [1, 2, 3],
    "is_hidden": false
  }
  ```
- **返回值**: 更新后的帖子对象
- **说明**: 更新指定ID的帖子信息

#### 5. 删除帖子（软删除）

- **路径**: `/api/v1/posts/{post_id}`
- **方法**: `DELETE`
- **权限**: 需要登录，且必须是帖子作者、版主或管理员
- **返回值**: 
  ```json
  {
    "detail": "帖子已删除"
  }
  ```
- **说明**: 软删除指定的帖子

#### 6. 恢复已删除的帖子

- **路径**: `/api/v1/posts/{post_id}/restore`
- **方法**: `POST`
- **权限**: 需要登录，且必须是版主或管理员
- **返回值**: 
  ```json
  {
    "detail": "帖子已恢复"
  }
  ```
- **说明**: 恢复指定的已删除帖子

#### 7. 切换帖子可见性

- **路径**: `/api/v1/posts/{post_id}/visibility`
- **方法**: `PATCH`
- **权限**: 需要登录，且必须是帖子作者、对应版块的版主或管理员
- **请求体**: 
  ```json
  {
    "hidden": true
  }
  ```
- **返回值**: 
  ```json
  {
    "detail": "帖子已隐藏",
    "post_id": 1,
    "is_hidden": true
  }
  ```
- **说明**: 隐藏或显示指定的帖子

### 点赞相关接口

#### 1. 对帖子点赞/取消点赞

- **路径**: `/api/v1/posts/{post_id}/vote`
- **方法**: `POST`
- **权限**: 无（公开接口，但通常需要登录）
- **请求体**: 
  ```json
  {
    "vote_type": "upvote"  // 或 "downvote"
  }
  ```
- **返回值**: 
  ```json
  {
    "success": true,
    "vote_count": 5,
    "message": "点赞成功"  // 或 "取消点赞", "取消反对", "反对成功"
  }
  ```
- **说明**: 
  - 用户可以对帖子进行点赞（赞数+1）或反对（赞数-1）
  - 如果用户已经点赞/反对过该帖子，则再次点击相同操作会取消
  - 如果用户已经点赞后点击反对，会取消点赞并添加反对，反之亦然

#### 2. 获取帖子点赞数

- **路径**: `/api/v1/posts/{post_id}/votes`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **返回值**: 帖子的点赞数（整数）
- **说明**: 获取指定帖子的点赞数

### 收藏相关接口

#### 1. 收藏帖子

- **路径**: `/api/v1/posts/{post_id}/favorite`
- **方法**: `POST`
- **权限**: 需要登录
- **返回值**: 
  ```json
  {
    "success": true,
    "message": "帖子收藏成功"
  }
  ```
- **说明**: 将指定帖子添加到当前用户的收藏列表中

#### 2. 取消收藏

- **路径**: `/api/v1/posts/{post_id}/favorite`
- **方法**: `DELETE`
- **权限**: 需要登录
- **返回值**: 
  ```json
  {
    "success": true,
    "message": "已取消收藏"
  }
  ```
- **说明**: 从当前用户的收藏列表中移除指定帖子

#### 3. 检查收藏状态

- **路径**: `/api/v1/posts/{post_id}/favorite/status`
- **方法**: `GET`
- **权限**: 无（公开接口，未登录时返回false）
- **返回值**: 布尔值，表示当前用户是否已收藏该帖子
- **说明**: 检查当前用户是否已收藏指定帖子

#### 4. 获取用户收藏列表

- **路径**: `/api/v1/users/me/favorites`
- **方法**: `GET`
- **权限**: 需要登录
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认20）
- **返回值**: 帖子对象数组
- **说明**: 获取当前用户的收藏帖子列表

### 分类相关接口

#### 1. 获取分类列表

- **路径**: `/api/v1/categories/`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 分类对象数组
- **说明**: 获取所有分类的列表，支持分页

#### 2. 获取分类详情

- **路径**: `/api/v1/categories/{category_id}`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **返回值**: 分类对象
- **说明**: 获取指定ID的分类详细信息

#### 3. 创建分类

- **路径**: `/api/v1/categories/`
- **方法**: `POST`
- **权限**: 需要登录，且必须是管理员
- **请求体**: 
  ```json
  {
    "name": "分类名称",
    "description": "分类描述"
  }
  ```
- **返回值**: 创建的分类对象
- **说明**: 创建新分类，仅管理员可执行

### 评论相关接口

#### 1. 创建评论

- **路径**: `/api/v1/comments/`
- **方法**: `POST`
- **权限**: 需要登录，且拥有CREATE_COMMENT权限
- **请求体**: 
  ```json
  {
    "content": "评论内容",
    "post_id": 1,
    "parent_id": null
  }
  ```
- **返回值**: 创建的评论对象
- **说明**: 创建新评论，可以是帖子的直接评论，也可以是对其他评论的回复

#### 2. 获取帖子评论列表

- **路径**: `/api/v1/comments/post/{post_id}`
- **方法**: `GET`
- **权限**: 需要登录
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 评论对象数组
- **说明**: 获取指定帖子下的所有评论，支持分页

### 版块相关接口

#### 1. 获取版块列表

- **路径**: `/api/v1/sections/`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 版块对象数组
- **说明**: 获取所有论坛版块的列表，支持分页

#### 2. 创建版块

- **路径**: `/api/v1/sections/`
- **方法**: `POST`
- **权限**: 需要登录，且必须是管理员
- **请求体**: 
  ```json
  {
    "name": "版块名称",
    "description": "版块描述",
    "icon": "版块图标URL",
    "color": "#颜色代码",
    "sort_order": 1
  }
  ```
- **返回值**: 创建的版块对象
- **说明**: 创建新版块，仅管理员可执行

#### 3. 更新版块

- **路径**: `/api/v1/sections/{section_id}`
- **方法**: `PUT`
- **权限**: 需要登录，且必须是管理员
- **请求体**: 
  ```json
  {
    "name": "更新的版块名称",
    "description": "更新的版块描述",
    "icon": "更新的版块图标URL",
    "color": "#更新的颜色代码",
    "sort_order": 2
  }
  ```
- **返回值**: 更新后的版块对象
- **说明**: 更新指定版块信息，仅管理员可执行

#### 4. 添加版主

- **路径**: `/api/v1/sections/{section_id}/moderators/{user_id}`
- **方法**: `POST`
- **权限**: 需要登录，且必须是管理员
- **返回值**: 
  ```json
  {
    "detail": "版主添加成功"
  }
  ```
- **说明**: 将指定用户添加为指定版块的版主

#### 5. 移除版主

- **路径**: `/api/v1/sections/{section_id}/moderators/{user_id}`
- **方法**: `DELETE`
- **权限**: 需要登录，且必须是管理员
- **返回值**: 
  ```json
  {
    "detail": "版主移除成功"
  }
  ```
- **说明**: 将指定用户从指定版块的版主列表中移除

#### 6. 获取版块帖子

- **路径**: `/api/v1/sections/{section_id}/posts`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认20）
- **返回值**: 帖子对象数组
- **说明**: 获取指定版块下的所有帖子，支持分页

#### 7. 删除版块

- **路径**: `/api/v1/sections/{section_id}`
- **方法**: `DELETE`
- **权限**: 需要登录，且必须是管理员
- **返回值**: 
  ```json
  {
    "detail": "版块已删除"
  }
  ```
- **说明**: 删除指定版块（软删除）

#### 8. 恢复已删除的版块

- **路径**: `/api/v1/sections/{section_id}/restore`
- **方法**: `POST`
- **权限**: 需要登录，且必须是管理员
- **返回值**: 
  ```json
  {
    "detail": "版块已恢复"
  }
  ```
- **说明**: 恢复已删除的版块

### 标签相关接口

#### 1. 获取标签列表

- **路径**: `/api/v1/tags/`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 标签对象数组
- **说明**: 获取所有标签的列表，支持分页

#### 2. 获取热门标签

- **路径**: `/api/v1/tags/popular`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `limit`: 返回的标签数量（默认10）
- **返回值**: 标签对象数组
- **说明**: 获取使用次数最多的标签列表，按使用次数降序排序

#### 3. 获取最近标签

- **路径**: `/api/v1/tags/recent`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **查询参数**: 
  - `limit`: 返回的标签数量（默认10）
- **返回值**: 标签对象数组
- **说明**: 获取最近使用的标签列表，按最后使用时间降序排序

#### 4. 创建标签

- **路径**: `/api/v1/tags/`
- **方法**: `POST`
- **权限**: 需要登录，且必须是管理员
- **请求体**: 
  ```json
  {
    "name": "标签名称",
    "description": "标签描述",
    "color": "#颜色代码"
  }
  ```
- **返回值**: 创建的标签对象
- **说明**: 创建新标签，仅管理员可执行

#### 5. 更新标签

- **路径**: `/api/v1/tags/{tag_id}`
- **方法**: `PUT`
- **权限**: 需要登录，且必须是管理员
- **请求体**: 
  ```json
  {
    "name": "更新的标签名称",
    "description": "更新的标签描述",
    "color": "#更新的颜色代码"
  }
  ```
- **返回值**: 更新后的标签对象
- **说明**: 更新指定标签信息，仅管理员可执行

### 验证码相关接口

#### 1. 生成验证码

- **路径**: `/api/v1/captcha/generate`
- **方法**: `GET`
- **权限**: 无（公开接口）
- **返回值**: 
  - 验证码图片（二进制数据）
  - 响应头中包含验证码ID: `X-Captcha-ID`
- **说明**: 生成验证码图片，验证码将在配置的时间后过期

#### 2. 验证验证码

- **路径**: `/api/v1/captcha/verify/{captcha_id}`
- **方法**: `POST`
- **权限**: 无（公开接口）
- **请求体**: 
  ```json
  {
    "code": "用户输入的验证码"
  }
  ```
- **返回值**: 
  ```json
  {
    "detail": "验证成功"
  }
  ```
- **说明**: 
  - 验证用户输入的验证码是否正确
  - 验证码验证后立即删除，防止重复使用
  - 不区分大小写进行验证

### 任务相关接口

#### 1. 获取任务状态

- **路径**: `/api/v1/tasks/status/{task_id}`
- **方法**: `GET`
- **权限**: 需要登录，且拥有VIEW_TASKS权限
- **返回值**: 任务状态信息
- **说明**: 获取指定任务的状态信息

#### 2. 获取任务详情

- **路径**: `/api/v1/tasks/info/{task_id}`
- **方法**: `GET`
- **权限**: 需要登录
- **返回值**: 任务详细信息
- **说明**: 获取指定任务的详细信息

#### 3. 获取活动任务

- **路径**: `/api/v1/tasks/active`
- **方法**: `GET`
- **权限**: 需要登录
- **返回值**: 活动任务列表
- **说明**: 获取所有当前活动的任务

#### 4. 取消任务

- **路径**: `/api/v1/tasks/revoke/{task_id}`
- **方法**: `POST`
- **权限**: 需要登录
- **查询参数**: 
  - `terminate`: 是否终止任务（默认false）
- **返回值**: 
  ```json
  {
    "detail": "任务已取消"
  }
  ```
- **说明**: 取消指定的任务，可选择是否强制终止

#### 5. 重试任务

- **路径**: `/api/v1/tasks/retry/{task_id}`
- **方法**: `POST`
- **权限**: 需要登录
- **返回值**: 
  ```json
  {
    "detail": "任务已重新提交"
  }
  ```
- **说明**: 重新提交执行已完成或失败的任务

#### 6. 获取任务列表

- **路径**: `/api/v1/tasks/list`
- **方法**: `GET`
- **权限**: 需要登录，且拥有VIEW_TASKS权限
- **查询参数**: 
  - `task_type`: 任务类型（可选）
  - `skip`: 分页偏移量（默认0）
  - `limit`: 每页数量（默认100）
- **返回值**: 任务对象数组
- **说明**: 获取任务列表，支持按类型筛选和分页

#### 7. 注册任务

- **路径**: `/api/v1/tasks/register`
- **方法**: `POST`
- **权限**: 需要登录，且同时拥有MANAGE_TASKS和EXECUTE_TASKS权限
- **请求体**: 
  ```json
  {
    "name": "任务名称",
    "task_type": "任务类型",
    "params": {
      "参数1": "值1",
      "参数2": "值2"
    },
    "scheduled_time": "2025-01-01T00:00:00Z"
  }
  ```
- **返回值**: 注册成功的任务信息
- **说明**: 注册一个新任务，可以是立即执行或计划执行的任务

#### 8. 删除任务

- **路径**: `/api/v1/tasks/{task_id}`
- **方法**: `DELETE`
- **权限**: 需要登录，且拥有MANAGE_TASKS权限
- **返回值**: 
  ```json
  {
    "detail": "任务已删除"
  }
  ```
- **说明**: 删除指定任务的记录

#### 9. 获取任务统计信息

- **路径**: `/api/v1/tasks/stats`
- **方法**: `GET`
- **权限**: 需要登录，且必须是管理员
- **返回值**: 任务统计信息，包含任务执行状态、工作节点状态等
- **说明**: 获取系统任务相关的统计信息，用于监控和管理

### 接口使用注意事项

1. **认证方式**
   - 需要登录的接口应在请求头中包含`Authorization`字段
   - 格式为`Bearer {token}`，其中`{token}`是登录或注册时获取的JWT令牌
   - 例如：`Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

2. **错误处理**
   - 所有接口在遇到错误时会返回相应的HTTP状态码和详细错误信息
   - 常见错误码：
     - 400: 请求参数错误
     - 401: 未授权（未登录或令牌无效）
     - 403: 权限不足
     - 404: 资源不存在
     - 500: 服务器内部错误

3. **速率限制**
   - 部分接口有速率限制，过于频繁的请求会被拒绝
   - 被限制时会返回429状态码和Retry-After响应头

4. **缓存控制**
   - 部分公开接口（如获取帖子列表、帖子详情等）使用缓存加速响应
   - 缓存过期时间通常为1分钟到1小时不等，具体取决于接口性质

5. **权限要求**
   - 接口权限分为几种类型：
     - 公开接口：无需认证即可访问
     - 用户接口：需要有效的登录状态
     - 权限接口：需要特定的权限点(Permission)
     - 角色接口：需要特定的角色(Role)，如管理员
   - 对于权限不足的请求，系统会返回403错误

6. **版本控制**
   - API遵循版本控制，当前版本为v1
   - 所有API路径都以`/api/v1/`开头

7. **参数验证**
   - 请求参数会经过严格验证，不符合要求的参数将导致400错误
   - 验证规则包括：类型检查、范围检查、格式检查等

8. **响应格式**
   - 所有接口返回JSON格式的响应
   - 正常响应通常包含请求的数据结果
   - 错误响应通常包含`detail`字段，描述错误原因

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   PORT=5000
   MONGODB_URI=mongodb://localhost:27017/forum
   JWT_SECRET=your_jwt_secret
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## Database Seeding

To populate your database with mock data extracted from the frontend components, run:

```
npm run seed
```

This will seed the database with:
- 4 users with different roles
- 7 categories
- 15 tags
- 5 sample posts with content
- 6 comments
- Post-tag relationships

The seeding script checks for existing data to avoid duplicates, so you can run it multiple times safely.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token

### Users
- `GET /api/users` - Get all users (admin only)
- `GET /api/users/:id` - Get user by ID
- `GET /api/users/:id/posts` - Get posts by user ID
- `PUT /api/users/:id` - Update user (authenticated user only)
- `DELETE /api/users/:id` - Delete user (admin or self only)

### Posts
- `GET /api/posts` - Get all posts (with pagination)
- `GET /api/posts/featured` - Get featured posts
- `GET /api/posts/:id` - Get post by ID
- `POST /api/posts` - Create new post (authenticated)
- `PUT /api/posts/:id` - Update post (owner or admin only)
- `DELETE /api/posts/:id` - Delete post (owner or admin only)

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/:id` - Get category by ID
- `GET /api/categories/:id/posts` - Get posts by category ID
- `POST /api/categories` - Create new category (admin only)
- `PUT /api/categories/:id` - Update category (admin only)
- `DELETE /api/categories/:id` - Delete category (admin only)

### Tags
- `GET /api/tags` - Get all tags
- `GET /api/tags/:id` - Get tag by ID
- `GET /api/tags/:id/posts` - Get posts by tag ID
- `POST /api/tags` - Create new tag (authenticated)
- `PUT /api/tags/:id` - Update tag (admin only)
- `DELETE /api/tags/:id` - Delete tag (admin only)

### Comments
- `GET /api/posts/:postId/comments` - Get comments for a post
- `POST /api/posts/:postId/comments` - Add comment to post (authenticated)
- `PUT /api/comments/:id` - Update comment (owner or admin only)
- `DELETE /api/comments/:id` - Delete comment (owner or admin only)

## 数据导入

本项目包含导入前端模拟数据的功能，可以通过以下方式使用：

### 通过命令行导入

```bash
# 在backend目录下执行
python -m app.scripts.seed_forum_data

# 若要清除现有数据再导入
python -m app.scripts.seed_forum_data --clear
```

### 通过API导入

系统提供了API端点用于导入数据（仅限管理员使用）：

```
POST /api/v1/seed/seed-forum-data
    参数：clear_existing (boolean) - 是否清除现有数据

GET /api/v1/seed/clear-forum-data
    清除所有论坛数据
```

### 导入数据内容

导入的数据包括：

1. **用户**：管理员、技术分享者、设计师、后端开发者等角色
2. **分类**：技术讨论、产品设计、职业发展、项目分享等
3. **标签**：Python、JavaScript、Vue.js、React、FastAPI等
4. **帖子**：关于技术、设计、职业发展的示例帖子
5. **评论**：与帖子相关的用户讨论

## API速率限制功能

论坛系统实现了多层次的API速率限制功能，以防止API滥用并确保系统稳定性。开发者可以根据不同场景选择适合的限流方法。所有限流实现都基于Redis，支持分布式部署场景。

### 限流方法概述

系统提供三种限流实现方式：

1. **全局中间件限流** - 应用于所有API请求
2. **端点装饰器限流** - 针对特定API端点的精细控制
3. **依赖函数限流** - 可在路由处理函数内动态应用

### 1. 全局中间件限流

适用于为所有API请求提供基础保护的场景。

#### 配置方法

在 `main.py` 中启用中间件：

```python
from app.middlewares import RateLimitMiddleware

# 在应用启动时添加中间件
app.add_middleware(RateLimitMiddleware)
```

中间件配置在 `core/config.py` 中：

```python
# 限流配置
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS = 60  # 默认每个IP每分钟60个请求
RATE_LIMIT_WINDOW = 60  # 时间窗口（秒）
```

#### 特点

- 全局生效，无需修改各个端点
- 支持在配置中快速调整限流参数
- 提供IP级别的默认保护
- 可配置豁免特定路径（如文档、健康检查等）

### 2. 端点装饰器限流

适用于需要对特定API端点进行精细控制的场景，尤其是敏感或资源密集型操作。

#### 使用方法

直接在路由函数上应用装饰器：

```python
from fastapi import APIRouter, Request
from app.core.decorators import endpoint_rate_limit

router = APIRouter()

@router.post("/sensitive-operation")
@endpoint_rate_limit(limit=10, window=60)  # 每分钟最多10次请求
async def sensitive_endpoint(request: Request):
    """需要特殊限流的敏感操作"""
    return {"message": "操作成功"}
```

#### 特点

- 针对特定端点定制限流规则
- 可基于用户ID或IP进行限流
- 支持自定义键生成函数，实现复杂限流逻辑
- 自动记录限流触发的详细日志

### 3. 依赖函数限流

适用于需要在请求处理过程中动态决定限流策略的场景。

#### 使用方法

在路由函数中注入依赖项：

```python
from fastapi import APIRouter, Depends, Request
from app.dependencies import rate_limit

router = APIRouter()

@router.get("/dynamic-limited-endpoint/{resource_id}")
async def dynamic_endpoint(
    resource_id: int,
    request: Request,
    # 使用速率限制依赖，每30秒最多5个请求
    _: bool = Depends(rate_limit(limit=5, window=30))
):
    """使用依赖注入方式限流的端点"""
    return {"resource_id": resource_id}
```

对于仅基于IP的简化限流：

```python
@router.get("/ip-limited-endpoint")
async def ip_endpoint(
    request: Request,
    _: bool = Depends(ip_rate_limit(limit=20, window=60))
):
    """仅基于IP限流的端点"""
    return {"message": "Hello"}
```

#### 特点

- 可以根据请求参数动态调整限流规则
- 易于在现有端点上添加限流功能
- 可与其他依赖项组合使用
- 支持更细粒度的控制，如特定资源或操作的限流

### 限流触发响应

当请求超过限制时，API将返回：

- HTTP状态码：`429 Too Many Requests`
- 响应体：`{"detail": "请求太频繁，请稍后再试"}`

### 最佳实践

1. **分层限流策略**：
   - 使用全局中间件提供基础保护
   - 对敏感端点使用更严格的端点装饰器限流
   - 需要特殊逻辑的场景使用依赖函数限流

2. **合理设置限制**：
   - 读取操作可以设置较宽松的限制
   - 写入、删除等操作应设置较严格的限制
   - 账户操作（如登录、注册）需要特别严格的限制

3. **监控与调整**：
   - 定期检查限流日志，了解API使用模式
   - 根据实际使用情况调整限流参数
   - 对频繁触发限流的IP或用户进行分析

4. **用户体验考虑**：
   - 在前端实现退避算法，避免频繁重试
   - 向用户提供清晰的限流提示
   - 考虑为高级用户或特定场景提供更高的限制

### 实现细节

所有限流方法都使用 `core/cache.py` 中的 `RateLimiter` 类，确保统一的限流行为和性能。该实现基于Redis的计数器和过期时间机制，支持分布式环境下的准确限流。
