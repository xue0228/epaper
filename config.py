import os
import shutil
from configparser import ConfigParser
from threading import RLock

from constants import ROOT_DIR
from observer import Subject


class Config(Subject):
    def __init__(self):
        super().__init__()
        self.config = ConfigParser()
        self._config_path = os.path.join(ROOT_DIR, "config.ini")
        if not os.path.exists(self._config_path):
            shutil.copy(os.path.join(ROOT_DIR, "config.ini.default"), self._config_path)
        self.config.read(self._config_path)
        self._dict = None
        self.lock = RLock()

    @property
    def dict(self) -> dict:
        if self._dict is None:
            self._dict = self._get_config()
        return self._dict

    def _get_config(self) -> dict:
        data = {}
        for k, v in self.config.items():
            data[k] = dict(v)
        return data

    def update_config(self, item: dict):
        with self.lock:
            for k, v in item.items():
                for k2, v2 in v.items():
                    self.config[k][k2] = str(v2)
            self._dict = self._get_config()
            with open(self._config_path, "w") as f:
                self.config.write(f)
