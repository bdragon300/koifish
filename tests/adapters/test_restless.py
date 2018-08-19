import itertools
from unittest.mock import Mock, patch

import inflection
import pytest
import requests_mock
from hammock import Hammock
from itsdangerous import json

from adapters import RestlessAdapter
from exc import AdapterError
from model.restrictions import Filters, Sorts, Pagination
from urllib.parse import urlparse, parse_qs


class TestRestlessHelper:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_config = {
            'name': 'httpmock://example.com',
            'headers': {'Content-Type': 'application/json'}
        }
        self.obj = RestlessAdapter(config=self.test_config)

    @pytest.mark.parametrize('config', (
        {},
        {'config': {'verify': True}}
    ))
    def test_default_headers_param(self, config):
        obj = RestlessAdapter(**config)

        assert obj.config['headers'] == {'Content-Type': 'application/json'}

    def test_get(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'pk_val': 1234
            }
            test_data = {
                'some_id': 444,
                'foo': 'bar'
            }
            check_data = test_data
            uri = "{}/{}/{}".format(
                self.test_config['name'],
                inflection.underscore(test_params['model_name']),
                test_params['pk_val']
            )
            a.register_uri('GET', uri, json=test_data)

            res = h.get(**test_params)

            assert res == check_data

    def test_create(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            test_data = {
                'some_id': 444,
                'foo': 'bar'
            }
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'data': test_data
            }
            check_data = test_data
            uri = "{}/{}".format(self.test_config['name'], inflection.underscore(test_params['model_name']))
            a.register_uri('POST', uri, json=test_data)

            res = h.create(**test_params)

            assert res == check_data

    def test_update(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            test_data = {
                'some_id': 444,
                'foo': 'bar'
            }
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'pk_val': 444,
                'data': test_data
            }
            check_data = test_data
            uri = "{}/{}/{}".format(
                self.test_config['name'],
                inflection.underscore(test_params['model_name']),
                test_params['pk_val']
            )
            a.register_uri('PUT', uri, json=test_data)

            res = h.update(**test_params)

            assert res == check_data

    def test_delete(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'pk_val': 444
            }
            uri = "{}/{}/{}".format(
                self.test_config['name'],
                inflection.underscore(test_params['model_name']),
                test_params['pk_val']
            )
            a.register_uri('DELETE', uri, status_code=204)

            res = h.delete(**test_params)

            assert res is None

    def test_get_list(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            filter, sort, pagination = Filters(), Sorts(), Pagination(offset=0, limit=10)
            test_data = {
                'objects': [
                    {'some_id': 444, 'foo': 'bar'},
                    {'some_id': 555, 'foo': 'baz'},
                ],
                'num_results': 2
            }
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'filters': filter,
                'sorts': sort,
                'pagination': pagination
            }
            check_data = test_data['objects'], test_data['num_results']
            uri = "{}/{}".format(self.test_config['name'], inflection.underscore(test_params['model_name']))
            a.register_uri('GET', uri, json=test_data)

            res = h.get_list(**test_params)

            assert res == check_data

    def test_get_list_params(self):
        a = requests_mock.Adapter()
        with self.obj as h:
            h.handle._session.mount('httpmock', a)
            filter, sort, pagination = Filters(field1__lt=14), Sorts('-field2'), Pagination(offset=30, limit=10)
            test_data = {
                'objects': [
                    {'some_id': 444, 'foo': 'bar'},
                    {'some_id': 555, 'foo': 'baz'},
                ],
                'num_results': 2
            }
            test_params = {
                'model_name': "SomeModel1",
                'pk': 'some_id',
                'filters': filter,
                'sorts': sort,
                'pagination': pagination
            }
            check_data = {
                'q': h.build_q(filter, sort, pagination),
                'results_per_page': pagination.limit
            }
            uri = "{}/{}".format(self.test_config['name'], inflection.underscore(test_params['model_name']))
            a.register_uri('GET', uri, json=test_data)

            h.get_list(**test_params)

            chunks = urlparse(a.last_request.url)
            query_vars = parse_qs(chunks.query)
            assert all(json.loads(query_vars[k][0]) == v for k, v in check_data.items())

    def test_start_returns_hammock_obj(self):
        res = self.obj.start()

        assert isinstance(res, Hammock)

    def test_start_passed_config_to_hammock_obj(self):
        with patch('hammock.Hammock') as p:
            res = self.obj.start()

            p.assert_called_once_with(**self.test_config)

    def test_start_pass_kwargs_to_created_hammock_object(self):
        test_data = {
            'verify': True,
            'headers': {'Content-Type': 'application/json'}
        }
        check_data = test_data
        check_data.update(self.test_config)

        with patch('hammock.Hammock') as p:
            res = self.obj.start(**test_data)

            p.assert_called_once_with(**check_data)

    def test_parse_response_http204(self):
        resp = Mock(status_code=204)

        res = self.obj.parse_response(resp)

        assert res is None

    def test_parse_response_json(self):
        test_data = {'foo': 'bar'}
        check_data = test_data
        resp = Mock(status_code=200)
        resp.json.return_value = test_data

        res = self.obj.parse_response(resp)

        assert res == check_data

    def test_parse_response_json_error(self):
        resp = Mock(status_code=200)
        resp.json.side_effect = json.JSONDecodeError('Json Error', 'doc', 123)

        with pytest.raises(AdapterError) as exc_info:
            self.obj.parse_response(resp)

        assert exc_info.value.args[1] is resp

    @pytest.mark.parametrize('status_code', range(400, 512))
    def test_parse_response_4xx_5xx(self, status_code):
        resp = Mock(status_code=status_code)

        with pytest.raises(AdapterError) as exc_info:
            self.obj.parse_response(resp)

        assert exc_info.value.args[1] is resp

    def test_build_query_params(self):
        test_params = (Filters(test_field1__lt=4), Sorts('test_field2'), Pagination(offset=123, limit=456))

        res = self.obj.build_query(*test_params)

        assert res.keys() == {'q', 'results_per_page'}

    @pytest.mark.parametrize('restrictions', (
        (Filters(test_field1__lt=4), Sorts('test_field2'), Pagination(offset=123, limit=456)),
        (Filters(), Sorts(), Pagination(offset=0, limit=456))
    ))
    def test_build_query_values(self, restrictions):
        res = self.obj.build_query(*restrictions)

        assert json.loads(res['q']) == self.obj.build_q(*restrictions) \
               and res['results_per_page'] == restrictions[2].limit

    def test_build_q_filters(self):
        test_params = (Filters(), Sorts(), Pagination(offset=123, limit=456))
        test_params[0].make(
            test_field1__eq=123,
            test_field2__ne=456,
            test_field2__gt=789,
            test_field2__lt=901,
            test_field3__in=(1, 2, '3'),
            test_field4__eq=None,
            test_field5__ne=None,
        )
        check_data = [{'and': [
            {'name': 'test_field1', 'op': 'eq', 'val': 123},
            {'name': 'test_field2', 'op': 'neq', 'val': 456},
            {'name': 'test_field2', 'op': 'gt', 'val': 789},
            {'name': 'test_field2', 'op': 'lt', 'val': 901},
            {'name': 'test_field3', 'op': 'in', 'val': (1, 2, '3')},
            {'name': 'test_field4', 'op': 'is_null'},
            {'name': 'test_field5', 'op': 'is_not_null'},
        ]}]

        res = self.obj.build_q(*test_params)

        assert all(i in check_data[0]['and'] for i in res['filters'][0]['and'])

    def test_build_q_sorts(self):
        test_params = (Filters(), Sorts(), Pagination(offset=123, limit=456))
        test_params[1].make('test_field1', '-test_field2')
        check_data = [
            {'field': 'test_field1', 'direction': 'asc'},
            {'field': 'test_field2', 'direction': 'desc'}
        ]

        res = self.obj.build_q(*test_params)

        assert res['order_by'] == check_data

    def test_build_q_pagination(self):
        test_params = (Filters(), Sorts(), Pagination(offset=123, limit=456))
        check_data = {'offset': 123, 'limit': 456}

        res = self.obj.build_q(*test_params)

        assert res['offset'] == check_data['offset'] and 'limit' not in res

    def test_build_q_error_on_filter_has_wrong_op_and_null_value(self):
        test_params = (Filters(), Sorts(), Pagination(offset=123, limit=456))
        test_params[0].make(
            test_field1__gt=None,
            test_field2__lt=None,
            test_field3__in=None,
        )

        with pytest.raises(AdapterError):
            res = self.obj.build_q(*test_params)

    def test_jsonify_body_returns_bytes_type(self):
        test_data = {
            'key1': 'key2',
            'ключ1': 'значение1',
            'key2': {'key21': 'value21'},
            'key3': ['value31', 'value32']
        }
        check_data = json.dumps(test_data)

        res = self.obj.jsonify_body(test_data)

        assert res == bytes(check_data, 'utf-8') and type(res) == bytes

    @pytest.mark.parametrize('offset', (0, 45))
    def test_get_total_count(self, offset):
        test_data = {
            'objects': [{}, {}, {}, {}],
            'num_results': 4
        }
        pagination = Pagination(offset=offset, limit=10)
        check_data = test_data['num_results'] + pagination.offset

        res = self.obj.get_total_count(test_data, pagination)

        assert res == check_data

    def test_get_total_count_return_zero_on_zero_objects(self):
        test_data = {
            'objects': [],
            'num_results': 0
        }
        pagination = Pagination(offset=10, limit=10)

        res = self.obj.get_total_count(test_data, pagination)

        assert res == 0

    def test_get_total_count_return_num_results_if_offset_is_none(self):
        test_data = {
            'objects': [{}, {}, {}, {}],
            'num_results': 4
        }
        test_restrictions = Pagination(offset=None, limit=10)
        check_data = test_data['num_results']

        res = self.obj.get_total_count(test_data, test_restrictions)

        assert res == check_data
