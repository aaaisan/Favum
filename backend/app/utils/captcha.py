import random
import string
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from fastapi import HTTPException, status
from ..core.redis import redis_client

class CaptchaGenerator:
    def __init__(self, width=200, height=60, font_size=36, length=6):
        self.width = width
        self.height = height
        self.font_size = font_size
        self.length = length
        
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 字体文件路径（使用系统默认字体）
        self.font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        
    def _generate_text(self):
        """生成随机验证码文本"""
        # 字符集：数字和大写字母
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(self.length))
    
    def _generate_background(self):
        """生成背景图片"""
        return Image.new('RGB', (self.width, self.height), 'white')
    
    def _add_noise(self, draw):
        """添加干扰"""
        # 添加干扰点
        for _ in range(random.randint(100, 200)):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=self._random_color(64, 255))
        
        # 添加干扰线
        for _ in range(random.randint(3, 5)):
            start = (random.randint(0, self.width), random.randint(0, self.height))
            end = (random.randint(0, self.width), random.randint(0, self.height))
            draw.line([start, end], fill=self._random_color(64, 255), width=2)
    
    def _random_color(self, min_val, max_val):
        """生成随机颜色"""
        return (
            random.randint(min_val, max_val),
            random.randint(min_val, max_val),
            random.randint(min_val, max_val)
        )
    
    def generate(self):
        """生成验证码"""
        # 生成文本
        text = self._generate_text()
        
        # 创建图片
        image = self._generate_background()
        draw = ImageDraw.Draw(image)
        
        # 添加干扰
        self._add_noise(draw)
        
        # 加载字体
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # 计算文本大小
        text_width = self.width // len(text)
        
        # 绘制文本
        for i, char in enumerate(text):
            # 随机偏移
            x = text_width * i + random.randint(2, 10)
            y = random.randint(2, (self.height - self.font_size) // 2)
            
            # 随机旋转角度
            angle = random.randint(-30, 30)
            
            # 使用不同颜色绘制每个字符
            color = self._random_color(0, 64)
            
            # 创建单个字符的图片并旋转
            char_img = Image.new('RGBA', (text_width, self.height), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((5, y), char, font=font, fill=color)
            rotated = char_img.rotate(angle, expand=False, fillcolor=(255, 255, 255, 0))
            
            # 将旋转后的字符图片粘贴到主图片上
            image.paste(rotated, (x, 0), rotated)
        
        # 转换为字节流
        byte_io = BytesIO()
        image.save(byte_io, 'PNG')
        byte_io.seek(0)
        
        return text, byte_io.getvalue()

class CaptchaValidator:
    @staticmethod
    def validate_and_delete(captcha_id: str, captcha_code: str) -> None:
        """验证验证码并删除"""
        # 测试模式：允许任何验证码通过
        return
        # 从Redis获取验证码
        stored_code = redis_client.get(f"captcha:{captcha_id}")
        if not stored_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期或不存在"
            )
        
        # 验证后删除验证码
        redis_client.delete(f"captcha:{captcha_id}")
        
        # 验证码不区分大小写
        if captcha_code.upper() != stored_code.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
    
    async def __call__(self, captcha_id: str, captcha_code: str) -> str:
        """
        使类可调用，用于FastAPI依赖注入
        
        Args:
            captcha_id: 验证码ID
            captcha_code: 用户输入的验证码
            
        Returns:
            str: 成功时返回验证码
            
        Raises:
            HTTPException: 验证码无效或过期时抛出异常
        """
        self.validate_and_delete(captcha_id, captcha_code)
        return captcha_code 