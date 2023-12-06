import time

from RPi import GPIO

from constants import BUTTON_VCC_PIN, BUTTON_OUT_PIN, BUZZER_VCC_PIN, BUZZER_IO_PIN

# 采用 BCM 引脚编号
# GPIO.setmode(GPIO.BOARD)
# 因为 IT8951 包内也用到了 RPi.GPIO，此处选择的模式必须与其相同
# 否则在同一进程内运行会因选择的模式不同而报错
GPIO.setmode(GPIO.BCM)
# 关闭警告
GPIO.setwarnings(False)


class Button:
    def __init__(self, vcc=BUTTON_VCC_PIN, out=BUTTON_OUT_PIN, bounce_time=200):
        self._vcc = vcc
        self._out = out
        if vcc != 0:
            GPIO.setup(vcc, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(out, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self._out, GPIO.RISING, bouncetime=bounce_time)

    def is_pressed(self) -> bool:
        return GPIO.event_detected(self._out)

    def clean_up(self):
        GPIO.cleanup([self._vcc, self._out])


class Buzzer:
    def __init__(self, vcc=BUZZER_VCC_PIN, io_pin=BUZZER_IO_PIN, dc=50):
        self._vcc = vcc
        self._io_pin = io_pin
        self._dc = dc
        self._p = None

    def beep(self, freq, duration):
        self._set_output()
        self._p.ChangeFrequency(freq)
        self._p.start(self._dc)
        time.sleep(duration)
        self._p.stop()
        # 不用发出声音时马上将通道关闭
        # 否则蜂鸣器会因为 IO 口的电压波动而发出较大的噪音
        self.clean_up()

    def _set_output(self):
        GPIO.setup(self._vcc, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self._io_pin, GPIO.OUT)
        self._p = GPIO.PWM(self._io_pin, 1)

    def repeated_beep(self, num, freq=1000, duration=0.1, interval=0.1):
        self._set_output()
        for i in range(num):
            self._p.ChangeFrequency(freq)
            self._p.start(self._dc)
            time.sleep(duration)
            self._p.stop()
            if i != num - 1:
                time.sleep(interval)
        self.clean_up()

    def clean_up(self):
        GPIO.cleanup([self._vcc, self._io_pin])


def play_song(buzzer):
    # 定义音调频率
    # C调低音
    CL = [0, 131, 147, 165, 175, 196, 211, 248]
    # C调中音
    CM = [0, 262, 294, 330, 350, 393, 441, 495]
    # C调高音
    CH = [0, 525, 589, 661, 700, 786, 882, 990]
    # 定义乐谱
    # 音调 0表示休止符
    song_p = [
        CM[1], CM[2], CM[3], CM[5], CM[5], CM[0], CM[3], CM[2], CM[1], CM[2], CM[3], CM[0],
        CM[1], CM[2], CM[3], CM[7], CH[1], CH[1], CH[1], CM[7], CH[1], CM[7], CM[6], CM[5], CM[0],
        CM[1], CM[2], CM[3], CM[5], CM[5], CM[0], CM[3], CM[2], CM[1], CM[2], CM[1], CM[0],
        CM[1], CM[2], CM[3], CM[5], CM[1], CM[0], CM[1], CL[7], CL[6], CL[7], CM[1], CM[0]
    ]
    # 音调对应的节拍
    song_t = [
        2, 2, 2, 1, 5, 4, 2, 2, 2, 1, 5, 4,
        2, 2, 2, 1, 5, 2, 2, 2, 1, 3, 2, 4, 4,
        2, 2, 2, 1, 5, 4, 2, 2, 2, 1, 3, 5,
        2, 2, 2, 1, 5, 4, 2, 2, 2, 2, 8, 2
    ]
    # 定义标准节拍时间
    metre = 0.125
    for i in range(len(song_p)):
        if song_p[i] == 0:
            time.sleep(song_t[i] * metre)
        else:
            buzzer.beep(song_p[i], song_t[i] * metre)


if __name__ == '__main__':
    button = Button()
    buzzer = Buzzer()

    while True:
        if button.is_pressed():
            buzzer.repeated_beep(3)
            break
        time.sleep(0.1)

    button.clean_up()
