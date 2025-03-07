from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig # type: ignore
from pydantic import EmailStr
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
    body: str,
    template_name: Optional[str] = None,
    template_data: Optional[dict] = None,
) -> None:
    """发送邮件"""
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
        }
    ) 