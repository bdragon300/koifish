from copy import deepcopy, copy

class Slotinit(object):
    """
    Class allows to set slots value from constructor kwargs. If slot name is absent in kwargs then it can be optionally
    set to default value.

    Example:
        class Car(Slotinit):
            __slots__ = ('color', 'engine_power', 'bodywork_type')
            _default_slot_values = {'color': 'black', 'bodywork_type': 'sedan'}

        my_car = Car(color='blue', engine_power='100hp')  # color='blue', engine_power='100hp', bodywork_type='sedan'
    """

    defaults = {}
    __slots__ = ()

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            if slot in kwargs:
                setattr(self, slot, kwargs[slot])
            elif slot in self.defaults:
                setattr(self, slot, self.defaults[slot])


class DeepcopySlotMixin:
    """Adds ability to deep copying all slots of the class and its ancestors"""
    def __deepcopy__(self, memo):
        obj = copy(self)
        self_id = id(self)
        copied = memo.get(self_id)

        if copied is None:
            for slots in (getattr(cls, '__slots__', []) for cls in type(self).__mro__):
                for slot in slots:
                    try:
                        setattr(obj, slot, deepcopy(getattr(self, slot), memo))
                    except AttributeError:
                        pass  # Skip slot if it was not set in self
            memo[self_id] = copied

        return obj
