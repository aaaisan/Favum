import os
import sys
import subprocess
from datetime import datetime
import gzip
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def create_backup():
    # 创建备份目录
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"forum_db_backup_{timestamp}.sql")
    compressed_file = f"{backup_file}.gz"
    
    try:
        # 使用 mysqldump 创建备份
        cmd = [
            "mysqldump",
            f"--host={settings.MYSQL_HOST}",
            f"--port={settings.MYSQL_PORT}",
            f"--user={settings.MYSQL_USER}",
            f"--password={settings.MYSQL_PASSWORD}",
            "--single-transaction",  # 保证数据一致性
            "--routines",           # 包含存储过程和函数
            "--triggers",           # 包含触发器
            "--events",             # 包含事件
            settings.MYSQL_DATABASE
        ]
        
        with open(backup_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)
        
        # 压缩备份文件
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除未压缩的文件
        os.remove(backup_file)
        
        print(f"数据库备份成功: {compressed_file}")
        return compressed_file
        
    except subprocess.CalledProcessError as e:
        print(f"备份失败: {e}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def restore_backup(backup_file):
    if not os.path.exists(backup_file):
        print(f"备份文件不存在: {backup_file}")
        return False
    
    try:
        # 如果是压缩文件，先解压
        if backup_file.endswith('.gz'):
            uncompressed_file = backup_file[:-3]
            with gzip.open(backup_file, 'rb') as f_in:
                with open(uncompressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = uncompressed_file
        
        # 使用 mysql 命令恢复数据
        cmd = [
            "mysql",
            f"--host={settings.MYSQL_HOST}",
            f"--port={settings.MYSQL_PORT}",
            f"--user={settings.MYSQL_USER}",
            f"--password={settings.MYSQL_PASSWORD}",
            settings.MYSQL_DATABASE
        ]
        
        with open(backup_file, "r") as f:
            subprocess.run(cmd, stdin=f, check=True)
        
        # 如果之前解压了文件，删除解压的文件
        if backup_file.endswith('.sql'):
            os.remove(backup_file)
            
        print("数据库恢复成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"恢复失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) != 3:
            print("使用方法: python backup_db.py restore <backup_file>")
            sys.exit(1)
        restore_backup(sys.argv[2])
    else:
        create_backup() 