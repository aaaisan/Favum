import asyncio
import argparse
import sys
from scripts.seed_data import seed_database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="论坛数据库种子脚本")
    parser.add_argument("--clear", action="store_true", help="清除所有现有数据")
    
    args = parser.parse_args()
    
    print("开始导入数据...")
    if args.clear:
        print("将清除所有现有数据")
        response = input("确定要清除所有数据吗？这个操作不可逆！(y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("操作已取消")
            sys.exit(0)
    
    # 运行异步函数
    asyncio.run(seed_database(clear_existing=args.clear))
    
    print("数据导入完成！") 