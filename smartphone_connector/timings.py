import threading
from typing import Callable


class CancleSubscription:
    __running = True

    @property
    def is_running(self):
        return self.__running

    def cancel(self):
        self.__running = False


class ThreadJob(threading.Thread):
    def __init__(self, callback: Callable, interval: float):
        '''runs the callback function after interval seconds'''
        self.callback = callback
        self.event = threading.Event()
        self.interval = interval
        self.__running = False
        super(ThreadJob, self).__init__()

    def cancel(self):
        self.__running = False
        self.event.set()

    @property
    def is_running(self):
        return self.__running

    def run(self):
        self.__running = True
        while not self.event.wait(self.interval):
            self.callback()
