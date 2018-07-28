from collections import MutableSequence
import abc


class BaseCache(MutableSequence, metaclass=abc.ABCMeta):
    __slots__ = ('total_count', 'init_args')

    def __init__(self, **kwargs):
        self.init_args = kwargs if kwargs else {}
        self.total_count = None

    def new(self):
        return self.__class__(**self.init_args)


class BaseCacher(metaclass=abc.ABCMeta):
    __slots__ = ('cache_class', 'init_args')

    def __init__(self, **kwargs):
        self.init_args = kwargs if kwargs else {}

    def new_cache(self, **kwargs):
        return self.cache_class(**kwargs)
