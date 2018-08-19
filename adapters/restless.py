import hammock
import inflection
import requests
from itsdangerous import json

from exc import AdapterError
from layer import Adapter
from model.restrictions import FilterOperator, SortOperator


class RestlessAdapter(Adapter):
    """
    This adapter abstracts interacting with REST API provided by Flask-Restless service
    
    Config dict treats as Hammock initial parameters. Since Hammock kwargs actually passed to requests.session
    thus config dict contains both Hammock and session params:

        {
            # Hammock parameters
            'name': 'http://example.com/api',
            'append_slash': True,
            'headers': {'Content-Type': 'application/json'},
            'proxies': {'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'},

            # requests.session parameters
            'params': {...},
            'verify': True,
            ...
        }
    
    Using as context manager:
        >>> config_dict = {'name': 'http://www.example.com/api/client'}
        >>> with RestlessAdapter(config=config_dict) as example_com:
        >>>    res = example_com.get('id', 123, headers={'Content-Type': 'application/json'})
        >>>    print(type(res))
        <class 'dict'>

    Using as object:
        >>> config_dict = {'name': 'http://www.example.com/api/client'}
        >>> example_com = RestlessAdapter(config=config_dict).start()
        >>> res = example_com.get('id', 123, headers={'Content-Type': 'application/json'})
        >>> print(type(res))
        <class 'dict'>
        >>> example_com.terminate()

    Of course you may use hammock object directly:
        >>> config_dict = {'name': 'http://www.example.com/api'}
        >>> with RestlessAdapter(config=config_dict) as example_com:
        >>>    h = example_com.handle
        >>>    ans = h.client(123).GET()
        >>>    res = example_com.parse_response(ans)
        >>>    print(type(res))
        <class 'dict'>

    """

    restless_filters = {
        FilterOperator.Equal: 'eq',
        FilterOperator.NotEqual: 'neq',
        FilterOperator.GreaterThan: 'gt',
        FilterOperator.LessThan: 'lt',
        FilterOperator.In: 'in'
    }

    restless_sorts = {
        SortOperator.Ascending: 'asc',
        SortOperator.Descending: 'desc'
    }

    def __init__(self, **kwargs):
        if 'config' not in kwargs:
            kwargs['config'] = {}
        if 'headers' not in kwargs['config']:
            kwargs['config']['headers'] = {'Content-Type': 'application/json'}

        super().__init__(**kwargs)

    def get(self, model_name, pk, pk_val, *args, **kwargs):
        if not self.handle:
            self.handle = self.start()

        tbl = inflection.underscore(model_name)
        robj = getattr(self.handle, tbl)(pk_val).GET(*args, **kwargs)  # GET http://base_url/tbl/pk_val
        return self.parse_response(robj)

    def create(self, model_name, pk, data, *args, **kwargs):
        if not self.handle:
            self.handle = self.start()

        tbl = inflection.underscore(model_name)
        jdata = self.jsonify_body(data)
        robj = getattr(self.handle, tbl).POST(data=jdata, *args, **kwargs)  # POST http://base_url/tbl
        res = self.parse_response(robj)

        pk_val = res.get(pk)
        if pk_val is None:
            res[pk] = res.get(pk)

        return res

    def update(self, model_name, pk, pk_val, data, *args, **kwargs):
        if not self.handle:
            self.handle = self.start()

        tbl = inflection.underscore(model_name)
        jdata = self.jsonify_body(data)
        robj = getattr(self.handle, tbl)(pk_val).PUT(data=jdata, *args, **kwargs)  # PUT http://base_url/tbl/pk_val
        res = self.parse_response(robj)

        return res

    def delete(self, model_name, pk, pk_val, *args, **kwargs):
        if not self.handle:
            self.handle = self.start()

        tbl = inflection.underscore(model_name)
        robj = getattr(self.handle, tbl)(pk_val).DELETE(*args, **kwargs)  # DELETE http://base_url/tbl/pk_val
        return self.parse_response(robj)

    def get_list(self, model_name, pk, filters, sorts, pagination, *args, **kwargs):
        if not self.handle:
            self.handle = self.start()

        tbl = inflection.underscore(model_name)
        # GET http://base_url/tbl?params
        robj = getattr(self.handle, tbl).GET(params=self.build_query(filters, sorts, pagination), *args, **kwargs)
        res = self.parse_response(robj)
        return res.get('objects'), self.get_total_count(res, pagination)

    def start(self, **kwargs):
        params = self.config
        params.update(kwargs)
        return hammock.Hammock(**params)

    def terminate(self, **kwargs):
        pass

    def parse_response(self, response: requests.Response):
        """
        Parse http response and transform it to dict/list representation
        :param response:
        :raises AdapterError: HTTP error or error while parsing json
        :return: deserialized response
        """
        ans = None

        if response.status_code != 204:
            try:
                ans = response.json()
            except ValueError as e:
                msg = 'Unable to parse JSON response'
                raise AdapterError(msg, response) from e

        if response.status_code >= 400:
            raise AdapterError('HTTP error {}'.format(response.status_code), response)

        return ans

    @staticmethod
    def build_query(filters, sorts, pagination) -> dict:
        """
        Returns dict with url parameters for listing operations
        :param filters: Filters object
        :param sorts: Sorts object
        :param pagination: Pagination object
        :return: url params dict
        """
        res = {
            'q': RestlessAdapter.jsonify_restrictions(filters, sorts, pagination),
            'results_per_page': pagination.limit
        }
        return res

    @staticmethod
    def jsonify_restrictions(filters, sorts, pagination):  # NOQA
        """
        :param filters:
        :param sorts:
        :param pagination:
        :return:
        """
        return json.dumps(RestlessAdapter.build_q(filters, sorts, pagination))

    @staticmethod
    def build_q(filters, sorts, pagination) -> dict:
        """
        Build 'q' url param dict from restrictions
        :param filters: Filters object
        :param sorts: Sorts object
        :param pagination: Pagination object
        :raises AdapterError:
        :return:
        """
        def to_filter(f):
            if f.val is None:
                # TODO: 'in' operation
                if f.op == FilterOperator.Equal:
                    op = 'is_null'
                elif f.op == FilterOperator.NotEqual:
                    op = 'is_not_null'
                else:
                    raise AdapterError("Cannot apply '{}' operation to NULL in filter on field '{}'".format(
                        f.op, f.field_name
                    ))
                return {
                    'name': f.field_name,
                    'op': op,
                }
            else:
                return {
                    'name': f.field_name,
                    'op': RestlessAdapter.restless_filters[f.op],
                    'val': f.val
                }

        def to_sort(s):
            return {
                'field': s.field_name,
                'direction': RestlessAdapter.restless_sorts[s.direction]
            }

        filter_expr = [to_filter(f) for i in filters for f in filters[i]]
        sorts = [to_sort(s) for i in sorts for s in sorts[i]]
        offset = pagination.offset
        # limit = pagination.limit  # `results_per_page` url param used instead

        res = {}
        if filter_expr: res['filters'] = [{'and': filter_expr}]
        if sorts: res['order_by'] = sorts
        if offset: res['offset'] = offset
        return res

    @staticmethod
    def jsonify_body(data) -> bytes:
        """
        Jsonify outgoing data
        :param data:
        :return: bytes string
        """
        return json.dumps(data).encode('utf8')  # type: bytes

    @staticmethod
    def get_total_count(response_data, pagination) -> int:
        """
        Calculates records total count based on Flask-Restless listing response and initial restrictions.

        Flask-Restless returns objects count remains after offset value instead of total count. Thus, total
        is the sum of offset and remaining objects count ('num_results' response field).
        If passed offset is out of range then return 0.
        :param response_data: listing response dict
        :param pagination: Pagination object
        :return:
        """
        if response_data['num_results'] == 0:
            return 0
        elif pagination.offset is not None:
            return response_data['num_results'] + pagination.offset
        else:
            return response_data['num_results']


__all__ = ('RestlessAdapter', )
