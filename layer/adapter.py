from abc import ABCMeta, abstractmethod


class BaseAdapter(metaclass=ABCMeta):
    """Base class for service adapters"""

    def __init__(self, **kwargs):
        """
        :param config: Optional config dict
        :param filters: Optional Filters object
        :param sorts: Optional Sorts object
        :param pagination: Optional Pagination object
        """
        self.init_params = kwargs

        self.config = kwargs.get('config')
        self.filters = kwargs.get('filters')
        self.sorts = kwargs.get('sorts')
        self.pagination = kwargs.get('pagination')
        self.handle = kwargs.get('handle')

    def __enter__(self):
        self.handle = self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: catch all exceptions and turn out to AdapterError
        return self.terminate()

    @abstractmethod
    def start(self, *args, **kwargs):
        """
        Opens file/connection/session/etc with which the concrete adapter works
        :return: handle
        """
        pass

    @abstractmethod
    def terminate(self, *args, **kwargs):
        """
        Terminate opened handle
        :param handle:
        :return:
        """
        pass

    @abstractmethod
    def parse_response(self, response): ...

    @abstractmethod
    def get(self, model_name, pk, pk_val, *args, **kwargs) -> dict: ...

    @abstractmethod
    def create(self, model_name, pk, data, *args, **kwargs) -> dict: ...

    @abstractmethod
    def update(self, model_name, pk, pk_val, data, *args, **kwargs) -> dict: ...

    @abstractmethod
    def delete(self, model_name, pk, pk_val, *args, **kwargs) -> dict: ...

    @abstractmethod
    def get_list(self, model_name, pk, filters, sorts, pagination, *args, **kwargs) -> (list, int): ...


Adapter = BaseAdapter
