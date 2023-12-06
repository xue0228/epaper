import hashlib
import io
import os
from math import floor
from typing import Union

from PIL import Image, ImageDraw, ImageFont

from constants import ROOT_DIR


def get_hash(file: Union[bytes, Image.Image]) -> str:
    if isinstance(file, Image.Image):
        data = io.BytesIO()
        file.save(data, format="PNG")
        file = data.getvalue()
    return hashlib.md5(file).hexdigest()


def resize_img(file, size, fill=(0xFF, 0xFF, 0xFF)):
    img = Image.new("RGB", size, fill)
    data = Image.open(file)
    if data.size[0] / data.size[1] < size[0] / size[1]:
        target_height = size[1]
        target_width = round(target_height / data.size[1] * data.size[0])
    else:
        target_width = size[0]
        target_height = round(target_width / data.size[0] * data.size[1])
    data = data.resize((target_width, target_height))
    x = round((size[0] - target_width) / 2)
    y = round((size[1] - target_height) / 2)
    img.paste(data, (x, y))
    return img


def get_text_width(text: str) -> float:
    letter = "abcdefghijklmnopqrstuvwxyz"
    number = "0123456789"
    symbol = "~!@#$%^&*()_+`-=[]\;',./{}|:\"<>?"
    others = " "
    letter_width = 3 / 7
    number_width = 3 / 7
    symbol_width = 3 / 7
    others_width = 0.5

    width = 0
    for item in text.lower():
        if item in letter:
            width += letter_width
        elif item in number:
            width += number_width
        elif item in symbol:
            width += symbol_width
        elif item in others:
            width += others_width
        else:
            width += 1
    return width


def draw_text(text: str, img: Image.Image, font: str = None):
    if font is None:
        font = os.path.join(ROOT_DIR, "HanZiZhiMeiFangSongGBK.ttf")

    padding = 0.5
    border = 0.2
    border_size = min([border * item for item in img.size])
    lines = text.split("\n")
    width = max([get_text_width(item) for item in lines])
    height = len(lines) + (len(lines) - 1) * padding
    font_size = floor(min([(img.width - border_size) / width, (img.height - border_size) / height]))
    max_width = width * font_size
    max_height = height * font_size
    x = int((img.width - max_width) / 2)
    y = int((img.height - max_height) / 2)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font, font_size)
    for i in range(len(lines)):
        draw.text((x, int(y + i * (1 + padding) * font_size)), lines[i], (0, 0, 0), font)
    return img


def mask_img(img: Image.Image, alpha: float = 0.5):
    img = img.convert("RGBA")
    mask = Image.new("RGBA", img.size, (255, 255, 255, int(255 * alpha)))
    img.paste(mask, (0, 0), mask)
    img = img.convert("RGB")
    return img
