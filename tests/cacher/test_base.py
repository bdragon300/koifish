import pytest
from cacher.base import BaseCache, BaseCacher
from unittest.mock import Mock


class ObjectStub:
    pass


class BaseCacheStub(BaseCache):
    def __delitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

    def __getitem__(self, item):
        pass

    def __len__(self):
        pass

    def insert(self, index, value):
        pass


class BaseCacherStub(BaseCacher):
    pass


class TestBaseCache:
    def test_default_total_count(self):
        obj = BaseCacheStub()

        assert obj.total_count is None

    @pytest.mark.parametrize('kwargs', (
        {},
        {'arg1': 'val1', 'arg2': 'val2'}
    ))
    def test_init_args(self, kwargs):
        obj = BaseCacheStub(**kwargs)

        assert obj.init_args == kwargs

    def test_new_creates_new_instance(self):
        obj = BaseCacheStub()

        res = obj.new()

        assert res is not obj and isinstance(res, obj.__class__)

    @pytest.mark.parametrize('kwargs', (
        {},
        {'arg1': 'val1', 'arg2': 'val2'}
    ))
    def test_new_passes_init_args_to_new_instance(self, kwargs):
        obj = BaseCacheStub(**kwargs)

        res = obj.new()

        assert res.init_args == obj.init_args


class TestBaseCacher:
    @pytest.mark.parametrize('kwargs', (
        {},
        {'arg1': 'val1', 'arg2': 'val2'}
    ))
    def test_init_args(self, kwargs):
        obj = BaseCacherStub(**kwargs)

        assert obj.init_args == kwargs

    def test_new_cache_return_cache_class(self):
        obj = BaseCacherStub()
        obj.cache_class = ObjectStub

        res = obj.new_cache()

        assert isinstance(res, ObjectStub)

    @pytest.mark.parametrize('kwargs', (
        {},
        {'arg1': 'val1', 'arg2': 'val2'}
    ))
    def test_new_cache_passes_kwargs_to_object(self, kwargs):
        obj = BaseCacherStub()
        obj.cache_class = Mock()

        res = obj.new_cache(**kwargs)

        obj.cache_class.assert_called_once_with(**kwargs)

    def test_new_cache_error_if_cache_class_has_not_set(self):
        obj = BaseCacherStub()

        with pytest.raises(AttributeError):
            obj.new_cache()
