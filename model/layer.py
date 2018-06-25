import collections


class ListResponse(collections.UserList):  # NOQA
    """
    List with additional attributes. Purpose is to hold response from Impl.get_list operation
    Additional attributes defined in slots
    """
    __slots__ = (
        'total_count',  # Total selection objects count
    )


class BaseLayer:
    """
    Implementation layer with data manipulating methods
    """
    def get(self, pk, pk_value, **kwargs):
        """
        Retrieve one record by primary key
        :param pk: primary key name
        :param pk_value: primary key value
        :return: record dict
        """
        raise NotImplementedError

    def create(self, data, **kwargs):
        """
        Create new record with data from kwargs. Returned dict (if any) is treated as created record
        :param data: record dict
        :return: None or dict with created record
        """
        raise NotImplementedError

    def update(self, pk, pk_value, data, **kwargs):
        """
        Update record with given primary key. Returned dict (if any) is treated as updated record
        :param pk: primary key name
        :param pk_value: primary key value
        :param data: record dict
        :return: None or dict with updated record
        """
        raise NotImplementedError

    def delete(self, pk, pk_val, **kwargs):
        """
        Delete record by primary key
        :param pk: primary key name
        :param pk_val: primary key value
        :return:
        """
        raise NotImplementedError

    def get_list(self, restrictions, **kwargs) -> ListResponse:
        """
        Get records list using given restrictions
        :param restrictions: restrictions object
        :return: ListResponse object with records
        """
        raise NotImplementedError
