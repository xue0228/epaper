import glob
import io
import math
import os.path
import time
from abc import ABCMeta, abstractmethod
from threading import RLock
from typing import Optional, Tuple

import cv2
from PIL import Image, ImageDraw
from PIL.ImageOps import invert

from config import Config
from constants import WIDTH, HEIGHT, DATA_DIR, ALBUM_DIR, CLEAR_BEFORE_UPDATE
from display import Display
from log import logger
from observer import Observer
from utils import get_hash, draw_text, resize_img, mask_img


class BaseMode(Observer, metaclass=ABCMeta):
    """
    不同模式的基类
    """

    def __init__(self):
        # 记录与本模式相关的配置参数
        self.config = {}
        # 存储当前模式的线程锁
        self.lock = RLock()
        # 记录当前所处模式
        self._current_mode = ""
        # 存储控制墨水屏刷新的实例
        self._display: Optional[Display] = None
        # 记录是否首次运行
        self._once = True
        # 记录上次刷新屏幕的时间戳
        self._last_time = 0
        # 记录显示图像的 hash 值
        self._hash = ""

    @abstractmethod
    def get_image(self) -> Optional[Image.Image]:
        pass

    @abstractmethod
    def need_update(self) -> bool:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        模式名称
        :return:
        """
        pass

    @property
    def width(self) -> int:
        return WIDTH

    @property
    def height(self) -> int:
        return HEIGHT

    @property
    def size(self) -> Tuple[int, int]:
        return self.width, self.height

    def empty_image(self, color=None) -> Image.Image:
        """
        创建与屏幕尺寸相同的纯色图像
        :param color:
        :return:
        """
        if color is None:
            color = (0xff, 0xff, 0xff)
        return Image.new("RGB", self.size, color)

    def _update_display(self, compare_hash: bool):
        """
        刷新屏幕
        :return:
        """
        image = self.get_image()
        if image is None:
            self._display.clear()
            logger.debug(f"{self.name}：显示图像为 None，直接清屏")
            return
        data = io.BytesIO()
        image.save(data, format="PNG")
        img_hash = get_hash(data.getvalue())
        if not compare_hash:
            self._hash = img_hash
            if CLEAR_BEFORE_UPDATE:
                self._display.clear()
            self._display.update(data)
            logger.debug(f"{self.name}：无需比较 hash 值，屏幕已刷新")
            return
        else:
            logger.debug(f"{self.name}：需要比较 hash 值")
        if self._hash != img_hash:
            self._hash = img_hash
            if CLEAR_BEFORE_UPDATE:
                self._display.clear()
            self._display.update(data)
            logger.debug(f"{self.name}：hash 值不同，屏幕已刷新")
        else:
            logger.debug(f"{self.name}：hash 值相同，跳过刷新")

    def set_display(self, display: Display):
        """
        设置控制屏幕刷新的实例
        :param display:
        :return:
        """
        self._display = display

    def is_enough_interval(self, interval: float) -> bool:
        """
        一般用于 self.update_image 中，用于判断距离上次刷新是否满足指定时间间隔
        :param interval:
        :return:
        """
        now = time.time()
        if now - self._last_time >= interval:
            self._last_time = now
            return True
        return False

    def once_init(self, config: Config):
        self.config = config.dict.get(self.name, {})
        self._last_time = time.time()

    def after_update(self, config: Config):
        pass

    def update(self, notice: Config):
        """
        每次接收到配置参数时都会进行的更新函数
        :param notice:
        :return:
        """
        mode = notice.dict["base"]["mode"]
        logger.debug(f"{self.name}：当前模式为{mode}")

        if self._once:
            logger.debug(f"{self.name}：首次运行，初始化参数")
            self._once = False
            self.once_init(notice)

        if mode != self.name:
            self._current_mode = mode
            logger.debug(f"{self.name}：与本模式无关，跳过")
            return

        self.config = notice.dict.get(self.name, {})
        logger.debug(f"{self.name}：模块配置已更新")

        if self._current_mode != mode:
            self._current_mode = mode
            self._last_time = time.time()
            self._update_display(False)
            logger.debug(f"{self.name}：切换到本模式，刷新成功")
            return

        if self.need_update():
            logger.debug(f"{self.name}：需要更新显示图像")
            self._update_display(True)
            self.after_update(notice)
            logger.debug(f"{self.name}：更新图像后相关配置修改成功")
        else:
            logger.debug(f"{self.name}：无需更新显示图像")


class OffMode(BaseMode):
    name = "off"

    def need_update(self) -> bool:
        return False

    def get_image(self) -> Optional[Image.Image]:
        return None


class FixedMode(BaseMode):
    name = "fixed"

    def __init__(self):
        super().__init__()
        self._image_path = os.path.join(DATA_DIR, f"{self.name}.png")
        self._need_update = False

    def need_update(self) -> bool:
        if self._need_update:
            self._need_update = False
            return True
        if self.is_enough_interval(float(self.config.get("interval", "300"))):
            if not os.path.exists(self._image_path):
                return False
            else:
                return True
        return False

    def get_image(self) -> Optional[Image.Image]:
        if os.path.exists(self._image_path):
            img = Image.open(self._image_path)
        else:
            img = self.empty_image()
            img = draw_text("固定图像模式\n请上传图像", img)
        return img

    def api_func(self, file=None, text: str = "", alpha: float = 0.5):
        if file is None and text == "":
            return
        if file is not None:
            image = resize_img(file, self.size)
        else:
            if os.path.exists(self._image_path):
                image = Image.open(self._image_path)
            else:
                image = self.empty_image()
        if text != "":
            image = mask_img(image, alpha)
            image = draw_text(text, image)
        image.save(self._image_path)
        self._need_update = True


class MovieMode(BaseMode):
    name = "movie"

    def __init__(self):
        super().__init__()
        self._movie_path = os.path.join(DATA_DIR, "movie.mp4")
        self._image_path = os.path.join(DATA_DIR, f"{self.name}.png")

    def need_update(self) -> bool:
        return self.is_enough_interval(float(self.config.get("interval", "60")))

    def get_image(self) -> Optional[Image.Image]:
        if os.path.exists(self._movie_path):
            video = cv2.VideoCapture(self._movie_path)
            frame_index = int(self.config["index"])
            # frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            # if frame_index > frame_count:
            #     video.release()
            #     return False
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = video.read()
            if frame is not None:
                cv2.imwrite(self._image_path, frame)
                image = resize_img(self._image_path, self.size, (0x00, 0x00, 0x00))
            else:
                movie = self.empty_image()
                image = draw_text("慢放电影模式\n电影已结束", movie)
            video.release()
        else:
            movie = self.empty_image()
            image = draw_text("慢放电影模式\n电影不存在", movie)
        return image

    def after_update(self, config: Config):
        index = int(self.config["index"])
        config.update_config({self.name: {"index": index + 1}})


class ClockMode(BaseMode):
    name = "clock"

    @staticmethod
    def draw_round(image, center, radius, long, angle1, angle2, color=None):
        draw_obj = ImageDraw.Draw(image)
        if color is None:
            color = 'black'
        draw_obj.ellipse(
            (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
            fill=color
        )
        p1 = (
            round(long * math.cos(math.radians(90 - angle1))) + center[0],
            round(-1 * long * math.sin(math.radians(90 - angle1))) + center[1]
        )
        p2 = (
            round(-1 * long * math.tan(math.radians(angle2 / 2)) * math.cos(math.radians(angle1))) + center[0],
            round(-1 * long * math.tan(math.radians(angle2 / 2)) * math.sin(math.radians(angle1))) + center[1]
        )
        p3 = (
            round(long * math.tan(math.radians(angle2 / 2)) * math.cos(math.radians(angle1))) + center[0],
            round(long * math.tan(math.radians(angle2 / 2)) * math.sin(math.radians(angle1))) + center[1]
        )
        draw_obj.polygon([p1, p2, p3], fill=color)

    def get_image(self) -> Optional[Image.Image]:
        # 重置画布
        image = self.empty_image()
        # 计算时针分针角度
        now = time.localtime()
        hour_angle = ((now.tm_hour % 12) + now.tm_min / 60) / 12 * 360
        minute_angle = now.tm_min / 60 * 360
        invert_flag = False
        if now.tm_sec >= 30:
            invert_flag = True
        # 计算圆心坐标、时针分针半径
        center = (round(self.width / 2), round(self.height / 2))
        radius_h = round(min(self.width, self.height) / 2 * 0.50)
        radius_m = round(min(self.width, self.height) / 2 * 0.65)
        # 绘制时针分针圆盘
        self.draw_round(image, center, radius_m, round(radius_m * 1.2), minute_angle, 60, 'black')
        self.draw_round(image, center, radius_h, round(radius_h * 1.2), hour_angle, 60, 'white')
        # 反转颜色
        if invert_flag:
            image = invert(image)
        return image

    def need_update(self) -> bool:
        return self.is_enough_interval(30)


class AlbumMode(BaseMode):
    name = "album"

    def __init__(self):
        super().__init__()
        self._album_list = []
        self._current_photo = ""

    def _update_album_list(self):
        self._current_photo = self.config.get("current", "")
        self._album_list = [file for file in glob.glob(os.path.join(ALBUM_DIR, "*"))]
        if self._current_photo not in self._album_list:
            if len(self._album_list) == 0:
                self._current_photo = ""
            else:
                self._current_photo = self._album_list[0]

    def _get_index(self) -> int:
        for i in range(len(self._album_list)):
            if self._album_list[i] == self._current_photo:
                return i

    def _next_photo(self):
        length = len(self._album_list)
        if length > 0:
            index = (self._get_index() + 1) % length
            self._current_photo = self._album_list[index]

    def after_update(self, config: Config):
        config.update_config({"album": {"current": self._current_photo}})

    def need_update(self) -> bool:
        return self.is_enough_interval(float(self.config.get("interval", "86400")))

    def get_image(self) -> Optional[Image.Image]:
        self._update_album_list()
        if self._current_photo != "":
            img = resize_img(os.path.join(ALBUM_DIR, self._current_photo), self.size)
        else:
            img = self.empty_image()
            img = draw_text("轮播相册模式\n相册文件夹为空", img)
        self._next_photo()
        return img
