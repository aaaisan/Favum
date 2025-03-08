import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base
from app.db.database import engine
from app.core.config import settings
from app.db.models import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

def init_db():
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建管理员用户
    db = Session(engine)
    try:
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                username=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                role=UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
            print("管理员用户创建成功")
        else:
            print("管理员用户已存在")
    finally:
        db.close()

if __name__ == "__main__":
    print(f"正在连接数据库: {settings.DATABASE_URL}")
    init_db()
    print("数据库初始化完成") 