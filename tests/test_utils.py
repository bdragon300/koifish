import pytest
from utils import Slotinit


class SlotinitStub(Slotinit):
    __slots__ = ('slot1', 'slot2', 'slot3', 'slot4')
    defaults = {'slot2': 'test_value2', 'slot3': 'test_value3'}


class TestSlotinit:
    @pytest.mark.parametrize('slotname', SlotinitStub.__slots__)
    def test_init_slot(self, slotname):
        test_value = 'test_value'
        test_data = {slotname: test_value}
        obj = SlotinitStub(**test_data)

        assert getattr(obj, slotname) == test_value

    @pytest.mark.parametrize('slotname,slotvalue', SlotinitStub.defaults.items())
    def test_set_default_value(self, slotname, slotvalue):
        obj = SlotinitStub()

        assert getattr(obj, slotname) == slotvalue

    @pytest.mark.parametrize('slotname', set(SlotinitStub.__slots__) - SlotinitStub.defaults.keys())
    def test_absent_slots_are_not_initilized(self, slotname):
        obj = SlotinitStub()

        with pytest.raises(AttributeError):
            getattr(obj, slotname)
