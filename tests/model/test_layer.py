from model import Model, ModelImpl, Layer


class ModelStubImpl(ModelImpl):
    pass


class ModelStub(Model):
    pass


class LayerStub(Layer):
    pass


class TestLayer:
    def test_get_impl_name(self):
        test_data = ModelStub
        check_data = 'ModelStubImpl'

        res = LayerStub.get_impl_name(test_data)

        assert res == check_data

    def test_get_impl_returns_class_type(self):
        test_data = ModelStub

        res = LayerStub.get_impl(test_data)

        assert isinstance(res, type)

    def test_get_impl_returns_class(self):
        test_data = ModelStub
        check_data = ModelStubImpl

        res = LayerStub.get_impl(test_data)

        assert res == check_data

    def test_get_impl_returns_none_if_not_found(self):
        class DoesNotExistModelStub(Model):
            pass

        test_data = DoesNotExistModelStub

        res = LayerStub.get_impl(test_data)

        assert res is None
