from abc import ABCMeta, abstractmethod

import inflection

from exc import ModelError
from fields import Field
from layer.impl import ListResponse


class ForeignRel(Field, metaclass=ABCMeta):
    def __init__(self, to, on_delete, to_field=None, *validators, **kwargs):
        """
        Optional `to_field` parameter contains name of field in the related model used for
        relation. If omitted, then name automatically builds as following:
        * The primary key for Many-To-One relations
        * Current lowercase model name plus 'id' for One-To-Many. E.g. for Customer.orders will be 'customer_id'

        :param to: Related model class name
        :param on_delete:
        :param to_field: Optional name of related model field
        """
        super().__init__(self, *validators, **kwargs)

        self._to = to
        self._on_delete = on_delete
        self._to_field = to_field
        self._to_model_cached = None
        self._my_model_cls = None

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, val):
        self._to = val

    @property
    def to_field(self):
        if self._to_field is None:
            f = self._get_to_field(self._related)
        else:
            f = self._to_field

        if not hasattr(self._related, f):
            raise ModelError("'{}' field does not exist in model '{}'".format(
                f, self._related.__name__
            ))

        return f

    @to_field.setter
    def to_field(self, val):
        self._to_field = val

    @property
    def _related(self):
        """Related model class"""
        if self._my_model_cls is None:
            raise ModelError("Model not initialized")

        if self._to_model_cached is None:
            mdl_cls = self._my_model_cls._meta.models.get(self._to) if isinstance(self._to, str) else self._to
            if mdl_cls is not None:
                self._to_model_cached = mdl_cls
            else:
                raise ModelError("Model '{}' related from '{}' is not found".format(self._to, self._my_model_cls.__name__))

        return self._to_model_cached

    def init(self, model_cls):
        """
        Initialize object after creating. Called by model after its class initialization.
        :param model_cls: Containing model class
        :return:
        """
        self._my_model_cls = model_cls

        if isinstance(model_cls, str):
            raise RuntimeError


    @abstractmethod
    def _get_to_field(self, to_model_cls): ...


class ManyToOneField(ForeignRel):
    def __get__(self, instance, owner):
        if instance is not None:
            robj = self._related(instance._layer_class)  # FIXME: make layer_class as property in Model
            lval = super().__get__(instance, owner)
            if lval is None:
                return None

            f = {self.to_field + '__eq': lval}
            qs = robj.objects.filter(**f)

            try:
                return qs[0]
            except IndexError:
                return None

        return self

    def __set__(self, instance, value):
        # FIXME: pretty bad way to determine if it's a Model, I need to think up smth better. I don't wanna import Model
        if hasattr(value, 'primary_key'):
            rval = getattr(value, self.to_field)
        else:
            rval = value

        super().__set__(instance, rval)

    def _get_to_field(self, to_model_cls):
        return to_model_cls.primary_key


ForeignKey = ManyToOneField


class OneToManyField(ForeignRel):
    def __init__(self, to, on_delete, to_field=None, *validators, **kwargs):
        super().__init__(to, on_delete, to_field, virtual=True, *validators, **kwargs)

    def __get__(self, instance, owner):
        if instance is not None:
            robj = self._related(instance._layer_class)  # FIXME: make layer_class as property in Model
            lval = instance[instance.primary_key]

            qs = robj.objects
            if lval is not None:
                f = {self.to_field + '__eq': lval}
                qs = qs.filter(**f)
            else:
                # FIXME: this is a dirty hack, EmptyQuerySet needed to be implement
                x = ListResponse()
                x.total_count = 0
                qs._fetch_page = lambda *a, **kw: x
            return qs

        return self

    def __set__(self, instance, value):
        raise AttributeError('OneToMany field is read-only')

    def _get_to_field(self, to_model_cls):
        if self._my_model_cls is None:
            raise ModelError("Model not initialized")

        our_name = inflection.underscore(self._my_model_cls.__name__)
        our_pk = 'id'

        return our_name + '_' + our_pk


__all__ = ('ForeignKey', 'ManyToOneField', 'OneToManyField')
