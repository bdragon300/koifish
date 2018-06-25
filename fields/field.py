from copy import copy, deepcopy
from enum import Enum
from bidict import bidict


class Field(object):
    """Model field class"""
    @property
    def field_type(self):
        """Type that field have. Used for type control and type cast. Read-only property"""
        return self._field_type

    @property
    def name(self):
        """Field name. Read-only property"""
        return self._name

    @property
    def required(self):
        """Is this field is required to have a value. Read-only property"""
        return self._required

    @property
    def tags(self):
        """Tags associated with field"""
        return self._tags

    @property
    def get_callback(self):
        """Callback used to obtain field value"""
        return self._get_callback

    @property
    def save_callback(self):
        """Callback used to save field value"""
        return self._save_callback

    @property
    def val(self):
        """Field value"""
        return self._do_encode(self._field_type, self._raw_val)

    @val.setter
    def val(self, value):
        if value is None:
            self._raw_val = None
        else:
            self._raw_val = self._do_decode(self._field_type, value)

    @property
    def raw(self):
        """Raw field value without typing"""
        return self._raw_val

    @raw.setter
    def raw(self, value):
        self._raw_val = value

    def __init__(self, **kwargs):
        """
        :param field_type: Optional. Type of value. Builtin types, enum.Enum are allowed
        :param required: Optional. If True then this field must have value
        :param tags: Optional. Iterable with any tags you want to assign with the field
        :param get_callback: Optional. Callback used to obtain field value, called after model data was obtained.
        :param save_callback: Optional. Callback used to save field value, called before model data will be saved.
        """
        self._set_field_type(kwargs.get('field_type'))
        self._required = kwargs.get('required', False)
        self._tags = frozenset(kwargs.get('tags', ()))
        self._raw_val = None
        self._name = kwargs.get('_name')

        self._get_callback = kwargs.get('get_callback')
        self._save_callback = kwargs.get('save_callback')

    def __repr__(self):
        return "<{} '{}'> = {}".format(self.__class__.__name__, self._name, self._raw_val)

    def __eq__(self, other):
        raise TypeError('Cannot compare Field objects, compare their values instead')

    def __ne__(self, other):
        raise TypeError('Cannot compare Field objects, compare their values instead')

    def _set_field_type(self, field_type):
        self._field_type = field_type
        self._enum_mapping = None

        # list, values of enum items counts from zero
        if isinstance(field_type, list):
            self._enum_mapping = bidict({field_type[x]: x for x in range(len(field_type))})

        # dict, enum items and their values are in dict
        elif isinstance(field_type, dict):
            self._enum_mapping = bidict(field_type)

        # enum.Enum, enum items and their values are in Enum class
        elif isinstance(field_type, type) and issubclass(field_type, Enum):
            self._enum_mapping = bidict({x: y.value for x,y in field_type.__members__.items()})

        if self._enum_mapping:
            self._do_encode = lambda t, v: self._enum_mapping.inv(v)
            self._do_decode = lambda t, v: self._enum_mapping[v]
        elif self._field_type is not None:
            self._do_encode = lambda t, v: v
            self._do_decode = lambda t, v: t(v)
        else:
            self._do_encode = lambda t, v: v
            self._do_decode = lambda t, v: v

    __slots__ = ('_field_type', '_name', '_required', '_tags', '_get_callback', '_save_callback', '_raw_val',
                 '_do_decode', '_do_encode', '_enum_mapping')