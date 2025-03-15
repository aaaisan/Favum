# 帖子API端点测试工具

这个测试工具用于测试论坛系统中的帖子相关API端点。通过这个脚本，您可以验证所有与帖子相关的功能是否正常工作，包括创建、读取、更新、删除帖子，以及投票、收藏等功能。

## 功能

该测试工具会自动测试以下端点：

1. `POST /api/v1/posts` - 创建帖子
2. `GET /api/v1/posts` - 获取帖子列表
3. `GET /api/v1/posts/{post_id}` - 获取帖子详情
4. `PUT /api/v1/posts/{post_id}` - 更新帖子
5. `DELETE /api/v1/posts/{post_id}` - 删除帖子
6. `POST /api/v1/posts/{post_id}/restore` - 恢复被删除的帖子
7. `PATCH /api/v1/posts/{post_id}/visibility` - 切换帖子可见性
8. `POST /api/v1/posts/{post_id}/vote` - 为帖子投票
9. `GET /api/v1/posts/{post_id}/votes` - 获取帖子投票统计
10. `POST /api/v1/posts/{post_id}/favorite` - 收藏帖子
11. `DELETE /api/v1/posts/{post_id}/favorite` - 取消收藏帖子
12. `GET /api/v1/posts/{post_id}/favorite/status` - 检查收藏状态
13. `GET /api/v1/posts/{post_id}/comments` - 获取帖子评论

## 使用方法

### 准备工作

1. 确保Python 3.6+已安装
2. 安装依赖: `pip install requests`
3. 确保后端API服务已启动并运行在预设地址（默认为`http://localhost:8000`）

### 自动认证 (新功能)

测试工具现在支持自动认证，可以自动获取访问令牌，而无需手动输入。默认情况下，工具会使用以下凭据：

- 用户名：`admin`
- 密码：`admin123`

您可以通过以下方式控制自动认证：

1. 使用环境变量：`AUTO_AUTH=0` 禁用自动认证
2. 使用命令行参数：`--no-auto-auth` 禁用自动认证
3. 自定义凭据：`--username "your_user" --password "your_pass"`

### 运行测试

**方法1：使用Bash脚本（推荐）**

最简单的方法是使用提供的Bash脚本，它会自动处理认证和测试流程：

```bash
./run_posts_tests.sh
```

脚本参数：
```
选项:
  -h, --help             显示帮助信息
  -t, --token TOKEN      设置用户访问令牌
  -a, --admin TOKEN      设置管理员访问令牌
  --host HOST            设置API主机地址 (默认: localhost:8000)
  --normal-only          只运行标准功能测试
  --edge-only            只运行边缘情况测试
  --no-auto-auth         禁用自动认证 (默认启用)
  --username USERNAME    设置登录用户名 (默认: admin)
  --password PASSWORD    设置登录密码 (默认: admin123)
```

**方法2：直接运行Python脚本**

您也可以直接运行Python测试脚本：

```bash
python test_posts_endpoints.py
```

此方式同样支持自动认证，如果没有提供令牌，脚本会尝试使用默认凭据获取访问令牌。

**方法3：通过命令行参数提供令牌**

如果您已有令牌，可以直接提供：

```bash
python test_posts_endpoints.py "YOUR_ACCESS_TOKEN" ["ADMIN_TOKEN"]
```

- 第一个参数是普通用户的访问令牌
- 第二个参数是管理员用户的访问令牌（可选）

**方法4：在脚本中直接设置令牌**

您也可以直接编辑脚本，在脚本开始部分设置TOKEN和ADMIN_TOKEN变量：

```python
# 配置
TOKEN = "your_access_token_here"  # 请设置有效的认证令牌
ADMIN_TOKEN = "admin_token_here"  # 管理员令牌 (如需测试管理员功能)
# 禁用自动认证
AUTO_AUTH = False
```

### 配置选项

您可以根据需要修改脚本中的以下配置：

- `API_HOST`: API主机地址，默认为`localhost:8000`
- `TOKEN`: 普通用户认证令牌
- `ADMIN_TOKEN`: 管理员用户认证令牌
- `AUTO_AUTH`: 是否启用自动认证，默认为`True`
- `USERNAME`: 自动认证使用的用户名，默认为`admin`
- `PASSWORD`: 自动认证使用的密码，默认为`admin123`

## 输出说明

测试结果将使用彩色输出显示：

- 绿色: 成功的请求（2xx状态码）
- 黄色: 警告或可能的问题（非2xx状态码）
- 红色: 错误或失败的请求
- 蓝色: 信息性消息

对于每个端点测试，脚本会显示：
1. 请求的URL和方法
2. 响应状态码
3. 响应内容（JSON格式，如果可用）

## 故障排除

1. **认证错误（401）**
   - 检查提供的用户名和密码是否正确
   - 如果使用令牌，确保令牌有效且未过期
   - 检查令牌格式是否正确（Bearer token）

2. **连接错误**
   - 确保API服务正在运行
   - 检查API_HOST配置是否正确

3. **权限错误（403）**
   - 某些端点可能需要特定权限或角色
   - 对于管理员专用端点，确保使用管理员令牌

4. **自动认证失败**
   - 检查认证端点是否为 `/api/v1/auth/login`
   - 打印API响应以检查错误消息
   - 手动尝试登录以验证凭据

## 高级用法

### 测试特定端点

您可以修改脚本中的`run_all_tests`函数，注释掉不需要测试的端点，或者创建自定义测试函数只测试特定端点。

### 添加更多断言和验证

当前脚本主要关注API调用是否成功，您可以添加更多断言来验证响应内容是否符合预期，例如：

```python
response = test_endpoint("GET", f"/{test_post_id}")
assert response.json()["title"] == expected_title, "帖子标题不符合预期"
```

### 自动化集成

该脚本可以集成到CI/CD流程中，通过检查退出码来确定测试是否通过。您可以修改脚本，在测试失败时返回非零退出码。 