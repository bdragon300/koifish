import pytest
from unittest.mock import patch
from fieldtypes import JsonDict
from itsdangerous import json


class TestJsonDict:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = JsonDict()

    @pytest.mark.parametrize('initial_value', ('{}', '{"key1":"value1", "key2":{"key21":"value21"}}'))
    def test_json_init(self, initial_value):
        check_data = json.loads(initial_value)

        obj = JsonDict(initial_value)

        assert obj == check_data

    @pytest.mark.parametrize('initial_value', ({}, {'789': 000}, {'key1': 'value1', 'key2': 2}))
    def test_dict_init(self, initial_value):
        obj = JsonDict(initial_value)

        assert obj == initial_value

    def test_jsondict_init(self):
        initial_value = JsonDict({1: 2, 3: 4})
        obj = JsonDict(initial_value)

        assert obj == initial_value
        assert obj.__wrapped__ is not initial_value.__wrapped__

    @pytest.mark.parametrize('initial_value', ({}, {'789': 000}, {'ключ1': 'значение1', 'key2': 2}))
    def test_str_json_serialize(self, initial_value):
        dumped = json.dumps(initial_value)

        @patch('json.dumps')
        @patch('itsdangerous.json.dumps')
        def f(*args):
            dumps_mock, dumps_mock2 = args
            dumps_mock.return_value = dumped
            dumps_mock2.return_value = dumped

            obj = JsonDict(initial_value)

            assert str(obj) == json.dumps(initial_value, ensure_ascii=False)

        f()

    @pytest.mark.parametrize('initial_value', ({}, {'789': 000}, {'ключ1': 'значение1', 'key2': 2}))
    def test_repr_json_serialize(self, initial_value):
        dumped = json.dumps(initial_value)

        @patch('json.dumps')
        @patch('itsdangerous.json.dumps')
        def f(*args):
            dumps_mock, dumps_mock2 = args
            dumps_mock.return_value = dumped
            dumps_mock2.return_value = dumped

            obj = JsonDict(initial_value)

            assert repr(obj) == json.dumps(initial_value, ensure_ascii=False)

        f()
