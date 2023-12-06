import threading
import time
from typing import Iterable

from api import run_api
from constants import HAS_BUZZER, IS_RUN_GPIO
from display import Display
from gpio import Button, Buzzer
from log import logger
from mode import BaseMode
from singleton import config


def run_mode(display: Display, modes: Iterable[BaseMode]):
    """
    墨水屏显示模式控制子线程
    :param display:
    :param modes:
    :return:
    """
    for mode in modes:
        mode.set_display(display)
        config.attach(mode)
        logger.debug(f"成功配置模块：{mode.name}")

    while True:
        try:
            config.notify()
        except:
            logger.exception("主循环出错")
        time.sleep(float(config.dict["base"]["heartbeat"]))


def run_gpio(modes: Iterable[BaseMode]):
    """
    GPIO 控制子线程
    :param modes:
    :return:
    """
    logger.debug("开始运行 GPIO 控制模块")
    button = Button()
    if HAS_BUZZER:
        buzzer = Buzzer()

    modes = [mode.name for mode in modes]

    while True:
        if button.is_pressed():
            mode = config.dict["base"]["mode"]
            index = 0
            for i in range(len(modes)):
                if mode == modes[i]:
                    if i != len(modes) - 1:
                        index = i + 1
                    else:
                        index = 0
                    mode = modes[index]
                    break
            config.update_config({"base": {"mode": mode}})
            logger.debug(f"使用按键切换到{mode}模式")
            if HAS_BUZZER:
                buzzer.repeated_beep(index + 1)
        # 此处休眠时间调短可以提高按键的响应速度
        # 我是为了防止短时间内响应多次按键，特意将其调高到了 1s
        time.sleep(1)


def start_api(display: Display, modes: Iterable[BaseMode]):
    """
    主程序，启动各种不同的线程
    :param display:
    :param modes:
    :return:
    """
    threads = [
        threading.Thread(target=run_mode, args=(display, modes)),
        threading.Thread(target=run_api, args=(modes,)),
    ]
    if IS_RUN_GPIO:
        threads.append(threading.Thread(target=run_gpio, args=(modes,)))

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    from singleton import off_mode, fixed_mode, movie_mode, clock_mode, album_mode
    from constants import VCOM
    from display import IT8951Display

    # from display import WaveShareDisplay

    d = IT8951Display(VCOM)
    # d = WaveShareDisplay()
    m = [off_mode, fixed_mode, movie_mode, clock_mode, album_mode]
    start_api(d, m)
