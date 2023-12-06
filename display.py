from abc import ABCMeta, abstractmethod

from IT8951 import constants
from IT8951.display import AutoEPDDisplay
from PIL import Image


class Display(metaclass=ABCMeta):
    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def update(self, file):
        pass


class IT8951Display(Display):
    def __init__(self, vcom: float):
        self._epd = AutoEPDDisplay(vcom=vcom)

    @property
    def width(self) -> int:
        return self._epd.width

    @property
    def height(self) -> int:
        return self._epd.height

    def clear(self):
        self._epd.clear()

    def update(self, file):
        self._epd.frame_buf.paste(0xFF, box=(0, 0, self.width, self.height))
        img = Image.open(file)
        self._epd.frame_buf.paste(img, (0, 0))
        self._epd.draw_full(constants.DisplayModes.GC16)


class WaveShareDisplay(Display):
    def __init__(self):
        # 此处根据自己购买的墨水屏型号自行修改 self._epd
        from waveshare_epd import epd5in65f
        self._epd = epd5in65f.EPD()
        self._epd.init()

    def clear(self):
        self._epd.Clear()

    def update(self, file):
        img = Image.open(file)
        self._epd.display(self._epd.getbuffer(img))
