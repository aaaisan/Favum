from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig # type: ignore
from pydantic import EmailStr
import datetime
from ..core.celery_config import celery_app
from ..core.config import settings

# 邮件配置
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=True,
)

fastmail = FastMail(email_conf)

# 网站URL
SITE_URL = settings.SITE_URL or "http://localhost:8080"

@celery_app.task(
    name="send_email",
    queue="email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
async def send_email(
    subject: str,
    recipients: List[EmailStr],
    body: str = "",
    template_name: Optional[str] = None,
    template_data: Optional[dict] = None,
) -> None:
    """发送邮件"""
    # 确保template_data包含当前年份
    if template_data is None:
        template_data = {}
    
    # 添加当前年份
    if "current_year" not in template_data:
        template_data["current_year"] = datetime.datetime.now().year
    
    # 添加网站URL
    if "site_url" not in template_data:
        template_data["site_url"] = SITE_URL
    
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        template_body=template_data,
    )
    
    if template_name:
        await fastmail.send_message(message, template_name=template_name)
    else:
        await fastmail.send_message(message)

@celery_app.task(
    name="send_welcome_email",
    queue="email",
)
async def send_welcome_email(user_email: EmailStr, username: str) -> None:
    """发送欢迎邮件"""
    await send_email.delay(
        subject="欢迎加入论坛",
        recipients=[user_email],
        template_name="welcome.html",
        template_data={
            "username": username,
            "site_url": SITE_URL,
        }
    )

@celery_app.task(
    name="send_reset_password_email",
    queue="email",
)
async def send_reset_password_email(
    user_email: EmailStr,
    username: str,
    reset_token: str
) -> None:
    """发送重置密码邮件"""
    await send_email.delay(
        subject="重置密码",
        recipients=[user_email],
        template_name="reset_password.html",
        template_data={
            "username": username,
            "reset_token": reset_token,
            "reset_url": f"{SITE_URL}/reset-password",
        }
    )

@celery_app.task(
    name="send_verification_email",
    queue="email",
)
async def send_verification_email(
    user_email: EmailStr,
    username: str,
    verify_token: str
) -> None:
    """发送邮箱验证邮件"""
    await send_email.delay(
        subject="验证您的邮箱",
        recipients=[user_email],
        template_name="verify_email.html",
        template_data={
            "username": username,
            "verify_token": verify_token,
            "verify_url": f"{SITE_URL}/verify-email",
        }
    ) 