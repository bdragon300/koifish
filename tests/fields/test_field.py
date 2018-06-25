import pytest
from copy import copy, deepcopy
from fields import Field
from enum import Enum


class ColorEnumStub(Enum):
    RED = 44
    GREEN = 55
    BLUE = 'blue'


class TestField:
    def test_default_prop_values(self):
        obj = Field()

        assert obj.field_type is None
        assert obj.name is None
        assert obj.required is False
        assert obj.tags == frozenset()
        assert obj.get_callback is None
        assert obj.save_callback is None
        assert obj.val is None
        assert obj.raw is None

    def test_field_type_prop_initialized(self):
        obj = Field(field_type=bool)

        assert obj.field_type == bool

    def test_name_prop_initialized(self):
        obj = Field(_name='FooName')

        assert obj.name == 'FooName'

    def test_required_prop_initialized(self):
        obj = Field(required=True)

        assert obj.required is True

    def test_tags_prop_initialized(self):
        iterable = ['tag1', 'tag2', 'tag3']

        obj = Field(
            tags=iterable
        )

        assert obj.tags == frozenset(iterable)

    @pytest.mark.parametrize('init_value', (('tag1', 'tags2')))
    def test_tags_prop_type(self, init_value):
        obj = Field(tags=init_value)

        assert isinstance(obj.tags, frozenset)

    def test_get_callback_prop_initialized(self):
        obj = Field(
            get_callback=lambda field, data: 'get_callback_test'
        )

        assert obj.get_callback(obj, {}) == 'get_callback_test'

    def test_save_callback_prop_initialized(self):
        obj = Field(
            save_callback=lambda field, data: 'save_callback_test'
        )

        assert obj.save_callback(obj, {}) == 'save_callback_test'

    @pytest.mark.parametrize('init_value', (None, True, 123, 'string'))
    def test_raw_prop_without_typing(self, init_value):
        obj = Field()
        obj._raw_val = init_value

        x = obj.raw

        assert x is init_value

    @pytest.mark.parametrize('init_value', (None, True, 123, 'string'))
    def test_raw_prop_set(self, init_value):
        obj = Field()

        obj.raw = init_value

        assert obj._raw_val is init_value

    @pytest.mark.parametrize('field_type,init_value,expect_value', (
        (bool, 1, True),
        (int, True, 1),
        (str, 123, '123'),
        (int, '123', 123),
        (float, 1, 1.0)
    ))
    def test_val_prop_typing_builtin_types(self, field_type, init_value, expect_value):
        obj = Field(field_type=field_type)

        obj.val = init_value
        x = obj.val

        assert x == expect_value
        assert type(x) == type(expect_value)

    @pytest.mark.parametrize('field_type,init_value', (
        (dict, 1),
        (int, int),
        (int, type)
    ))
    def test_val_prop_typing_type_error_builtins_types(self, field_type, init_value):
        obj = Field(field_type=field_type)

        with pytest.raises(TypeError):
            obj.val = init_value

    @pytest.mark.parametrize('field_type,init_value,expect_raw_value', (
        (['RED', 'GREEN', 'BLUE'], 'RED', 0),
        ({'RED': 35, 'GREEN': 'deep green', 'BLUE': 'blue'}, 'RED', 35),
        ({'RED': 35, 'GREEN': 'deep green', 'BLUE': 'blue'}, 'GREEN', 'deep green'),
        (ColorEnumStub, 'RED', ColorEnumStub['RED'].value)
    ))
    def test_val_prop_set_in_enum_field_type(self, field_type, init_value, expect_raw_value):
        obj = Field(field_type=field_type)

        obj.val = init_value

        assert obj.raw == expect_raw_value

    @pytest.mark.parametrize('field_type', (
            ['RED', 'GREEN', 'BLUE'],
            {'RED': 35, 'GREEN': 'deep green', 'BLUE': 'blue'},
            ColorEnumStub
    ))
    @pytest.mark.parametrize('wrong_value', ('BLACK', int, type))
    def test_val_prop_error_on_wrong_value_set_in_enum_field_type(self, field_type, wrong_value):
        obj = Field(field_type=field_type)

        with pytest.raises(KeyError):
            obj.val = wrong_value

    def test_val_prop_default_if_field_value_is_set(self):
        obj = Field(field_type=int)

        assert obj.val is None

    @pytest.mark.parametrize('init_value', (None, True, 123, 'string'))
    def test_val_prop_without_typing(self, init_value):
        obj = Field()
        obj.val = init_value

        x = obj.val

        assert x == init_value
        assert type(x) == type(init_value)

    def test_val_prop_none_value_typing_immune(self):
        obj = Field(field_type=int)

        obj.val = 123
        obj.val = None

        assert obj.val is None

    def test_repr(self):
        obj = Field(field_type=int, _name='Field1')
        obj.val = 123

        assert repr(obj) == "<{} '{}'> = {}".format(obj.__class__.__name__, obj.name, obj.val)

    def test_str(self):
        obj = Field(field_type=int, _name='Field1')
        obj.val = 123

        assert repr(obj) == "<{} '{}'> = {}".format(obj.__class__.__name__, obj.name, obj.val)

    def test_eq(self):
        obj = Field()

        with pytest.raises(TypeError):
            obj == obj

    def test_ne(self):
        obj = Field()

        with pytest.raises(TypeError):
            obj != obj


class TestFieldCopy:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = Field(
            field_type=list,
            required=True,
            tags={'tag1', 'tag2'}
        )

    @pytest.mark.parametrize('member', Field.__slots__)
    def test_copying(self, member):
        setattr(self.obj, member, 'test_value')

        copy_obj = copy(self.obj)

        # Python allocates equal frozensets in single place. We need change one to make them different
        # copy_obj._tags |= {'another_tag'}

        assert getattr(self.obj, member) == getattr(copy_obj, member)
        assert type(getattr(self.obj, member)) == type(getattr(copy_obj, member))
        # assert copy_obj is not self.obj
        # assert copy_obj.val == self.obj.val
        # assert copy_obj.val is not self.obj.val
        # assert copy_obj.tags is not self.obj.tags
        # assert copy_obj.enum_cls == self.obj.enum_cls

    @pytest.mark.parametrize('member', Field.__slots__)
    def test_deepcopy(self, member):
        setattr(self.obj, member, 'test_value')

        deepcopy_obj = deepcopy(self.obj)

        # # Python allocates equal frozensets in single place. We need change one to make them different
        # deepcopy_obj._tags |= {'another_tag'}

        assert getattr(self.obj, member) == getattr(deepcopy_obj, member)
        assert type(getattr(self.obj, member)) == type(getattr(deepcopy_obj, member))
        # assert deepcopy_obj is not self.obj
        # assert deepcopy_obj.val == self.obj.val
        # assert deepcopy_obj.val is not self.obj.val
        # assert deepcopy_obj.tags is not self.obj.tags
        # assert deepcopy_obj.enum_cls == self.obj.enum_cls
