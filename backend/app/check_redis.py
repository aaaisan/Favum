from app.core.redis import redis_client

print("正在检查Redis连接...")
try:
    # 尝试设置一个测试键值
    redis_client.set("test_key", "test_value")
    # 读取测试键值
    value = redis_client.get("test_key")
    # 删除测试键值
    redis_client.delete("test_key")
    
    if value == "test_value":
        print("✅ Redis连接正常！")
    else:
        print("❌ Redis连接异常：存取值不匹配")
except Exception as e:
    print(f"❌ Redis连接失败: {str(e)}") 