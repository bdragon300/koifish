import pytest

from model.restrictions import SortOperator, Sort, Sorts

test_sorts = ('ascending_sort', '-descending_sort')

check_sorts = (
    ('ascending_sort', {Sort(field_name='ascending_sort', direction=SortOperator.Ascending)}),
    ('descending_sort', {Sort(field_name='descending_sort', direction=SortOperator.Descending)})
)

wrong_sorts = ('', '--expr', 'expr-expr2', 'expr-')


class TestSorts:
    test_incorrect_data = [
        {
            'test_field': 2365
        },
        {
            'test_field__asc': 'qrwgqwrg',
        },
        {
            'test_field__asc': 1,
            'another_field_asc': 2
        },
        {
            'test_field__unknown': 1
        }
    ]

    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = Sorts()

    @pytest.mark.parametrize('test,check', (
        ((test_sorts[:x], check_sorts[:x]) for x in range(1, len(test_sorts) + 1))
    ))
    def test_init_by_expression(self, test, check):
        check = dict(check)
        obj = Sorts(*test)

        assert dict(obj) == check

    @pytest.mark.parametrize('test,check',
        ((test_sorts[:x], check_sorts[:x]) for x in range(1, len(test_sorts) + 1))
    )
    def test_make(self, test, check):
        check = dict(check)
        self.obj.make(*test)

        assert dict(self.obj) == check

    @pytest.mark.parametrize('test', wrong_sorts)
    def test_make_error_on_wrong_expr_syntax(self, test):
        with pytest.raises(ValueError):
            self.obj.make(test)

    def test_make_clears_all_existing_restrictions(self):
        self.obj.make(*test_sorts)

        self.obj.make()

        assert dict(self.obj) == {}

    @pytest.mark.parametrize('test,check',
        ((test_sorts[:x], check_sorts[:x]) for x in range(1, len(test_sorts) + 1))
    )
    def test_apply(self, test, check):
        check = dict(check)
        self.obj.apply(*test)

        assert dict(self.obj) == check

    @pytest.mark.parametrize('test', wrong_sorts)
    def test_apply_error_on_wrong_expr_syntax(self, test):
        with pytest.raises(ValueError):
            self.obj.apply(test)

    def test_apply_appends_restriction_to_existing_ones(self):
        self.obj.apply('field1')

        self.obj.apply('-field2')

        assert dict(self.obj) == {
            'field1': {Sort(field_name='field1', direction=SortOperator.Ascending)},
            'field2': {Sort(field_name='field2', direction=SortOperator.Descending)}
        }

    def test_apply_replaces_restriction_for_the_same_field(self):
        self.obj.apply('field1')

        self.obj.apply('-field1')

        assert dict(self.obj) == {
            'field1': {Sort(field_name='field1', direction=SortOperator.Descending)},
        }
