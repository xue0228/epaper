from abc import ABCMeta, abstractmethod
from typing import List


class Observer(metaclass=ABCMeta):
    """
    观察者
    """

    @abstractmethod
    def update(self, notice):
        pass


class Subject:
    """
    被观察者，即观察目标
    """

    def __init__(self):
        self.observers: List[Observer] = []

    def attach(self, obs: Observer):
        self.observers.append(obs)

    def detach(self, obs: Observer):
        self.observers.remove(obs)

    def notify(self):
        for obs in self.observers:
            obs.update(self)
