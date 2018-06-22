import wrapt
from itsdangerous import json


class JsonDict(wrapt.ObjectProxy):
    """
    Acts as builtin dict, but can also be initialized with serialized JSON string, which deserialized automatically.
    String representation result of object is an automatically serialized JSON string from current dict data.
    """
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            obj = dict(**json.loads(args[0]))
        else:
            obj = dict(*args, **kwargs)
        super().__init__(obj)

    def __repr__(self):
        return json.dumps(self.__wrapped__, ensure_ascii=False)

    def __str__(self):
        return self.__repr__()
