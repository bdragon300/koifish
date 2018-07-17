from copy import deepcopy

from cacher import MemoryCache
from exc import EmptyCacheError
from model.restrictions.restrictions import Filters, Sorts, Pagination
from decimal import Decimal

# Special constant used to point out that QuerySet has unknown count of objects (i.e. infinite count)
Inf = Decimal('Inf')


class BaseIterator:
    def __init__(self, qs, cache_iterator):
        self._qs = qs
        self._iter = cache_iterator
        self._offset = 0


class ModelIterator(BaseIterator):
    def __next__(self):
        try:
            self._offset += 1
            return self._qs.new_model(next(self._iter))
        except EmptyCacheError:
            self._qs.cache_page(self._offset)

            return self._qs.new_model(next(self._iter))


class ValuesIterator(BaseIterator):
    def __next__(self):
        try:
            self._offset += 1
            return next(self._iter)
        except EmptyCacheError:
            self._qs.cache_page(self._offset)

            return next(self._iter)


class QuerySet(object):
    """Provides interface for making list requests and working with returned objects list"""

    default_request_limit = 10

    def __init__(self, model_obj, **kwargs):
        """
        :param model_obj: Model object used to make list request
        :param cache: Cache object to use to cache manage
        :param request_limit: Limit of objects to request at once
        """
        self._model_obj = model_obj
        self._cache = kwargs.get('cache', MemoryCache())
        self._request_limit = kwargs.get('request_limit', self.default_request_limit)
        self._filters = Filters()
        self._sorts = Sorts()
        self._iterator_class = ModelIterator

    def filter(self, **kwargs):
        """
        Return a new QuerySet instance with the args ANDed to the existing set.

        Accepts kwargs in following syntax: field__operation=value. For possible operations see `FilterOperator`.
        :param kwargs: filter expressions
        :return: new QuerySet instance with given filters
        """
        obj = deepcopy(self)
        obj.filters.apply(**kwargs)

        return obj

    def order_by(self, *args):
        """
        Return a new QuerySet instance with the ordering changed.

        Accepts field names for ordering by. Field name preceeded by '-' means descending sort, e.g. '-field'.
        :param args: sort expressions
        :return:
        """
        obj = deepcopy(self)
        obj.sorts.apply(*args)

        return obj

    def all(self):
        """Return copy of current QuerySet instance"""
        return deepcopy(self)

    def count(self):
        """Return total_count number came with response"""
        try:
            return self._cache.total_count
        except EmptyCacheError:
            t = self[0]  # Fill cache with the first page
            return self._cache.total_count

    def exists(self):
        """Return True if the QuerySet contains any results"""
        return bool(self.count())

    def values(self):
        """Return a QuerySet that returns dictionaries, rather than model instances, when used as an iterable."""
        obj = deepcopy(self)
        obj._iterator_class = ValuesIterator

        return obj

    def set_request_limit(self, limit):
        """Set object limit to be requested"""
        self._request_limit = limit

        return self

    def new_model(self, data):
        """
        Return new model object with filled data.
        :param data: record dict
        :return:
        """
        obj = self._model_obj.new_model(data)
        obj.update(data)

        return obj

    def cache_page(self, offset):
        """
        Fetch one page with given offset and put it to cache
        :param offset:
        :return:
        """
        rl = self._request_limit
        res = self._fetch_page(offset, rl)
        self._cache[offset:rl] = res
        if res.total_count is not None:
            self._cache.total_count = res.total_count
        else:
            self._cache.total_count = Inf

    @property
    def filters(self):
        """Filters restriction object"""
        return self._filters

    @property
    def sorts(self):
        """Sorts restriction object"""
        return self._sorts

    @property
    def model_obj(self):
        """Model object which QuerySet instance was initialized with"""
        return self._model_obj

    @property
    def ordered(self):
        """True if the QuerySet is ordered — i.e. has an order_by() clause or a default ordering on the model."""
        return bool(self._sorts.data)

    def __iter__(self):
        return self._iterator_class(self, iter(self._cache))

    def __len__(self):
        return self.count()

    def __bool__(self):
        return bool(self.count())

    def __getitem__(self, k):
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        def objs(start, stop, step):
            c = start or 0

            # total_count may change during iteration
            while c < self._cache.total_count and (stop is None or (c < stop)):
                try:
                    o = self._cache[c]
                    yield
                except EmptyCacheError:
                    self.cache_page(c)
                    o = self._cache[c]

                yield self.new_model(o)
                c += step

        if isinstance(k, slice):
            start, stop, step = k.start, k.stop, k.step
            if start is not None:
                start = int(start)
            if stop is not None:
                stop = int(stop)
            return list(objs(start, stop, step))
        else:
            k = int(k)
            if k >= self._cache.total_count:
                raise IndexError('Index out of range')

            x = list(objs(k, k + 1, 1))
            return x[0]

    def __deepcopy__(self, memodict={}):
        obj = self.__class__(self._model_obj)
        for k, v in self.__dict__.items():
            if k == '_cache':
                obj.__dict__[k] = getattr(self, k).new()
            else:
                obj.__dict__[k] = deepcopy(v, memodict)

        return obj

    def _fetch_page(self, offset, limit):
        """
        Return one page of records with given offset/limit
        :param offset:
        :param limit:
        :return: ListResponse object
        """
        return self._model_obj.get_list(self.filters, self.sorts, Pagination(limit=limit, offset=offset))


__all__ = ('QuerySet', )