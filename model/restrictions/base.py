from collections import UserDict


class BaseRestriction:
    """Base class for concrete restriction type classes"""
    __slots__ = ()

    def __init__(self, **kwargs):
        """
        Initializes class slots from kwargs. All slots in kwargs are required.
        :param kwargs: slot=value, ...
        :raises TypeError: some slots are missing in kwargs
        """
        for slot in self.__slots__:
            if slot in kwargs:
                setattr(self, slot, kwargs[slot])
            else:
                raise TypeError("Constructor missing slot '{}' in keyword arguments".format(slot))

    def __eq__(self, other):
        for slot in self.__slots__:
            if getattr(self, slot) != getattr(other, slot):
                return False
        return True

    def __ne__(self, other):
        return not(self.__eq__(other))

    def __hash__(self):
        return hash(':'.join(str(getattr(self, x)) for x in self.__slots__))

    def __str__(self):
        return '{}: <{}>'.format(
            self.__class__.__name__, ', '.join(s + ':' + str(getattr(self, s)) for s in self.__slots__)
        )

    def __repr__(self):
        return self.__str__()


class BaseRestrictionContainer(UserDict):
    """
    Base restrictions container, acts as dict. Each item value is a `set` with concrete restriction objects.
    The class has methods for adding new restrictions into container that must be overridden in derived classes.
    """
    def make(self, *args, **kwargs):
        """Clear container and build new restriction objects"""
        raise NotImplementedError()

    def apply(self, *args, **kwargs):
        """Add new restrictions to the existing ones"""
        raise NotImplementedError()
