import itertools
from unittest.mock import Mock, MagicMock, call

import pytest
import random
import string

from cacher import MemoryCache
from layer.impl import ListResponse
from model import Model
from model.queryset import QuerySet, ModelIterator, ValuesIterator, Inf
from model.restrictions.restrictions import Filters, Sorts, Pagination


@pytest.fixture()
def record():
    d = ListResponse(initlist=[{'field1': 'value1', 'field2': 2}])
    d.total_count = len(d)

    return d

@pytest.fixture()
def records():
    recs = []
    for i in range(15):
        recs.append({
            'field' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)) :
                ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
                for i in range(3)
        })

    d = ListResponse(initlist=recs)
    d.total_count = 100500
    return d

@pytest.fixture()
def empty_records():
    res = ListResponse()
    res.total_count = 100500

    return res


def slice_permutations(start, stop, step):
    z = (list(zip(x, (start, stop, step))) for x in itertools.product((None, 1), repeat=3))
    for i in z:
        p = list(None if j[0] is None else j[1] for j in i)
        yield slice(*p)


class TestQuerySetMethods:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.model_obj = Mock(spec=Model)
        self.obj = QuerySet(self.model_obj)

    def test_default_vars(self):
        assert isinstance(self.obj._cache, MemoryCache) and not self.obj._cache.data
        assert isinstance(self.obj._filters, Filters) and not self.obj._filters.data
        assert isinstance(self.obj._sorts, Sorts) and not self.obj._sorts.data
        assert self.obj._request_limit == self.obj.default_request_limit
        assert self.obj._iterator_class is ModelIterator

    def test_request_limit_prop(self):
        test_data = 123
        self.obj.set_request_limit(test_data)

        assert self.obj.request_limit == test_data

    def test_filter_returns_new_queryset_instance(self):
        res = self.obj.filter(field1__ne=123)

        assert res is not self.obj and isinstance(res, QuerySet)

    def test_filter_has_effect(self):
        check_data = Filters(field1__ne=123)

        res = self.obj.filter(field1__ne=123)

        assert res.filters == check_data

    def test_filter_repeated_call_adds_filters(self):
        check_data = Filters(field1__ne=123, field2__lt=777)

        res = self.obj.filter(field1__ne=123).filter(field2__lt=777)

        assert res.filters == check_data

    def test_order_by_returns_new_queryset_instance(self):
        res = self.obj.order_by('-field1')

        assert res is not self.obj and isinstance(res, QuerySet)

    def test_order_by_has_effect(self):
        check_data = Sorts('-field1')

        res = self.obj.order_by('-field1')

        assert res.sorts == check_data

    def test_order_by_repeated_call_adds_sorts(self):
        check_data = Sorts('-field1', 'field2')

        res = self.obj.order_by('field2').order_by('-field1')

        assert res.sorts == check_data

    def test_all_returns_new_queryset_instance(self):
        res = self.obj.all()

        assert res is not self.obj and isinstance(res, QuerySet)

    def test_count_returns_cache_total_count(self, records):
        self.obj._cache[0:len(records)] = records
        self.obj._cache.total_count = records.total_count
        self.model_obj.get_list.side_effect = AssertionError  # Should not be called

        res = self.obj.count()

        assert res == records.total_count

    def test_count_fetch_and_return_total_count_on_empty_cache(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = self.obj.count()

        assert res == records.total_count

    def test_exists_true_on_some_records(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = self.obj.exists()

        assert res is True

    def test_exists_true_if_total_count_is_infinite(self, records, empty_records):
        records.total_count = None
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = self.obj.exists()

        assert res is True

    def test_exists_false_if_total_count_is_0(self, records, empty_records):
        records.total_count = 0
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = self.obj.exists()

        assert res is False

    def test_set_request_limit(self):
        self.obj.set_request_limit(1000)

        assert self.obj._request_limit == 1000

    def test_new_model_returns_new_instance(self):
        test_data = {}

        res = self.obj.new_model(test_data)

        assert res is self.model_obj.new_model.return_value
        self.model_obj.new_model.assert_called_once_with(test_data)

    def test_new_model_updates_model_with_data(self):
        test_data = {'field1': 'value1', 'field2': 2}
        res = self.obj.new_model(test_data)

        res.update.assert_called_once_with(test_data)

    def test_cache_page_impl_call_params(self, records):
        self.model_obj.get_list.return_value = records

        res = self.obj.cache_page(12)

        self.model_obj.get_list.assert_called_once_with(
            self.obj.filters, self.obj.sorts, Pagination(limit=self.obj._request_limit, offset=12)
        )

    def test_cache_page_slice_set_indexes(self):
        i = 19
        data = ListResponse(initlist=[
            {'field1': 'value11', 'field2': 21},
            {'field1': 'value12', 'field2': 22}
        ])
        data.total_count = 2
        self.obj.set_request_limit(1)
        self.model_obj.get_list.return_value = data
        self.obj._cache = MagicMock()

        res = self.obj.cache_page(i)

        self.obj._cache.__setitem__.assert_called_once_with(slice(i, i + self.obj._request_limit), data)

    def test_cache_page_set_cache_total_count(self, records):
        self.model_obj.get_list.return_value = records

        res = self.obj.cache_page(144)

        assert self.obj._cache.total_count == records.total_count

    def test_cache_page_set_cache_total_count_infinity_if_unknown(self, records):
        records.total_count = None
        self.model_obj.get_list.return_value = records

        res = self.obj.cache_page(156)

        assert self.obj._cache.total_count == Inf

    def test_filters_prop(self):
        assert self.obj.filters is self.obj._filters

    def test_sorts_prop(self):
        assert self.obj.sorts is self.obj._sorts

    def test_ordered_prop_false_if_no_sorts(self):
        assert self.obj.ordered is False

    def test_ordered_prop_true_if_sorts(self):
        res = self.obj.order_by('field1')

        assert res.ordered is True

    def test_model_obj_prop(self):
        assert self.obj._model_obj is self.model_obj

    def test_iteration_default_iterator(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = iter(self.obj)

        assert type(res) == ModelIterator

    def test_iteration_returns_items_on_empty_cache(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, records, empty_records)  # Return only one records page
        self.obj.new_model = Mock()

        items = [i for i in self.obj]

        assert all(i == self.obj.new_model.return_value for i in items)
        assert len(items) == len(records[:self.obj.request_limit] * 2)

    def test_iteration_new_model_calls_on_empty_cache(self, records, empty_records):
        test_data = records[:]
        self.model_obj.get_list.side_effect = (records, empty_records)
        self.obj.new_model = Mock()

        calls = [call(test_data.pop(0)) for i in self.obj]

        self.obj.new_model.assert_has_calls(calls)

    def test_iteration_returns_items_on_filled_cache(self, records):
        self.obj._cache[0:len(records)] = records
        self.obj._cache.total_count = records.total_count
        self.obj.new_model = Mock()

        items = [i for i in self.obj]

        assert all(i == self.obj.new_model.return_value for i in items)
        assert len(items) == len(records)

    def test_iteration_new_model_calls_on_filled_cache(self, records):
        test_data = records[:]
        self.obj._cache[0:len(records)] = records
        self.obj._cache.total_count = records.total_count
        self.obj.new_model = Mock()

        calls = [call(test_data.pop(0)) for i in self.obj]

        self.obj.new_model.assert_has_calls(calls)

    def test_values_returns_new_queryset_instance(self):
        self.model_obj.get_list.return_value = records

        res = self.obj.values()

        assert res is not self.obj and isinstance(res, QuerySet)

    def test_values_iterator(self):
        self.model_obj.get_list.return_value = records

        res = iter(self.obj.values())

        assert type(res) == ValuesIterator

    def test_values_iteration_returns_items_on_empty_cache(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)  # Return only one records page

        items = [i for i in self.obj.values()]
        assert items == records[:self.obj.request_limit]

    def test_values_iteration_returns_items_on_filled_cache(self, records):
        obj = self.obj.values()
        obj._cache[0:len(records)] = records
        obj._cache.total_count = records.total_count
        self.model_obj.get_list.side_effect = AssertionError  # Should not be called

        items = [i for i in obj]

        assert items == records

    def test_len(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = len(self.obj)

        assert res == records.total_count

    def test_bool_true_on_some_records(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)

        res = bool(self.obj)

        assert res is True

    def test_bool_true_if_total_count_is_infinite(self, records):
        records.total_count = None
        self.model_obj.get_list.return_value = records

        res = bool(self.obj)

        assert res is True

    def test_bool_false_if_total_count_is_0(self, records):
        records.total_count = 0
        self.model_obj.get_list.return_value = records

        res = bool(self.obj)

        assert res is False

    @pytest.mark.parametrize('start', (0, -1))
    @pytest.mark.parametrize('stop', (0, -1))
    @pytest.mark.parametrize('step', (0, -1))
    def test_getitem_negative_indices_slice(self, start, stop, step):
        ind = slice(start, stop, step)

        with pytest.raises(AssertionError):
            self.obj[ind]

    def test_getitem_genative_index(self):
        with pytest.raises(AssertionError):
            self.obj[-1]

    @pytest.mark.parametrize('ind', (1, 11, 17))
    def test_getitem_return_item(self, records, empty_records, ind):
        test_data = records.data[:self.obj.request_limit] * 2
        self.model_obj.get_list.side_effect = (records, records, empty_records)  # Return only one records page
        self.obj.new_model = lambda x: x  # Simple returns its argument, for compare convenience

        res = self.obj[ind]

        assert res == test_data[ind]

    @pytest.mark.parametrize('ind', itertools.chain(
        slice_permutations(1, 10, 3),
        slice_permutations(1, 20, 3)
    ))
    def test_getitem_return_items_slice(self, records, empty_records, ind):
        test_data = records.data[:self.obj.request_limit] * 2
        self.model_obj.get_list.side_effect = (records, records, empty_records)  # Return only one records page
        self.obj.new_model = lambda x: x  # Simple returns its argument, for compare convenience

        res = self.obj[ind]

        assert list(res) == test_data[ind]

    def test_getitem_out_of_range(self, records, empty_records):
        self.model_obj.get_list.side_effect = (records, empty_records)
        test_data = records.total_count + 1

        with pytest.raises(IndexError):
            self.obj[test_data]
