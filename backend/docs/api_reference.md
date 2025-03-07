# API 参考文档

## 核心模块 (core)

### 权限管理 (permissions.py)

#### 枚举类
```python
class Role(str, Enum):
    """角色枚举类
    
    定义系统中的用户角色层级：
    - SUPER_ADMIN: 超级管理员，拥有所有权限
    - ADMIN: 管理员，拥有大部分管理权限
    - MODERATOR: 版主，拥有内容管理权限
    - USER: 普通用户，基本操作权限
    - GUEST: 访客，只读权限
    """

class Permission(str, Enum):
    """权限枚举类
    
    定义系统中的具体权限：
    - 用户管理权限 (MANAGE_USERS, VIEW_USERS)
    - 角色管理权限 (MANAGE_ROLES, VIEW_ROLES)
    - 任务管理权限 (MANAGE_TASKS, VIEW_TASKS, EXECUTE_TASKS)
    - 系统管理权限 (MANAGE_SYSTEM, VIEW_SYSTEM)
    - 内容管理权限 (MANAGE_CONTENT, CREATE_CONTENT, EDIT_CONTENT等)
    """
```

### 缓存管理 (cache.py)

#### 类
```python
class RedisClient:
    """Redis客户端单例类
    
    确保整个应用使用同一个Redis连接实例
    """
    
    @classmethod
    def get_instance(cls) -> redis.Redis:
        """获取Redis客户端实例
        
        如果实例不存在则创建新实例，否则返回现有实例
        """

class CacheManager:
    """缓存管理器类
    
    提供高级缓存操作接口，包括：
    - 序列化和反序列化
    - 设置和获取缓存
    - 删除和清理缓存
    - 批量操作
    - 健康检查
    """
    
    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 要缓存的值
            expire: 过期时间（秒或timedelta对象）
        
        Returns:
            bool: 操作是否成功
        """
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存的值，不存在则返回None
        """
```

### 装饰器 (decorators.py)

#### 函数装饰器
```python
def handle_exceptions(*exceptions: Type[Exception], status_code: int = 500, message: str = "服务器内部错误"):
    """异常处理装饰器
    
    统一处理API端点的异常，转换为HTTP响应
    
    Args:
        exceptions: 要捕获的异常类型
        status_code: HTTP状态码
        message: 错误消息
    """

def rate_limit(limit: int, window: int = 60, key: Optional[str] = None):
    """速率限制装饰器
    
    限制API端点的访问频率
    
    Args:
        limit: 时间窗口内允许的最大请求次数
        window: 时间窗口大小（秒）
        key: 自定义限流键前缀
    """

def cache(expire: int = 300, key_prefix: str = "cache", skip_cache: bool = False):
    """缓存装饰器
    
    缓存API端点的响应结果
    
    Args:
        expire: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        skip_cache: 是否跳过缓存
    """
```

## 数据访问层 (crud)

### 基础CRUD (base.py)
```python
class CRUDBase[T, CreateSchema, UpdateSchema]:
    """通用CRUD操作基类
    
    为模型提供基础的创建、读取、更新、删除操作
    
    Type Parameters:
        T: 数据库模型类型
        CreateSchema: 创建模型的Pydantic架构
        UpdateSchema: 更新模型的Pydantic架构
    """
    
    def create(self, db: Session, *, obj_in: CreateSchema) -> T:
        """创建新记录
        
        Args:
            db: 数据库会话
            obj_in: 创建模型数据
            
        Returns:
            T: 创建的模型实例
        """
```

## 服务层 (services)

### 任务服务 (task_service.py)
```python
class TaskService:
    """任务服务类
    
    处理任务相关的业务逻辑，包括：
    - 任务的创建和调度
    - 任务状态管理
    - 任务执行结果处理
    """
    
    async def create_task(self, task_data: dict) -> Task:
        """创建新任务
        
        Args:
            task_data: 任务配置数据
            
        Returns:
            Task: 创建的任务实例
        """
```

## API端点 (endpoints)

### 用户API (users.py)
```python
@router.post("/")
async def create_user(...):
    """创建新用户
    
    - 验证用户数据
    - 检查邮箱是否已注册
    - 创建用户记录
    - 发送欢迎邮件
    """

@router.get("/")
async def read_users(...):
    """获取用户列表
    
    - 支持分页
    - 可按角色筛选
    - 缓存结果
    """
```

### 帖子API (posts.py)
```python
@router.post("/")
async def create_post(...):
    """创建新帖子
    
    - 验证帖子内容
    - 检查用户权限
    - 创建帖子记录
    - 触发相关事件
    """

@router.get("/{post_id}")
async def read_post(...):
    """获取帖子详情
    
    - 检查帖子是否存在
    - 增加阅读计数
    - 返回帖子信息
    """
```

## 工具函数 (utils)

### 辅助函数 (helpers.py)
```python
def generate_password_hash(password: str) -> str:
    """生成密码哈希值
    
    使用bcrypt算法对密码进行加密
    
    Args:
        password: 原始密码
        
    Returns:
        str: 密码哈希值
    """

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    检查密码是否匹配其哈希值
    
    Args:
        plain_password: 原始密码
        hashed_password: 密码哈希值
        
    Returns:
        bool: 密码是否正确
    """
```

## 工具类 (utils)

### 任务管理器 (tasks.py)
```python
class TaskManager:
    """任务管理器类
    
    处理所有任务相关的操作，包括：
    - 任务状态查询和管理
    - 任务执行控制（取消、重试）
    - 任务列表和统计信息
    - 工作器状态监控
    """
    
    @staticmethod
    def get_task_status(task_id: str) -> dict:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 包含任务状态信息的字典
        """
    
    @staticmethod
    def get_task_info(task_id: str) -> Optional[dict]:
        """获取任务详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[dict]: 任务的详细信息，不存在则返回None
        """
```

## 异步任务 (tasks)

### 邮件任务 (email.py)
```python
@celery_app.task
def send_welcome_email(user_email: str, username: str):
    """发送欢迎邮件
    
    Args:
        user_email: 用户邮箱
        username: 用户名
    """

@celery_app.task
def send_password_reset_email(user_email: str, reset_token: str):
    """发送密码重置邮件
    
    Args:
        user_email: 用户邮箱
        reset_token: 重置令牌
    """
```

## 中间件 (middleware)

### 请求日志中间件
```python
class RequestLoggingMiddleware:
    """请求日志中间件
    
    记录所有HTTP请求的详细信息：
    - 请求方法和URL
    - 请求头和参数
    - 响应状态和时间
    - 错误信息
    """
```

## 事件处理 (events)

### 系统事件
```python
async def startup_event():
    """应用启动事件处理
    
    - 初始化数据库连接
    - 建立Redis连接
    - 启动后台任务
    """

async def shutdown_event():
    """应用关闭事件处理
    
    - 关闭数据库连接
    - 清理Redis连接
    - 停止后台任务
    """
``` 