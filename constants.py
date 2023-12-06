import os

# 路径相关参数
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)
ALBUM_DIR = os.path.join(ROOT_DIR, "album")
if not os.path.exists(ALBUM_DIR):
    os.mkdir(ALBUM_DIR)

# 墨水屏参数
VCOM = -1.45
WIDTH = 1872
HEIGHT = 1404

# API 服务参数
HOST = "0.0.0.0"
API_PORT = 2264

# GPIO 相关参数
BUTTON_VCC_PIN = 5
BUTTON_OUT_PIN = 6
BUZZER_VCC_PIN = 12
BUZZER_IO_PIN = 16
# BUZZER_GND_PIN = 34

# 控制参数
CLEAR_BEFORE_UPDATE = False
IS_RUN_GPIO = False
HAS_BUZZER = False
