from .base import BaseCacher, BaseCache
from sparsedlist import SparsedList


class MemoryCache(BaseCache, SparsedList):
    def __init__(self, **kwargs):
        SparsedList.__init__(self)
        BaseCache.__init__(self, **kwargs)


class MemoryCacher(BaseCacher):
    def __init__(self, **kwargs):
        self.cache_class = MemoryCache
        super().__init__(**kwargs)
