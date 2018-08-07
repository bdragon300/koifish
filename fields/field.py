import collections
from enum import Enum

import booby.fields as bfields
import six
from bidict import bidict
from booby import decoders as builtin_decoders
from booby import encoders as builtin_encoders
from booby import validators as builtin_validators


class Field(bfields.Field):
    """
    Model field class

    :param default: This field `default`'s value.

        If passed a callable object then uses its return value as the
        field's default. This is particularly useful when working with
        `mutable objects <http://effbot.org/zone/default-values.htm>`_.

        If `default` is a callable it can optionaly receive the owner
        `model` instance as its first positional argument.

    :param required: If `True` this field value should not be `None`.
    :param primary_key: `True` if this field is primary key in model. Default is `False`
    :param virtual: `True` means this field will not be included in data exchange. Default is `False`
    :param choices: Possible field values with values mapping (`dict` or `enum.Enum`) or without mapping (`list`).

        A `list` parameter simply sets values which this field can have. `dict` or `enum.Enum` parameters also set
        mapping between field value and real model value. This behavior is similar to enums. Type validation applies to
        a real value type.
        E.g.:

        class Car(Model):
            color = Integer(choices={'BLUE': 0, 'RED': 1})

        car.color = 'RED'
        print(car._data[car._fields['color']])  # real data stored in model

        1

    :param name: Specify an alternate key name to use when decoding and encoding.
    :param description: Optional description.
    :param read_only: If `True`, the value is treated normally in decoding but omitted during encoding.
    :param \*validators: A list of field :mod:`validators` as positional arguments.
    """
    def __init__(self, *validators, **kwargs):
        self.options = kwargs

        self.default = kwargs.get('default')
        self.description = kwargs.get('description', '')
        self.required = kwargs.get('required', False)
        self.choices = kwargs.get('choices', [])
        self.primary_key = kwargs.get('primary_key', False)
        self.virtual = kwargs.get('virtual', False)

        # Setup field validators
        self.validators = []
        self._bi_mapping = None

        if self.required:
            self.validators.append(builtin_validators.Required())

        if self.choices:
            self._bi_mapping = self._init_bi_mapping(self.choices)
            if self._bi_mapping:
                self.validators = list(filter(lambda x: isinstance(x, builtin_validators.In), self.validators))
                self.validators.append(builtin_validators.In(list(self._bi_mapping.values())))
            else:
                self.validators.append(builtin_validators.In(list(self.choices)))

        self.validators.extend(validators)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        val = self._get_raw(instance, owner)

        if self._bi_mapping and val is not None:
            return self._bi_mapping.inv[val]
        else:
            return val

    def __set__(self, instance, value):
        if self._bi_mapping:
            value = self._bi_mapping[value]

        self._set_raw(instance, value)

    @staticmethod
    def _init_bi_mapping(choices):
        # dict, enum items and their values are in dict
        if isinstance(choices, dict):
            return bidict(choices)

        # enum.Enum, enum items and their values are in Enum class
        elif isinstance(choices, type) and issubclass(choices, Enum):
            return bidict({x: y.value for x, y in choices.__members__.items()})

        else:
            return None

    def _get_raw(self, instance, owner):
        """Get raw field value without using choices mapping"""
        return super().__get__(instance, owner)

    def _set_raw(self, instance, value):
        """Set raw field value without using choices mapping"""
        super().__set__(instance, value)


class StringField(Field):
    """:class:`Field` subclass with builtin `string` validation."""

    def __init__(self, *args, **kwargs):
        super(StringField, self).__init__(builtin_validators.String(), *args, **kwargs)

    @property
    def field_type(self):
        return six.string_types


class IntegerField(Field):
    """:class:`Field` subclass with builtin `integer` validation."""

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(builtin_validators.Integer(), *args, **kwargs)

    @property
    def field_type(self):
        return six.integer_types


class FloatField(Field):
    """:class:`Field` subclass with builtin `float` validation."""

    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__(builtin_validators.Float(), *args, **kwargs)

    @property
    def field_type(self):
        return float


class BooleanField(Field):
    """:class:`Field` subclass with builtin `bool` validation."""

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(builtin_validators.Boolean(), *args, **kwargs)

    @property
    def field_type(self):
        return bool


class EmbeddedField(Field):
    """:class:`Field` subclass with builtin embedded :class:`models.Model`
    validation.

    """

    def __init__(self, model, *args, **kwargs):
        kwargs.setdefault('encoders', []).append(builtin_encoders.Model())
        kwargs.setdefault('decoders', []).append(builtin_decoders.Model(model))

        super(EmbeddedField, self).__init__(builtin_validators.Model(model), *args, **kwargs)

        self.model = model

    def __set__(self, instance, value):
        if isinstance(value, collections.MutableMapping):
            value = self.model(**value)

        super(EmbeddedField, self).__set__(instance, value)


class EmailField(StringField):
    """:class:`Field` subclass with builtin `email` validation."""

    def __init__(self, *args, **kwargs):
        super(EmailField, self).__init__(builtin_validators.Email(), *args, **kwargs)


class URLField(StringField):
    """:class:`Field` subclass with builtin `URL` validation."""

    def __init__(self, *args, **kwargs):
        super(URLField, self).__init__(builtin_validators.URL(), *args, **kwargs)


class IPField(StringField):
    """:class:`Field` subclass with builtin `ip` validation."""

    def __init__(self, *args, **kwargs):
        super(IPField, self).__init__(builtin_validators.IP(), *args, **kwargs)


class URIField(StringField):
    """:class:`Field` subclass with builtin `URI` validation."""

    def __init__(self, *args, **kwargs):
        super(URIField, self).__init__(builtin_validators.URI(), *args, **kwargs)


class RawField(Field):
    """:class:`Field` raw input data"""

    def __init__(self, *args, **kwargs):
        super(RawField, self).__init__(*args, **kwargs)


class ListField(Field):
    """:class:`Field` subclass with builtin `list` validation
    and default value.

    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [])
        kwargs.setdefault('encoders', []).append(builtin_encoders.List())

        super(ListField, self).__init__(
            builtin_validators.List(*kwargs.get('inner_validators', [])),
            *args, **kwargs)

    @property
    def field_type(self):
        return list


class CollectionField(Field):
    """:class:`Field` subclass with builtin `list of` :class:`models.Model`
    validation, encoding and decoding.

    Example::

        class Token(Model):
            key = String()
            secret = String()

        class User(Model):
            tokens = Collection(Token)


        user = User({
            'tokens': [
                {
                    'key': 'xxx',
                    'secret': 'yyy'
                },
                {
                    'key': 'zzz',
                    'secret': 'xxx'
                },
            ]
        })

        user.tokens.append(Token(key='yyy', secret='xxx'))

    """

    def __init__(self, model, *args, **kwargs):
        kwargs.setdefault('default', [])

        kwargs.setdefault('encoders', []).append(builtin_encoders.Collection())
        kwargs.setdefault('decoders', []).append(builtin_decoders.Collection(model))
        super(CollectionField, self).__init__(builtin_validators.List(builtin_validators.Model(model)), *args, **kwargs)
        self.model = model

    def __set__(self, instance, value):
        if isinstance(value, collections.MutableSequence):
            value = self._resolve(value)

        super(CollectionField, self).__set__(instance, value)

    def _resolve(self, value):
        result = []
        for item in value:
            if isinstance(item, collections.MutableMapping):
                item = self.model(**item)
            result.append(item)
        return result
