import pytest
from unittest.mock import Mock
from layer import Adapter


@pytest.fixture
def adapter_stub():
    class AdapterStub(Adapter):
        def start(self, *args, **kwargs): ...

        def terminate(self, *args, **kwargs): ...

        def parse_response(self, response): ...

        def get(self, pk, pk_val, *args, **kwargs): ...

        def create(self, data, *args, **kwargs): ...

        def update(self, pk, pk_val, data, *args, **kwargs): ...

        def delete(self, pk, pk_val, *args, **kwargs): ...

        def get_list(self, filters, sorts, pagination, *args, **kwargs): ...

    return AdapterStub


class TestAdapter:
    def test_default_props(self, adapter_stub):
        obj = adapter_stub()

        assert obj.init_params == {}
        assert obj.config is None
        assert obj.filters is None
        assert obj.sorts is None
        assert obj.pagination is None
        assert obj.handle is None

    def test_init_params(self, adapter_stub):
        test_data = {
            'config': Mock(),
            'filters' : Mock(),
            'sorts': Mock(),
            'pagination': Mock(),
            'handle': Mock()
        }

        obj = adapter_stub(**test_data)
        assert all(test_data[a] == getattr(obj, a) for a in test_data) and obj.init_params == test_data

    def test_enter_context_manager_returns_self(self, adapter_stub):
        obj = adapter_stub()

        with obj as h:
            assert h is obj

    def test_enter_context_manager_starts_session(self, adapter_stub):
        adapter_stub.start = Mock()

        obj = adapter_stub()

        with obj as h:
            assert h.handle == adapter_stub.start.return_value

    def test_exit_context_manager_terminate_session(self, adapter_stub):
        adapter_stub.start = Mock()
        adapter_stub.terminate = Mock()

        obj = adapter_stub()

        with obj as h:
            pass

        adapter_stub.terminate.assert_called_once()
