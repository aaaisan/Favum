from typing import List, Optional, Union
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class EmailTemplate:
    """邮件模板"""
    
    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def render(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        try:
            template = self.env.get_template(f"{template_name}.html")
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"渲染邮件模板失败: {str(e)}")
            raise

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_TLS=settings.MAIL_TLS,
            MAIL_SSL=settings.MAIL_SSL,
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
        )
        self.fast_mail = FastMail(self.config)
        self.template = EmailTemplate()
    
    async def send_email(
        self,
        subject: str,
        recipients: Union[List[EmailStr], EmailStr],
        body: str,
        template_name: Optional[str] = None,
        template_data: Optional[dict] = None,
        cc: Optional[List[EmailStr]] = None,
        bcc: Optional[List[EmailStr]] = None,
        attachments: Optional[List[Path]] = None,
    ) -> bool:
        """发送邮件"""
        try:
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # 如果提供了模板，使用模板渲染
            if template_name and template_data:
                body = self.template.render(template_name, **template_data)
            
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=body,
                cc=cc,
                bcc=bcc,
                subtype="html"
            )
            
            await self.fast_mail.send_message(message, template_name=template_name)
            
            logger.info(
                "邮件发送成功",
                extra={
                    "subject": subject,
                    "recipients": recipients,
                    "template": template_name
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"邮件发送失败: {str(e)}",
                extra={
                    "subject": subject,
                    "recipients": recipients,
                    "template": template_name
                }
            )
            return False
    
    async def send_welcome_email(
        self,
        email: EmailStr,
        username: str
    ) -> bool:
        """发送欢迎邮件"""
        return await self.send_email(
            subject="欢迎加入我们的社区",
            recipients=email,
            template_name="welcome",
            template_data={"username": username}
        )
    
    async def send_reset_password_email(
        self,
        email: EmailStr,
        reset_token: str
    ) -> bool:
        """发送重置密码邮件"""
        return await self.send_email(
            subject="重置密码",
            recipients=email,
            template_name="reset_password",
            template_data={"reset_token": reset_token}
        )
    
    async def send_verification_email(
        self,
        email: EmailStr,
        verify_token: str
    ) -> bool:
        """发送验证邮件"""
        return await self.send_email(
            subject="验证您的邮箱",
            recipients=email,
            template_name="verify_email",
            template_data={"verify_token": verify_token}
        )

# 创建邮件发送器实例
email_sender = EmailSender() 