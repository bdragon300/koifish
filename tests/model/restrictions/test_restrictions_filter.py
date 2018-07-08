import random

import pytest

from model.restrictions import Filter, Filters, FilterOperator

test_filters = (
    ('test_field1__eq', '1234'),
    ('test_field2__lt', 45),
    ('test_field4__in', (1, 2, 3))
)

check_filters = (
    ('test_field1', {Filter(field_name='test_field1', op=FilterOperator.Equal, val='1234')}),
    ('test_field2', {Filter(field_name='test_field2', op=FilterOperator.LessThan, val=45)}),
    ('test_field4', {Filter(field_name='test_field4', op=FilterOperator.In, val=(1, 2, 3))}),
)

wrong_filters = (
    (('test_field', 2365), ),
    (('test_field__eq', 35), ('another_field_eq', "test_value")),
    (('test_field__something', 'test_value'), )
)


class TestFilters:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = Filters()

    @pytest.mark.parametrize('test,check',
        ((test_filters[:x], check_filters[:x]) for x in range(1, len(test_filters) + 1))
    )
    def test_init_by_expression(self, test, check):
        test = dict(test)
        check = dict(check)
        obj = Filters(**test)

        assert dict(obj) == check

    @pytest.mark.parametrize('test,check',
        ((test_filters[:x], check_filters[:x]) for x in range(1, len(test_filters) + 1))
    )
    def test_make(self, test, check):
        test = dict(test)
        check = dict(check)
        self.obj.make(**test)

        assert dict(self.obj) == check

    @pytest.mark.parametrize('test', wrong_filters)
    def test_make_error_on_wrong_expr_syntax(self, test):
        test = dict(test)

        with pytest.raises(ValueError):
            self.obj.make(**test)

    def test_make_clears_all_existing_restrictions(self):
        self.obj.make(**dict(test_filters))

        self.obj.make()

        assert dict(self.obj) == {}

    @pytest.mark.parametrize('test,check',
        ((test_filters[:x], check_filters[:x]) for x in range(1, len(test_filters) + 1))
    )
    def test_apply(self, test, check):
        test = dict(test)
        check = dict(check)
        self.obj.apply(**test)

        assert dict(self.obj) == check

    @pytest.mark.parametrize('test', wrong_filters)
    def test_apply_error_on_wrong_expr_syntax(self, test):
        test = dict(test)
        with pytest.raises(ValueError):
            self.obj.apply(**test)

    def test_apply_appends_restriction_to_existing_ones(self):
        test_data = {
            'two_restrictions__eq': '1234',
            'two_restrictions__gt': 123
        }
        check_data = {
            'two_restrictions': {
                Filter(field_name='two_restrictions', op=FilterOperator.Equal, val='1234'),
                Filter(field_name='two_restrictions', op=FilterOperator.GreaterThan, val=123)
            }
        }
        for k, v in test_data.items():
            self.obj.apply(**{k: v})

        assert dict(self.obj) == check_data
