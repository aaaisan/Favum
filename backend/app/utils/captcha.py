import random
import string
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from fastapi import HTTPException, status
from ..core.redis import redis_client
from typing import List, Tuple, Union

# 定义三种字体路径
FONT_PATHS = [
    "backend/app/static/fonts/Arial.ttf",
    "backend/app/static/fonts/Verdana.ttf",
    "backend/app/static/fonts/Georgia.ttf"
]

class CaptchaGenerator:
    """验证码生成器"""
    
    def __init__(
        self,
        width: int = 160,
        height: int = 60,
        length: int = 6,
        font_path: str = "backend/app/static/fonts/Arial.ttf",
        font_size: int = 36
    ):
        """初始化验证码生成器
        
        Args:
            width: 图片宽度
            height: 图片高度
            length: 验证码长度
            font_path: 字体文件路径
            font_size: 字体大小
        """
        self.width = width
        self.height = height
        self.length = length
        self.font_path = font_path
        self.font_size = font_size
        
        # 定义多种字体路径
        self.font_paths = [
            "backend/app/static/fonts/Arial.ttf",
            "backend/app/static/fonts/Verdana.ttf",
            "backend/app/static/fonts/Georgia.ttf"
        ]
        # 如果提供的字体不在列表中，添加进去
        if font_path not in self.font_paths:
            self.font_paths.append(font_path)
    
    def _generate_background(self):
        """生成背景"""
        # 创建空白图片，背景为白色
        return Image.new('RGB', (self.width, self.height), (255, 255, 255))
    
    def _generate_text(self):
        """生成随机验证码文本，排除容易混淆的字符"""
        # 排除容易混淆的字符：0,O,1,l,I,9,g,q,2,Z
        characters = '3456578ABCDEFGHJKLMNPQRSTUVWXY'
        return ''.join(random.choice(characters) for _ in range(self.length))
    
    def _add_noise(self, draw):
        """添加干扰"""
        # 添加干扰点
        for _ in range(random.randint(150, 250)):  # 增加干扰点数量
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=self._random_color(64, 255))
        
        # 添加干扰线
        for _ in range(random.randint(4, 6)):  # 增加干扰线数量
            start = (random.randint(0, self.width), random.randint(0, self.height))
            end = (random.randint(0, self.width), random.randint(0, self.height))
            draw.line([start, end], fill=self._random_color(64, 255), width=2)
    
    def _random_color(self, min_val=0, max_val=255):
        """生成随机颜色，确保颜色足够鲜艳"""
        # 生成RGB三个通道的值，确保至少有一个通道的值较高以产生鲜艳的颜色
        r = random.randint(min_val, max_val)
        g = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        
        # 确保至少有一个通道的值大于200，使颜色更鲜艳
        max_channel = max(r, g, b)
        if max_channel < 200:
            if r == max_channel:
                r = random.randint(200, 255)
            elif g == max_channel:
                g = random.randint(200, 255)
            else:
                b = random.randint(200, 255)
        
        return (r, g, b)

    def generate(self):
        """生成验证码图片
        
        Returns:
            tuple: (验证码文本, 图片二进制数据)
        """
        # 生成随机文本
        text = self._generate_text()
        
        # 创建图片对象
        image = self._generate_background()
        draw = ImageDraw.Draw(image)
        
        # 尝试加载多种字体
        fonts = []
        for path in self.font_paths:
            try:
                font = ImageFont.truetype(path, self.font_size)
                fonts.append(font)
            except Exception:
                continue
        
        # 如果以上字体都无法加载，尝试加载构造函数中指定的字体
        if not fonts:
            try:
                font = ImageFont.truetype(self.font_path, self.font_size)
                fonts = [font]
            except Exception:
                fonts = [ImageFont.load_default()]
        
        # 计算文本宽度
        try:
            text_width = fonts[0].getlength(text)
        except AttributeError:
            # 兼容旧版PIL
            text_width = sum(fonts[0].getsize(char)[0] for char in text)
        
        text_height = self.font_size
        
        # 计算文本位置（居中）
        x = (self.width - text_width) / 2
        y = (self.height - text_height) / 2
        
        # 为每个字符生成不同的颜色
        colors = [self._random_color() for _ in text]
        
        # 绘制文本
        for i, (char, color) in enumerate(zip(text, colors)):
            # 对每个字符应用微小的随机偏移
            char_x = x + i * (text_width / len(text))
            char_y = y + random.uniform(-5, 5)
            
            # 随机选择一个字体
            font = random.choice(fonts)
            
            draw.text(
                (char_x, char_y),
                char,
                font=font,
                fill=color
            )
        
        # 添加干扰
        self._add_noise(draw)
        
        # 转换为二进制数据
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        return text, image_bytes

class CaptchaValidator:
    """验证码验证器
    
    提供验证码验证功能，可作为依赖项使用。
    此类已被弃用，请使用CaptchaService中的方法代替。
    """
    
    def __init__(self):
        """初始化验证码验证器"""
        from ..services.captcha_service import CaptchaService
        self.captcha_service = CaptchaService()
    
    @staticmethod
    def validate_and_delete(captcha_id: str, captcha_code: str) -> None:
        """验证验证码并删除
        
        此方法仍保留用于向后兼容，但推荐直接使用CaptchaService中的方法。
        
        Args:
            captcha_id: 验证码ID
            captcha_code: 用户输入的验证码
            
        Raises:
            HTTPException: 当验证码无效或过期时抛出
        """
        from ..services.captcha_service import CaptchaService
        service = CaptchaService()
        service.validate_and_delete(captcha_id, captcha_code)
    
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