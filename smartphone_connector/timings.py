import threading
from time import time_ns
from typing import Callable
from inspect import signature


class CancleSubscription:
    __running = True

    @property
    def is_running(self):
        return self.__running

    def cancel(self):
        self.__running = False


class ThreadJob(threading.Thread):
    __next_id = 0
    __t_start = time_ns()
    __t_stop = time_ns()

    @classmethod
    def _next_id(cls):
        cls.__next_id += 1
        return f'job_{cls.__next_id}'

    def __init__(self, callback: Callable[[str, Callable], None], interval: float):
        '''runs the callback function after interval seconds'''
        self.callback = callback
        self.event = threading.Event()
        self.interval = interval
        self.__running = False
        self.__id = self._next_id()
        super(ThreadJob, self).__init__()

    def cancel(self):
        self.__running = False
        self.__t_stop = time_ns()
        self.event.set()

    stop = cancel

    @property
    def id(self):
        return self.__id

    @property
    def is_running(self):
        return self.__running

    def start(self):
        super().start()
        self.__t_start = time_ns()

    def reset_time(self):
        self.__t_start = time_ns()

    @property
    def time_s(self):
        '''returns the time in seconds since this job was started
        '''
        if self.is_running:
            return (time_ns() - self.__t_start) / 1000000000.0
        return (self.__t_stop - self.__t_start) / 1000000000.0

    def run(self):
        self.__running = True
        arg_count = len(signature(self.callback).parameters)
        if arg_count == 0:
            def clbk(): return self.callback()
        else:
            def clbk(): return self.callback(self)

        while not self.event.wait(self.interval):
            try:
                clbk()
            except:
                self.cancel()
                raise
