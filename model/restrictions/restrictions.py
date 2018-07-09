from enum import Enum
from .base import BaseRestriction, BaseRestrictionContainer
from utils import DeepcopySlotMixin


class FilterOperator(Enum):
    """Operators used for filtering restrictions when doing requests"""
    Equal = 'eq'
    LessThan = 'lt'
    GreaterThan = 'gt'
    NotEqual = 'ne'
    In = 'in'


class SortOperator(Enum):
    """Sort directions used in restrictions when doing requests"""
    Ascending = 'asc'
    Descending = 'desc'


class Filter(BaseRestriction):
    __slots__ = (
        'field_name',
        'op',  # RestrictionMatchOp.*
        'val'
    )


class Sort(BaseRestriction):
    __slots__ = (
        'field_name',
        'direction'
    )


class Pagination(BaseRestriction):
    __slots__ = (
        'offset',
        'limit'
    )


class Filters(BaseRestrictionContainer):
    """
    Filter restrictions container.

    Acts as a dict with following structure: {'field name' => set(FilterRestriction, ...)}.

    Methods below implement 'filtering' interface such as `filter(field1__lt=12, field2_ne='string')`.
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: filter expressions: field__op=value, field2__op=value, ...
        """
        super().__init__()
        self.make(**kwargs)

    def make(self, *args, **kwargs):
        """
        Clear container and build new restriction objects using given 'filtering' expressions
        :param kwargs: filter expressions: field__op=value, field2__op=value, ...
        :return:
        """
        self.data.clear()
        self.apply(**kwargs)

    def apply(self, *args, **kwargs):
        """
        Make restriction objects using given 'filtering' expressions and append them to the existing ones
        :param kwargs: filter expressions: field__op=value, field2__op=value, ...
        :return:
        """
        for k, v in kwargs.items():
            res = self.make_object(k, v)

            # Append filter if field has another ones
            if res.field_name not in self.data:
                self.data[res.field_name] = set()
            self.data[res.field_name].add(res)

    @staticmethod
    def make_object(key, value):
        """
        Make FilterRestriction object from 'filtering' expression
        :param key:
        :param value:
        :raises ValueError: if expression with wrong syntax got
        :return: FilterRestriction object
        """
        try:
            (field_name, op) = key.split('__')
            op = FilterOperator(op)  # Check that op listed in FilterOperator
        except ValueError:
            raise ValueError("Bad filter expression syntax: {}={}".format(key, value))

        init_args = {
            'field_name': field_name,
            'op': op,
            'val': value
        }
        return Filter(**init_args)


class Sorts(BaseRestrictionContainer):
    """
    Sort restrictions container.

    Acts as a dict with following structure: {'field name' => set(SortRestriction, ...)}.

    Methods below implement 'sorting' interface such as `order_by('field1', '-field2')`.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: sort expressions: 'field1', '-field2'
        """
        super().__init__()
        self.make(*args, **kwargs)

    def make(self, *args, **kwargs):
        """
        Clear container and build new restriction objects using given sorts
        :param args: sort expressions: 'field1', '-field2'
        :return:
        """
        self.data.clear()
        self.apply(*args, **kwargs)

    def apply(self, *args, **kwargs):
        """
        Make restriction objects using given 'filtering' expressions and append them to the existing ones
        :param args: sort expressions: 'field1', '-field2'
        :return:
        """

        # Only one sort per field
        for i in args:
            res = self.make_object(i)
            self.data[res.field_name] = {res}

    @staticmethod
    def make_object(expr):
        """
        Make SortRestriction object from 'sorting' expression
        :return: SortRestriction object
        """
        chunks = expr.split('-')
        if len(chunks) > 2 or not expr:
            raise ValueError("Bad sorting expression syntax: '{}'".format(expr))

        direction = SortOperator.Ascending
        field_name = chunks.pop(0)
        if field_name == '':
            direction = SortOperator.Descending
            field_name = chunks.pop(0)
        elif chunks:
            raise ValueError("Bad sorting expression syntax: '{}'".format(expr))

        init_args = {
            'field_name': field_name,
            'direction': direction
        }

        return Sort(**init_args)


class Restrictions(DeepcopySlotMixin):
    """All restrictions container"""

    __slots__ = (
        'filters',
        'sorts',
        'pagination'
    )

    def __init__(self):
        self.filters = Filters()
        self.sorts = Sorts()
        self.pagination = Pagination(offset=None, limit=None)

    def __eq__(self, other):
        if not isinstance(other, Restrictions):
            return False

        return self.filters == other.filters \
            and self.sorts == other.sorts \
            and self.pagination == other.pagination

    def __ne__(self, other):
        return not(self.__eq__(other))
