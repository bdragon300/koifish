import pytest
import random
import itertools
from sparsedlist import SparsedList
from cacher import MemoryCache, MemoryCacher
import re


@pytest.fixture
def plain_data():
    return [(i, object()) for i in range(40)]


@pytest.fixture
def powertwo_data():
    return [(2 ** i, object()) for i in range(10)]


def slice_permutations(start, stop, step):
    z = (list(zip(x, (start, stop, step))) for x in itertools.product((None, 1), repeat=3))
    for i in z:
        p = list(None if j[0] is None else j[1] for j in i)
        yield slice(*p)


class TestMemoryCache:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = MemoryCache()

    def test_props_default_values(self):
        assert len(self.obj.data) == 0

    @pytest.mark.parametrize('a,b,expect', (
        ({0: 0, 5: 5, 10: 10}, {0: 0, 5: 5, 10: 10}, True),
        ({0: 0, 5: 5, 10: 10}, {0: 0, 5: 5}, False),
        ({0: 0, 6: 6, 10: 10}, {0: 0, 5: 5, 10: 10}, False),
        ({0: 0, 5: 6, 10: 10}, {0: 0, 5: 5, 10: 10}, False)
    ))
    def test_equal(self, a, b, expect):
        obj = MemoryCache()
        obj.extend(a.items())
        self.obj.extend(b.items())

        res = self.obj == obj

        assert res is expect

    @pytest.mark.parametrize('a,b,expect', (
        ({0: 0, 5: 5, 10: 10}, {0: 0, 5: 5, 10: 10}, False),
        ({0: 0, 5: 5, 10: 10}, {0: 0, 5: 5}, True),
        ({0: 0, 6: 6, 10: 10}, {0: 0, 5: 5, 10: 10}, True),
        ({0: 0, 5: 6, 10: 10}, {0: 0, 5: 5, 10: 10}, True)
    ))
    def test_not_equal(self, a, b, expect):
        obj = MemoryCache()
        obj.extend(a.items())
        self.obj.extend(b.items())

        res = self.obj != obj

        assert res is expect

    def test_len(self, powertwo_data):
        self.obj.extend(powertwo_data)
        check_data = list(powertwo_data)[-1][0] + 1

        res = len(self.obj)

        assert res == check_data

    @pytest.mark.parametrize('ind', (1, -2))
    def test_getitem_index(self, ind, plain_data):
        self.obj.extend(plain_data)
        test_data = [i[1] for i in plain_data]

        res = self.obj[ind]

        assert res == test_data[ind]

    @pytest.mark.parametrize('ind', itertools.chain(
        slice_permutations(1, 10, 3),
        slice_permutations(-10, -1, 3)
    ))
    def test_getitem_slice(self, ind, plain_data):
        self.obj.extend(plain_data)
        test_data = [i[1] for i in plain_data]

        res = self.obj[ind]

        print(list(self.obj.items()))
        assert list(res) == test_data[ind]

    @pytest.mark.parametrize('ind', (3, 2**15, -2**15))
    def test_getitem_indexerror_int_index(self, ind, powertwo_data):
        self.obj.extend(powertwo_data)

        with pytest.raises(IndexError):
            self.obj[ind]

    @pytest.mark.parametrize('ind', itertools.chain(
        slice_permutations(2 ** 15, 2 ** 16, 3),
        slice_permutations(2, 50, 3),
        slice_permutations(-200, -100, 3)
    ))
    def test_getitem_indexerror_slice(self, ind, powertwo_data):
        self.obj.extend(powertwo_data)

        with pytest.raises(IndexError):
            list(self.obj[ind])

    @pytest.mark.parametrize('step', (0, -1))
    def test_getitem_error_on_zero_or_negative_step(self, step, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(ValueError):
            self.obj[1:3:step]

    @pytest.mark.parametrize('ind', itertools.chain(
        slice_permutations(1, 10, 3),
        slice_permutations(-200, -100, 3),
        slice_permutations(10, 1, 3),
        slice_permutations(-100, -200, 3),
    ))
    def test_getitem_error_on_empty_list(self, ind):
        with pytest.raises(IndexError):
            list(self.obj[ind])

    @pytest.mark.parametrize('ind', (2, -3, 1000))
    def test_setitem_index(self, ind, plain_data):
        self.obj.extend(plain_data)

        self.obj[ind] = 'test_mark'

        assert self.obj[ind] == 'test_mark'

    @pytest.mark.parametrize('ind', (2, -3, 1000))
    def test_setitem_index_replace_old_value(self, ind, plain_data):
        self.obj.extend(plain_data)

        self.obj[ind] = 'test'
        self.obj[ind] = 'test_mark'

        assert self.obj[ind] == 'test_mark'
        assert len(list(self.obj.items(start=ind, stop=ind + 1))) == 1  # SkipList allows add several value for one key

    @pytest.mark.parametrize('ind', itertools.chain(
        slice_permutations(0, 10, 3),
        slice_permutations(100, 110, 3)
    ))
    def test_setitem_slice(self, ind):
        list_length = 10
        test_data = ['test_mark' + str(x) for x in range(list_length)]

        self.obj[ind] = test_data

        assert all(a == b for a, b in zip(self.obj[ind], test_data))

    @pytest.mark.parametrize('ind', (
        slice(0, 5),
        slice(None, 5),
        slice(0, 5, 2),
        slice(-11, -5),
        slice(-11, -5, 2)
    ))
    def test_setitem_cut_value_if_slice_shorter_on_filled_list(self, ind, plain_data):
        self.obj.extend(plain_data)
        list_length = 10
        test_data = ['test_mark'] * list_length

        self.obj[ind] = test_data

        assert self.obj[ind.stop + ((ind.step or 1) - 1)] != 'test_mark'  # Check next item

    @pytest.mark.parametrize('ind', (
        slice(0, 5),
        slice(None, 5),
        slice(0, 5, 2)
    ))
    def test_setitem_cut_value_if_slice_shorter_on_unfilled_list(self, ind):
        list_length = 10
        test_data = ['test_mark'] * list_length

        self.obj[ind] = test_data

        # Check next item
        with pytest.raises(IndexError):
            check_index = ind.stop + ((ind.step or 1) - 1)
            self.obj[check_index]

    @pytest.mark.parametrize('ind', slice_permutations(5, 25, 3))
    def test_setitem_remove_the_rest_elements_if_positive_slice_longer_than_iterable(self, ind, plain_data):
        self.obj.extend(plain_data)
        check_data = list(plain_data)
        list_length = 5
        test_data = ['test_mark'] * list_length

        self.obj[ind] = test_data

        start = (ind.start or 0) + list_length * (ind.step or 1)
        for i in range(start, ind.stop or len(check_data), ind.step or 1):
            with pytest.raises(IndexError):
                self.obj[i]

    @pytest.mark.parametrize('ind', slice_permutations(-25, -5, 3))
    def test_setitem_remove_the_rest_elements_if_negative_slice_longer_than_iterable(self, ind, plain_data):
        self.obj.extend(plain_data)
        check_data = list(plain_data)
        list_length = 5
        test_data = ['test_mark'] * list_length

        self.obj[ind] = test_data

        # Convert negative indexes to positive ones
        start = (len(check_data) + (ind.start or 0)) + list_length * (ind.step or 1)
        stop = len(check_data) + (ind.stop or 0)
        for i in range(start, stop, ind.step or 1):
            with pytest.raises(IndexError):
                self.obj[i]

    def test_setitem_error_if_not_iterable_for_slice(self):
        with pytest.raises(TypeError):
            self.obj[0:2] = 123

    def test_setitem_indexerror_too_much_negative_int_index(self, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(IndexError):
            self.obj[-1000] = 123

    @pytest.mark.parametrize('ind', (
        -1,
        slice(-11, -5),
        slice(-11, -5, 2)
    ))
    def test_setitem_error_negative_indexes_on_empty_list(self, ind):
        list_length = 10
        test_data = ['test_mark'] * list_length

        with pytest.raises(IndexError):
            self.obj[ind] = test_data

    @pytest.mark.parametrize('step', (0, -1))
    def test_setitem_error_on_zero_or_negative_step(self, step, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(ValueError):
            self.obj[1:3:step] = [1, 2]

    @pytest.mark.parametrize('ind', (2, -2))
    def test_delitem(self, ind, plain_data):
        self.obj.extend(plain_data)

        del self.obj[ind]

        with pytest.raises(IndexError):
            self.obj[ind]

    @pytest.mark.parametrize('ind', (1000, -1000))
    def test_delitem_error(self, ind, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(IndexError):
            del self.obj[ind]

    def test_reversed_error(self):
        with pytest.raises(TypeError):
            reversed(self.obj)

    def test_add_list(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = [1, 5, 10, 100]
        check_data = list(powertwo_data)
        check_data += enumerate(test_data, start=check_data[-1][0] + 1)

        res = self.obj.__add__(test_data)

        assert list(res.items()) == check_data
        assert res is not self.obj

    def test_add_object(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = MemoryCache()
        test_data.extend(powertwo_data)
        check_data = list(powertwo_data)
        offset = check_data[-1][0] + 1
        check_data += [(x[0] + offset, x[1]) for x in powertwo_data]

        res = self.obj.__add__(test_data)

        assert list(res.items()) == check_data
        assert res is not self.obj

    def test_radd_list(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = [1, 5, 10, 100]
        check_data = list(enumerate(test_data)) + [(x[0] + len(test_data), x[1]) for x in powertwo_data]

        res = self.obj.__radd__(test_data)

        assert list(res.items()) == check_data
        assert res is not self.obj

    def test_radd_object(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = MemoryCache()
        test_data.extend(powertwo_data)
        check_data = list(powertwo_data)
        offset = check_data[-1][0] + 1
        check_data += [(x[0] + offset, x[1]) for x in powertwo_data]

        res = self.obj.__radd__(test_data)

        assert list(res.items()) == check_data
        assert res is not self.obj

    def test_iadd_list(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = [1, 5, 10, 100]
        check_data = list(powertwo_data)
        check_data += enumerate(test_data, start=check_data[-1][0] + 1)

        res = self.obj.__iadd__(test_data)

        assert list(res.items()) == check_data
        assert res is self.obj

    def test_iadd_object(self, powertwo_data):
        self.obj.extend(powertwo_data)
        test_data = MemoryCache()
        test_data.extend(powertwo_data)
        check_data = list(powertwo_data)
        offset = check_data[-1][0] + 1
        check_data += [(x[0] + offset, x[1]) for x in powertwo_data]

        res = self.obj.__iadd__(test_data)

        assert list(res.items()) == check_data
        assert res is self.obj

    def test_mul(self, powertwo_data):
        self.obj.extend(powertwo_data)
        n = 4
        offset = list(powertwo_data)[-1][0] + 1
        check_data = [(x[0] + offset * c, x[1]) for c in range(n) for x in powertwo_data]

        res = self.obj.__mul__(n)

        assert list(res.items()) == check_data
        assert res is not self.obj

    def test_imul(self, powertwo_data):
        self.obj.extend(powertwo_data)
        n = 4
        offset = list(powertwo_data)[-1][0] + 1
        check_data = [(x[0] + offset * c, x[1]) for c in range(n) for x in powertwo_data]

        res = self.obj.__imul__(n)

        assert list(res.items()) == check_data
        assert res is self.obj

    def test_append(self, plain_data):
        self.obj.extend(plain_data)
        test_data = 'test_mark'

        self.obj.append(test_data)

        assert self.obj[-1] == test_data

    def test_extend(self, powertwo_data, plain_data):
        check_data = dict(powertwo_data)
        check_data.update(plain_data)
        check_data = sorted(check_data.items())

        self.obj.extend(powertwo_data)
        self.obj.extend(plain_data)

        assert all(a[0] == b[0] and a[1] is b[1] for a, b in zip(self.obj.items(), check_data))

    def test_clear(self, plain_data):
        self.obj.extend(plain_data)

        self.obj.clear()

        assert self.obj.count() == 0

    def test_reverse(self):
        with pytest.raises(TypeError):
            self.obj.reverse()

    @pytest.mark.parametrize('ind', (-2, 1))
    def test_pop(self, ind, plain_data):
        self.obj.extend(plain_data)
        *_, check_data = zip(*list(plain_data))

        res = self.obj.pop(ind)

        assert res == check_data[ind]
        assert self.obj.count() == len(check_data) - 1

    def test_pop_error_empty_list(self):
        with pytest.raises(IndexError):
            self.obj.pop()

    def test_remove(self, plain_data):
        self.obj.extend(plain_data)
        *_, test_data = zip(*list(plain_data))

        self.obj.remove(test_data[10])

        with pytest.raises(ValueError):
            self.obj.index(test_data[10])
        assert list(self.obj[:10]) == list(test_data[:10]) and list(self.obj[11:]) == list(test_data[11:])

    def test_remove_error_not_found(self, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(ValueError):
            self.obj.remove(123)

    def test_sort(self):
        with pytest.raises(TypeError):
            self.obj.sort()

    def test_copy(self, plain_data):
        self.obj.extend(plain_data)

        res = self.obj.copy()

        assert res is not self.obj
        assert list(self.obj.items()) == list(res.items())

    @pytest.mark.parametrize('start,stop', (
        (None, None),
        (None, 20),
        (10, None),
        (10, 20)
    ))
    def test_index_start_stop(self, start, stop, plain_data):
        self.obj.extend(plain_data)
        *_, test_data = zip(*list(plain_data))
        ind = 15

        res = self.obj.index(test_data[ind], start=start, stop=stop)

        assert res == ind

    @pytest.mark.parametrize('start,stop,ind', (
        (None, 20, 20),
        (10, None, 9),
        (10, 20, 20)
    ))
    def test_index_error_not_found_start_stop(self, start, stop, ind, plain_data):
        self.obj.extend(plain_data)
        test_data, *_ = zip(*list(plain_data))

        with pytest.raises(ValueError):
            self.obj.index(test_data[ind], start=start, stop=stop)

    def test_index_error_not_found(self, plain_data):
        self.obj.extend(plain_data)

        with pytest.raises(ValueError):
            self.obj.index('not_found')

    def test_count_return_items_count(self, plain_data):
        self.obj.extend(plain_data)
        test_data = list(plain_data)

        res = self.obj.count()

        assert res == len(test_data)

    def test_count_item_arg(self):
        test_data = enumerate([x % 5 for x in range(40)])
        check_data = len([x for x in test_data if x == 1])
        self.obj.extend(test_data)

        res = self.obj.count(1)

        assert res == check_data

    def test_count_item_kwarg(self):
        test_data = enumerate([x % 5 for x in range(40)])
        check_data = len([x for x in test_data if x == 1])
        self.obj.extend(test_data)

        res = self.obj.count(item=1)

        assert res == check_data

    @pytest.mark.parametrize('start,stop', (
        (None, None),
        (None, 20),
        (10, None),
        (10, 20)
    ))
    def test_items(self, start, stop, powertwo_data):
        self.obj.extend(powertwo_data)
        check_data = \
            list(x for x in powertwo_data if (start is None or x[0] >= start) and (stop is None or x[0] < stop))

        assert list(self.obj.items(start=start, stop=stop)) == check_data

    def test_tail(self, plain_data):
        self.obj.extend(plain_data)
        check_data = list(plain_data)[-1][0]

        res = self.obj.tail()

        assert res == check_data

    def test_tail_error_if_empty(self):
        with pytest.raises(IndexError):
            self.obj.tail()
