from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class Login(BaseModel):
    username: str
    password: str
    captcha_id: str  # 验证码ID，必填
    captcha_code: str  # 验证码，必填

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    captcha_id: str
    captcha_code: str 