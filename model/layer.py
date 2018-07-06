from importlib import import_module
import sys


class BaseLayer(object):
    """
    Base class for implementation layer. Technically it is a factory that produces `ModelImpl` objects for given
    `Model` class. Each layer must contain one class derived from this one.

    Minimal layer class can be empty. All implementation classes are searched for by name in the layer's module
    namespace by concatenating 'Impl' to a model class name. Thus, all modules with implementation classes must be
    imported to the layer's module. E.g. if we have model named `Color` then 'ColorImpl` class will be searched for
    in the layer namespace.
    """
    @classmethod
    def get_impl(cls, model_cls):
        """
        Search and return for ModelImpl class for given Model. Returns None if Impl class was not found
        :param model_cls: Concrete Model class
        :return: implementation class or None
        """
        impl_name = cls.get_impl_name(model_cls)

        try:
            project_module = sys.modules[cls.__module__]
            impl_class = getattr(project_module, impl_name)

        except AttributeError:
            return None

        return impl_class

    @classmethod
    def get_impl_name(cls, model_cls) -> str:
        return model_cls.__name__ + 'Impl'


Layer = BaseLayer

__all__ = ['Layer']
