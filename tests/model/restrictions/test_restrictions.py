import pytest
from model.restrictions import Restrictions, Filters, Sorts, Pagination


test_filters_data = {
    'test_field__eq': 123,
    'id__gt': 777
}
test_sorts_data = ('field1', '-field2')
test_pagination_data = {
    'offset': 3,
    'limit': 10
}


class TestRestrictions:
    @pytest.fixture()
    def filled_restriction_pair(self):
        objs = (Restrictions(), Restrictions())
        for i in objs:
            i.filters.make(**test_filters_data)
            i.sorts.make(*test_sorts_data)
            i.pagination.limit = test_pagination_data['limit']
            i.pagination.offset = test_pagination_data['offset']

        yield objs

    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = Restrictions()

    def test_init_filters(self):
        assert dict(self.obj.filters) == {}

    def test_init_sorts(self):
        assert isinstance(self.obj.sorts, Sorts)
        assert dict(self.obj.sorts) == {}

    def test_init_pagination(self):
        assert isinstance(self.obj.pagination, Pagination)
        assert self.obj.pagination.limit is None
        assert self.obj.pagination.offset is None

    def test_eq_equal(self, filled_restriction_pair):
        a, b = filled_restriction_pair

        assert a == b

    def test_eq_different_sorts(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.sorts.apply('another_test_field')

        assert not(a == b)

    def test_eq_different_filters(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.filters.apply(another_test_field__eq=123)

        assert not(a == b)

    def test_eq_different_pagination(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.pagination.offset = a.pagination.offset + 1

        assert not(a == b)

    def test_ne_equal(self, filled_restriction_pair):
        a, b = filled_restriction_pair

        assert not(a != b)

    def test_ne_different_sorts(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.sorts.apply('another_test_field')

        assert a != b

    def test_ne_different_filters(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.filters.apply(another_test_field__eq=123)

        assert a != b

    def test_ne_different_pagination(self, filled_restriction_pair):
        a, b = filled_restriction_pair
        b.pagination.offset = a.pagination.offset + 1

        assert a != b
