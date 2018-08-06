from enum import Enum
from unittest.mock import Mock

import pytest

from fields import Field, IntegerField


class ChoicesEnumStub(Enum):
    RED = 44
    GREEN = 55
    BLUE = 'blue'


choices_dict_stub = {'RED': 44, 'GREEN': 55, 'BLUE': 'blue'}


class TestField:
    def test_default_prop_values(self):
        obj = Field()

        assert obj.primary_key is False
        assert obj.virtual is False

    def test_primary_key_prop_initialized(self):
        obj = Field(
            primary_key=True
        )

        assert obj.primary_key is True

    @pytest.mark.parametrize('choice,val', {x: y.value for x, y in ChoicesEnumStub.__members__.items()}.items())
    def test_get_descriptor_enum_value_mapping(self, choice, val):
        obj = Field(choices=ChoicesEnumStub)
        model_mock = Mock(_data={obj: val})

        res = obj.__get__(model_mock, None)

        assert res == choice

    @pytest.mark.parametrize('choice,val', choices_dict_stub.items())
    def test_get_descriptor_dict_value_mapping(self, choice, val):
        obj = Field(choices=choices_dict_stub)
        model_mock = Mock(_data={obj: val})

        res = obj.__get__(model_mock, None)

        assert res == choice

    def test_get_descriptor_list_not_mapped(self):
        obj = Field(choices=[1, 2, 3])
        model_mock = Mock(_data={obj: 1})

        res = obj.__get__(model_mock, None)

        assert res == 1

    def test_get_descriptor_no_choices(self):
        obj = Field()
        model_mock = Mock(_data={obj: 1})

        res = obj.__get__(model_mock, None)

        assert res == 1

    def test_get_descriptor_return_self_on_class_access(self):
        obj = Field(choices=choices_dict_stub)
        res = obj.__get__(None, object)

        assert res is obj

    @pytest.mark.parametrize('choice,val', {x: y.value for x, y in ChoicesEnumStub.__members__.items()}.items())
    def test_set_descriptor_enum_value_mapping(self, choice, val):
        obj = Field(choices=ChoicesEnumStub)
        model_mock = Mock(_data={})

        obj.__set__(model_mock, choice)

        assert model_mock._data[obj] == val

    @pytest.mark.parametrize('choice,val', choices_dict_stub.items())
    def test_set_descriptor_dict_value_mapping(self, choice, val):
        obj = Field(choices=choices_dict_stub)
        model_mock = Mock(_data={})

        obj.__set__(model_mock, choice)

        assert model_mock._data[obj] == val

    def test_set_descriptor_list_not_mapped(self):
        obj = Field(choices=[1, 2, 3])
        model_mock = Mock(_data={})

        res = obj.__set__(model_mock, 1)

        assert model_mock._data[obj] == 1

    def test_set_descriptor_no_choices(self):
        obj = Field()
        model_mock = Mock(_data={})

        res = obj.__set__(model_mock, 1)

        assert model_mock._data[obj] == 1

    def test_validate_enum(self):
        obj = IntegerField(choices=ChoicesEnumStub)

        obj.validate(ChoicesEnumStub['RED'].value)

    def test_validate_dict(self):
        obj = IntegerField(choices=ChoicesEnumStub)

        obj.validate(choices_dict_stub['RED'])
