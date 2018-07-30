import booby
import booby.errors

from cacher import MemoryCacher
from exc import ModelError, NotFoundError, ValidationError
from .queryset import QuerySet


class BaseModel(booby.Model):
    # TODO: make __copy__
    """
    Base class for user-defined ORM Models. Built on top of `booby` model, so see its docs.

    Model interface is similar to Django-ORM, but with some additional features, such as layers or model load methods.
    Model represents one record with fixed fields accessible via dot.

    Each model object always bound with one Layer object. Layer typically is an methods bunch implements CRUD + list
    operations. The Model and the Layer classes follow the Bridge design pattern.

    User may specify the layer on Model object create. The default layer is used if it was not specified. Once layer
    specified, all operations, including list operations and foreign key following, use this layer. To use another
    layer user needs to create model with it.

    Model field can be virtual. Virtual field acts as other ones, but does not include in requests and does not read
    from incoming data. Thus virtual field is not intended for store. E.g. it may act as a flag to alternate model
    behavior, or it may be calculated dynamically to reflect some fact, etc. One-to-many foreign fields also treat as
    'virtual'.

    One of fields must defined as primary key.
    """

    # _default_layer = DefaultLayer
    _default_layer = None
    _validate_on_write = True
    _validate_on_read = False
    _search_impl_in_default_layer = True
    _request_limit = 10
    _cacher = MemoryCacher()

    _primary_key = None  # Primary key field name
    _request_fields = {}  # _fields' slice of fields that included in requests

    def __init__(self, _layer_class=None, **kwargs):
        """
        Constructor receives layer_class as the first positional param. Init fields values can be passed as kwargs.
        :param _layer_class: Optional. Layer class. If omitted then `_default_layer` will be used
        :raises: ModelError: if no primary_key field defined
        """
        self._deleted = False
        self._layer_class = _layer_class or self._default_layer

        cls = self.__class__

        # Get list with fields that include in requests
        if not cls._request_fields:
            cls._request_fields = \
                {k: v for k, v in self._fields.items() if not v.virtual}

        super().__init__(**kwargs)
        # self._fields = self.instantiate_fields(self)
        # TODO: instantiate ForeignField

        # Set primary key field name as class variable
        if not cls._primary_key:
            cls._primary_key = self._get_primary_key()

        self._impl_object = self._get_impl(self._layer_class)()

    @property
    def objects(self):
        """New empty QuerySet instance, that contains current model objects"""
        obj = QuerySet(
            self,
            cache=self._cacher.new_cache(),
            request_limit=self._request_limit
        )
        return obj

    @property
    def primary_key(self):
        """Primary key name"""
        return self._primary_key

    def load(self, **kwargs):
        """
        Fill out this model with record obtained by primary key. Receives only one kwarg with primary key name/value.

        Example:
            load(id=123)
            load(pk=123)
        :param kwargs: primary_key=value
        :raises: NotFoundError: record not found
        :return: self
        """
        (pk, pk_val) = self._get_pk_from_kwarg(**kwargs)

        self._data = {}
        data = self._get_record_by_pk(pk, pk_val)
        self._load_request_data(data)

        self._deleted = False

        # Raises ValidationError if validation failed
        if self._validate_on_read:
            self.validate()

        return self

    def get(self, **kwargs):
        """
        Return new model object with record data loaded by given primary key. Factory method `new_model` used to create
        returned object.

        Receives only one kwarg with primary key name/value.
        Example:
            get(id=123)
            get(pk=123)

        :param kwargs: primary_key=value
        :raises: NotFoundError: record not found
        :return: new model object
        """
        pk, pk_val = self._get_pk_from_kwarg(**kwargs)
        data = self._get_record_by_pk(pk, pk_val)

        new_obj = self.new_model(data)
        new_obj._load_request_data(data)

        # Raises ValidationError if validation failed
        if new_obj._validate_on_read:
            new_obj.validate()

        return new_obj

    def save(self):
        """
        Save the model
        :return: self
        """
        if self._deleted:
            raise ModelError('Cannot save already deleted record')

        # Raises ValidationError if validation failed
        if self._validate_on_write:
            self.validate()

        data = {k: self._data.get(v) for k, v in self._request_fields.items()}

        if self[self._primary_key] is None:
            res = self._impl_object.create(data)
        else:
            res = self._impl_object.update(data)

        # Update model with returned data if any
        # Reduce result dict according with fields since it may contain extra keys
        # Don't use `update` method since the data has a mapped value for fields with enums, while those method sets
        #  value as enum value
        if res is not None:
            res = {self._request_fields[k]: v for k, v in res.items() if k in self._request_fields}
            self._data = res

        return self

    def delete(self):
        """
        Delete record. After deletion the model becomes read-only.
        :return: self
        """
        if self._deleted:
            raise ModelError('Record is already deleted')

        pk = self._primary_key
        pk_val = self._data[self._fields[pk]]

        if pk_val is None:
            raise ModelError('Primary key is not set')

        self._impl_object.delete(pk, pk_val)

        self._deleted = True

        return self

    def get_list(self, restrictions) -> list:
        """
        Method used by RequestSet to obtain list of records. Does not change internal state of model.
        :param restrictions: RequestSetRestrictions
        :return: list with record dicts
        """
        return self._impl_object.get_list(restrictions)

    def update(self, *args, **kwargs):
        """This method updates the `model` fields values with the given `dict`.
        The model can be updated passing a dict object or keyword arguments,
        like the Python's builtin :py:func:`dict.update`.
        """
        super().update(*args, **kwargs)
        self._deleted = False

    def new_model(self, data):
        """
        Factory method that creates new model object. Method typically used to return right model object during
        iteration over QuerySet.

        Returned object doesn't filled out by given `data`. This parameter typically used only to determine a class
        to produce, for instance.

        By default method returns simply new empty object of current class. User can alter this behavior in user models,
        for instance, when there is needed to implement polymorphism in model hierarchy based on response data.

        :param data: record dict
        :return: Empty model object
        """
        obj = self.__class__(self._layer_class)

        return obj

    def validate(self):
        try:
            super().validate()
        except booby.errors.ValidationError as e:
            raise ValidationError from e

    def _get_pk_from_kwarg(self, **kwargs):
        """
        Retrieve primary key from function kwargs
        :param kwargs:
        :return: (pk, pk_val)
        """
        if len(kwargs) != 1:
            raise TypeError("Function takes only 1 keyword argument")

        pk = list(kwargs)[0]
        pk_val = kwargs[pk]
        if 'pk' in kwargs:
            pk = self._primary_key
        if pk != self._primary_key:
            raise ValueError("{} is not primary key field".format(pk))
        if pk_val is None:
            raise ValueError("None value was passed as primary key".format(pk))

        return pk, pk_val

    def _get_record_by_pk(self, pk, pk_val) -> dict:
        """
        Obtain record by given primary key
        :param pk: primary key name
        :param pk_val: primary key value
        :return: record dict
        """
        data = self._impl_object.get(pk, pk_val)  # type: dict
        if not data:
            raise NotFoundError("Cannot find record with {}='{}'".format(pk, pk_val))

        return data

    def _load_request_data(self, data):
        """Load given record dict into model request fields"""
        # Reduce result dict according with fields since it may contain extra keys
        # Don't use `update` method since the data has a mapped value for fields with enums, while those method sets
        #  value as enum value
        res = {self._request_fields[k]: v for k, v in data.items() if k in self._request_fields}
        self._data = res

    # @staticmethod
    # def instantiate_fields(obj):
    #     """
    #     Instantiates field objects from defined fields
    #     :param obj: Entity object
    #     :return: {field_name: Field obj}
    #     """
    #     cls = obj.__class__
    #     fields = {}
    #
    #     # Instantiate primary key field firstly
    #     field_names = [f for f in dir(cls) if not f.startswith('_') and f != cls.primary_key]
    #     field_names.insert(0, cls.primary_key)
    #
    #     for i in field_names:
    #         class_field = getattr(cls, i)
    #         if isinstance(class_field, Field):
    #             if obj.dummy:
    #                 fields[i] = None
    #                 continue
    #             else:
    #                 fields[i] = copy(class_field)
    #                 fields[i].name = i
    #         else:
    #             continue
    #
    #         # ForeignField.related_entity specified only
    #         if isinstance(class_field, ForeignField):
    #             if class_field.request_set:
    #                 fields[i].request_set = class_field.request_set
    #             else:
    #                 if type(class_field.related_entity) != str:
    #                     raise TypeError("field {}: related_entity is not string".format(class_field))
    #
    #                 # Try to instantiate related_entity
    #                 import entities
    #                 # TODO: search dummy in the module contained self first
    #                 dummy_entity = getattr(entities, class_field.related_entity)
    #                 if dummy_entity is None:
    #                     raise TypeError("Unable to find class {}.{}".format('entities', class_field.related_entity))
    #
    #                 fields[i].request_set = dummy_entity(obj.layer_factory, dummy=True).objects
    #
    #         # OneToMany field needs to be set entity primary key obj
    #         if isinstance(class_field, OneToManyField):
    #             fields[i].primary_key_obj = weakref.proxy(fields[cls.primary_key])
    #
    #     if not fields:
    #         raise TypeError("{} has not defined fields".format(cls.__name__))
    #
    #     return fields

    def _get_primary_key(self):
        """
        Return primary key field name
        :raises ModelError: 0 or >1 primary key defined in model
        :return: Field object name
        """
        pk = list(k for k, v in self._fields.items() if v.primary_key)
        if len(pk) == 0:
            raise ModelError("No primary key in model '{}'".format(self.__class__.__name__))
        elif len(pk) > 1:
            raise ModelError("More than one field is primary key in model '{}'".format(self.__class__.__name__))
        return pk[0]

    def _get_impl(self, layer_class):
        """
        Try to get implementation class from given layer. If not found try to find it in default one. If not found again
        raise exception
        :param layer_class: layer class
        :raises ModelError: implementation class not found
        :return: implementation class
        """
        cls = self.__class__
        iobj = layer_class.get_impl(cls)
        if iobj is None and self._search_impl_in_default_layer:
            iobj = self._default_layer.get_impl(cls)

        if iobj is None:
            raise ModelError("Cannot find implementation for '{}' in layers [{}, {}]"
                             .format(cls.__name__, layer_class.__name__, self._default_layer.__name__))

        return iobj


Model = BaseModel

__all__ = ['Model']
