import pytest
from layer import ModelImpl


class TestImpl:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.obj = ModelImpl()

    def test_get(self):
        with pytest.raises(NotImplementedError):
            self.obj.get('id', 1234)

    def test_create(self):
        fields = {
            'field1': '1234',
            'field2': {
                1: 2,
                3: 4
            }
        }
        with pytest.raises(NotImplementedError):
            self.obj.create(fields)

    def test_update(self):
        fields = {
            'field1': '4321',
            'field2': {
                1: 'dgf',
                3: 4
            }
        }
        with pytest.raises(NotImplementedError):
            self.obj.update('id', 1234, fields)

    def test_delete(self):
        with pytest.raises(NotImplementedError):
            self.obj.delete('id', 1234)

    def test_get_list(self):
        with pytest.raises(NotImplementedError):
            self.obj.get_list(None, None, None)
