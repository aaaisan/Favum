import os
import sys
import argparse
from alembic import command
from alembic.config import Config

def get_alembic_config():
    """获取 Alembic 配置"""
    alembic_cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    return alembic_cfg

def create_migration(message):
    """创建新的迁移"""
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, autogenerate=True, message=message)
    print(f"已创建新的迁移文件，消息：{message}")

def upgrade_database(revision="head"):
    """升级数据库到指定版本"""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, revision)
    print(f"数据库已升级到版本：{revision}")

def downgrade_database(revision="-1"):
    """降级数据库到指定版本"""
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)
    print(f"数据库已降级到版本：{revision}")

def show_history():
    """显示迁移历史"""
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)

def show_current():
    """显示当前版本"""
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据库迁移管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建迁移
    create_parser = subparsers.add_parser("create", help="创建新的迁移")
    create_parser.add_argument("message", help="迁移说明")

    # 升级数据库
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument("--revision", default="head", help="目标版本 (默认: head)")

    # 降级数据库
    downgrade_parser = subparsers.add_parser("downgrade", help="降级数据库")
    downgrade_parser.add_argument("--revision", default="-1", help="目标版本 (默认: -1)")

    # 显示历史
    subparsers.add_parser("history", help="显示迁移历史")

    # 显示当前版本
    subparsers.add_parser("current", help="显示当前版本")

    args = parser.parse_args()

    if args.command == "create":
        create_migration(args.message)
    elif args.command == "upgrade":
        upgrade_database(args.revision)
    elif args.command == "downgrade":
        downgrade_database(args.revision)
    elif args.command == "history":
        show_history()
    elif args.command == "current":
        show_current()
    else:
        parser.print_help() 