import pytest
from utils import DeepcopySlotMixin
from copy import deepcopy


class DeepcopyStub(DeepcopySlotMixin):
    __slots__ = ('slot1', )


class DeepcopyStub2(DeepcopyStub):
    __slots__ = ('slot2', )


class TestSlotDeepcopy:
    def test_deepcopy(self):
        obj = DeepcopyStub2()
        obj.slot1 = []
        obj.slot2 = []

        res = deepcopy(obj)

        assert obj.slot1 is not res.slot1 and obj.slot2 is not res.slot2
