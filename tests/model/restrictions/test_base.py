import pytest
from model.restrictions.base import BaseRestriction, BaseRestrictionContainer


class RestrictionStub(BaseRestriction):
    __slots__ = ('test_slot', )


class TestBaseRestriction:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.init_slots = {'test_slot': 'test_value'}
        self.obj = RestrictionStub(**self.init_slots)

    def test_init_slots(self):
        assert {k: getattr(self.obj, k) for k in self.obj.__slots__} == self.init_slots

    def test_error_on_slot_missing_in_kwargs(self):
        with pytest.raises(TypeError):
            obj = RestrictionStub()

    def test_eq(self):
        obj = RestrictionStub(**self.init_slots)

        assert obj == self.obj

    def test_ne(self):
        obj = RestrictionStub(test_slot='another_value')

        assert obj != self.obj

    def test_hashable(self):
        assert BaseRestriction.__hash__ is not None

    def test_hashes_are_different(self):
        obj = RestrictionStub(test_slot='another_value')

        assert hash(self.obj) != hash(obj)


class TestBaseRestrictionContainer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = BaseRestrictionContainer()

    def test_make_not_implemented(self):
        with pytest.raises(NotImplementedError):
            self.obj.make()

    def test_apply_not_implemented(self):
        with pytest.raises(NotImplementedError):
            self.obj.apply()


