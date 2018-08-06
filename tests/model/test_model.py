import random
from unittest.mock import Mock, call

import pytest

import fields
from cacher import MemoryCacher
from exc import ModelError, NotFoundError, ValidationError
from model import Model, QuerySet


@pytest.fixture()
def randomize_record():
    def w(*args, **kwargs):
        d = dict(*args, **kwargs)
        return {k: random.randrange(10000) for k in d.keys()}

    return w


@pytest.fixture()
def model_stub_class():
    class ModelStub(Model):
        primary_key_field = fields.IntegerField(primary_key=True)
        request_field = fields.IntegerField()
        virtual_field = fields.IntegerField(virtual=True)

    return ModelStub


class TestModel:
    @pytest.fixture(autouse=True)
    def setup(self, model_stub_class, randomize_record):
        self.model_class = model_stub_class

        self.test_impl_obj = Mock()
        self.test_default_impl_obj = Mock()
        self.test_layer_class = Mock(
            get_impl=Mock(return_value=lambda *a, **kw: self.test_impl_obj),
            __name__='TestLayer'
        )
        self.test_default_layer_class = Mock(
            get_impl=Mock(return_value=lambda *a, **kw: self.test_default_impl_obj),
            __name__='TestDefaultLayer'
        )

        self.model_class._default_layer = self.test_default_layer_class
        self.obj = self.model_class()

    def test_pass_model_name_to_foreign_fields(self):
        class ForeignFieldsStub(Model):
            primary_key_field = Mock(spec=fields.IntegerField, primary_key=True)
            field1 = Mock(spec=fields.ForeignKey, primary_key=False)
            field2 = Mock(spec=fields.OneToManyField, primary_key=False)

        class DerivedForeignFieldsStub(ForeignFieldsStub):
            primary_key_field2 = Mock(spec=fields.IntegerField, primary_key=True)
            field3 = Mock(spec=fields.ForeignKey, primary_key=False)
            field4 = Mock(spec=fields.OneToManyField, primary_key=False)

        ancestor_fields_calls = (
            call(ForeignFieldsStub.__name__),
            call(DerivedForeignFieldsStub.__name__)
        )

        ForeignFieldsStub.field1.init.assert_has_calls(ancestor_fields_calls)
        ForeignFieldsStub.field2.init.assert_has_calls(ancestor_fields_calls)
        DerivedForeignFieldsStub.field3.init.assert_called_once_with(DerivedForeignFieldsStub.__name__)
        DerivedForeignFieldsStub.field4.init.assert_called_once_with(DerivedForeignFieldsStub.__name__)

    def test_primary_key_determine(self):
        primary_key = list(k for k, v in self.obj.__class__.__dict__.items()
                      if isinstance(v, fields.Field) and v.primary_key)

        assert len(primary_key) == 1
        assert self.obj.primary_key == primary_key[0]

    def test_error_on_no_primary_key(self):
        with pytest.raises(ModelError):
            class ModelStubNoPrimary(Model):
                primary_key_field = fields.IntegerField(primary_key=False)
                request_field = fields.IntegerField()
                virtual_field = fields.IntegerField(virtual=True)

    def test_override_primary_key_if_it_specified_explicitly_in_ancestor(self):
        class ForeignFieldsStub(Model):
            primary_key = 'override_pk'
            primary_key_field = Mock(spec=fields.IntegerField, primary_key=False)

        class DerivedForeignFieldsStub(ForeignFieldsStub):
            primary_key_field2 = Mock(spec=fields.IntegerField, primary_key=False)

        assert ForeignFieldsStub.primary_key == 'override_pk' \
            and DerivedForeignFieldsStub.primary_key == 'override_pk'

    def test_override_primary_key_if_it_specified_explicitly_in_successor(self):
        class ForeignFieldsStub(Model):
            primary_key_field = Mock(spec=fields.IntegerField, primary_key=True)

        class DerivedForeignFieldsStub(ForeignFieldsStub):
            primary_key = 'field3'
            primary_key_field2 = Mock(spec=fields.IntegerField, primary_key=False)
            field3 = Mock(spec=fields.IntegerField, primary_key=False)

        assert ForeignFieldsStub.primary_key == 'primary_key_field' \
            and DerivedForeignFieldsStub.primary_key == 'field3'

    def test_override_primary_key_if_it_specified_explicitly_everywhere(self):
        class ForeignFieldsStub(Model):
            primary_key = 'override_pk'
            primary_key_field = Mock(spec=fields.IntegerField, primary_key=True)

        class DerivedForeignFieldsStub(ForeignFieldsStub):
            primary_key = 'field3'
            primary_key_field2 = Mock(spec=fields.IntegerField, primary_key=False)
            field3 = Mock(spec=fields.IntegerField, primary_key=False)

        assert ForeignFieldsStub.primary_key == 'override_pk' \
            and DerivedForeignFieldsStub.primary_key == 'field3'

    def test_error_on_several_primary_keys(self):
        with pytest.raises(ModelError):
            class ModelStubTwoPrimary(Model):
                primary_key_field = fields.IntegerField(primary_key=False)
                request_field = fields.IntegerField()
                virtual_field = fields.IntegerField(virtual=True)

    def test_props_default_value(self):
        assert self.obj._deleted is False
        assert self.obj._validate_on_write is True
        assert self.obj._validate_on_read is False
        assert self.obj._search_impl_in_default_layer is True
        assert isinstance(self.obj._cacher, MemoryCacher)

    def test_default_layer_class(self):
        assert self.obj._layer_class is self.test_default_layer_class

    def test_layer_class_set(self):
        obj = self.model_class(self.test_layer_class)

        assert obj._layer_class is self.test_layer_class

    def test_impl_object_set_default_if_not_passed(self):
        assert self.obj._impl_object is self.test_default_impl_obj

    def test_impl_object_set(self):
        obj = self.model_class(self.test_layer_class)

        assert obj._impl_object is self.test_impl_obj

    def test_impl_object_set_default_if_not_found(self):
        self.test_layer_class.get_impl.return_value = None

        obj = self.model_class(self.test_layer_class)

        assert obj._impl_object is self.test_default_impl_obj

    def test_impl_object_raise_error_if_not_found_in_default(self):
        self.test_layer_class.get_impl.return_value = None
        self.test_default_layer_class.get_impl.return_value = None

        with pytest.raises(ModelError):
            obj = self.model_class(self.test_layer_class)

    def test_impl_object_raise_error_if_not_found_in_layer_and_forbidden_to_search_in_default_layer(self):
        self.model_class._search_impl_in_default_layer = False
        self.test_layer_class.get_impl.return_value = None

        with pytest.raises(ModelError):
            obj = self.model_class(self.test_layer_class)

    def test_request_fields_determine(self):
        check_data = {k: v for k, v in self.obj.__class__.__dict__.items()
                      if isinstance(v, fields.Field) and not v.virtual}

        assert self.obj._request_fields == check_data

    def test_model_init_by_kwargs(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        obj = self.model_class(**test_data)

        t = dict(obj)

        assert test_data == t

    def test_objects_prop_return_new_queryset_on_every_call(self):
        obj1 = self.obj.objects
        obj2 = self.obj.objects

        assert obj1 is not obj2 and isinstance(obj1, QuerySet) and isinstance(obj2, QuerySet)

    def test_objects_prop_pass_model_object(self):
        res = self.obj.objects

        assert res.model_obj is self.obj

    def test_objects_prop_pass_new_cache(self):
        self.obj._cacher = Mock(spec=MemoryCacher)

        res = self.obj.objects

        assert res._cache == self.obj._cacher.new_cache.return_value

    def test_objects_prop_pass_request_limit_param(self):
        test_data = 777
        self.obj._request_limit = test_data

        res = self.obj.objects

        assert res.request_limit == test_data

    def test_fields_prop(self):
        assert self.obj.fields is self.obj._fields

    def test_load_pk_kwarg_treats_as_primary_key(self, randomize_record):
        pk_val = 123
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = Mock(return_value=test_data)

        self.obj.load(pk=pk_val)

        self.obj._impl_object.get.assert_called_once_with(self.obj.primary_key, pk_val)

    def test_load_fill_request_fields(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data
        check_data = test_data
        check_data.update({k: None for k in dict(self.obj) if k not in self.obj._request_fields})

        self.obj.load(pk=123)

        assert dict(self.obj) == check_data

    def test_load_returns_self(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        res = self.obj.load(pk=123)

        assert res is self.obj

    @pytest.mark.parametrize('result', ({}, None))
    def test_load_raise_not_found_error_if_empty_data_returned(self, result):
        self.obj._impl_object.get = lambda *a, **kw: result

        with pytest.raises(NotFoundError):
            self.obj.load(pk=123)

    @pytest.mark.parametrize('kwargs', (
        {'pk': 123, 'primary_key_field': 456},
        {}
    ))
    def test_load_raise_error_on_wrong_kwargs_count(self, kwargs, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(TypeError):
            self.obj.load(**kwargs)

    @pytest.mark.parametrize('kwargs', (
        {'virtual_field': 123},
        {'field_does_not_exist': 123}
    ))
    def test_load_raise_error_on_not_primary_key_in_kwargs(self, kwargs, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(ValueError):
            self.obj.load(**kwargs)

    def test_load_validate(self, randomize_record):
        self.obj._validate_on_read = True
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = 'string'
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(ValidationError):
            self.obj.load(pk=123)

    def test_load_dont_validate(self, randomize_record):
        self.obj._validate_on_read = False
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = 'string'
        self.obj._impl_object.get = lambda *a, **kw: test_data

        self.obj.load(pk=123)  # ValidationError don't raise

    def test_get_pk_kwarg_treats_as_primary_key(self, randomize_record):
        pk_val = 123
        test_data = randomize_record(dict(self.obj))
        get_mock = self.obj._impl_object.get = Mock(return_value=test_data)

        self.obj.get(pk=pk_val)

        get_mock.assert_called_once_with(self.obj.primary_key, pk_val)

    def test_get_returns_new_filled_object(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data
        check_data = test_data
        check_data.update({k: None for k in dict(self.obj) if k not in self.obj._request_fields})

        res = self.obj.get(pk=123)

        assert dict(res) == check_data

    def test_get_returns_new_object_of_the_same_class(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        res = self.obj.get(pk=123)

        assert res is not self.obj
        assert res.__class__ == self.obj.__class__

    def test_get_returns_new_object_with_the_same_layer(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        res = self.obj.get(pk=123)

        assert res._layer_class == self.obj._layer_class

    @pytest.mark.parametrize('result', ({}, None))
    def test_get_raise_not_found_error_if_empty_data_returned(self, result):
        self.obj._impl_object.get = lambda *a, **kw: result

        with pytest.raises(NotFoundError):
            self.obj.get(pk=123)

    @pytest.mark.parametrize('kwargs', (
        {'pk': 123, 'primary_key_field': 456},
        {}
    ))
    def test_get_raise_error_on_wrong_kwargs_count(self, kwargs, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(TypeError):
            self.obj.get(**kwargs)

    @pytest.mark.parametrize('kwargs', (
        {'virtual_field': 123},
        {'field_does_not_exist': 123}
    ))
    def test_get_raise_error_on_not_primary_key_in_kwargs(self, kwargs, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(ValueError):
            self.obj.get(**kwargs)

    def test_get_validate(self, randomize_record):
        self.obj.__class__._validate_on_read = True
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = 'string'
        self.obj._impl_object.get = lambda *a, **kw: test_data

        with pytest.raises(ValidationError):
            self.obj.get(pk=123)

    def test_get_dont_validate(self, randomize_record):
        self.obj._validate_on_read = True
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = 'string'
        self.obj._impl_object.get = lambda *a, **kw: test_data

        self.obj.get(pk=123)  # ValidationError don't raise

    def test_save_create_dont_fill_model_if_returns_none(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = None
        self.obj.update(test_data)
        check_data = {k: v for k, v in dict(self.obj).items() if k in self.obj._request_fields}
        self.obj._impl_object.create = Mock(return_value=None)

        self.obj.save()

        self.obj._impl_object.create.assert_called_with(check_data)
        assert dict(self.obj) == test_data

    def test_save_create_fill_model_with_result(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = None
        req_data = randomize_record({k: None for k in dict(self.obj) if k in self.obj._request_fields})
        check_data = dict(self.obj)
        check_data.update(req_data)
        self.obj.update(test_data)
        self.obj._impl_object.create = Mock(return_value=req_data)

        self.obj.save()

        assert dict(self.obj) == check_data

    def test_save_create_actually_use_request_fields(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = None
        self.obj.update(test_data)
        self.obj._impl_object.create = Mock(return_value=test_data)
        check_data = {k: v for k, v in dict(self.obj).items() if k in self.obj._request_fields}

        self.obj.save()

        self.obj._impl_object.create.assert_called_with(check_data)

    def test_save_update_dont_fill_model_if_returns_none(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        check_data = {k: v for k, v in dict(self.obj).items() if k in self.obj._request_fields}
        self.obj._impl_object.update = Mock(return_value=None)

        self.obj.save()

        self.obj._impl_object.update.assert_called_with(check_data)
        assert dict(self.obj) == test_data

    def test_save_update_fill_model_with_result(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        req_data = randomize_record({k: None for k in dict(self.obj) if k in self.obj._request_fields})
        check_data = dict(self.obj)
        check_data.update(req_data)
        self.obj.update(test_data)
        self.obj._impl_object.update = Mock(return_value=req_data)

        self.obj.save()

        assert dict(self.obj) == check_data

    def test_save_update_actually_use_request_fields(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.update = Mock(return_value=test_data)
        check_data = {k: v for k, v in dict(self.obj).items() if k in self.obj._request_fields}

        self.obj.save()

        self.obj._impl_object.update.assert_called_with(check_data)

    def test_save_actually_use_raw_fields_data(self, randomize_record):
        # Actually test whether method doesn't use indexation or property access
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.update = Mock(return_value=None)
        m = Mock()
        for i in dir(self.obj):
            if isinstance(getattr(self.obj, i), fields.Field):
                setattr(self.obj, i, m)
        self.obj.__getitem__ = self.obj.__setitem__ = m

        self.obj.save()

        m.assert_not_called()
        assert dict(self.obj) == test_data

    def test_save_raise_error_on_failed_validation_before_save(self, randomize_record):
        self.obj._validate_on_write = True
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = 'string'
        self.obj.update(test_data)

        with pytest.raises(ValidationError):
            self.obj.save()

    def test_save_returns_self(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.update = Mock(return_value=None)

        res = self.obj.save()

        assert res is self.obj

    def test_save_raise_error_if_deleted(self):
        self.obj._deleted = True

        with pytest.raises(ModelError):
            self.obj.save()

    def test_delete_use_primary_key(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.delete = Mock(return_value=None)
        check_data = self.obj.primary_key, \
                     self.obj._data[self.obj._fields[self.obj.primary_key]]

        self.obj.delete()

        self.obj._impl_object.delete.assert_called_once_with(*check_data)

    def test_delete_set_deleted_flag(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.delete = Mock(return_value=None)

        self.obj.delete()

        assert self.obj._deleted is True

    def test_delete_returns_self(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj.update(test_data)
        self.obj._impl_object.delete = Mock(return_value=None)

        res = self.obj.delete()

        assert res is self.obj

    def test_delete_raise_error_if_primary_key_is_none(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        test_data['primary_key_field'] = None
        self.obj.update(test_data)
        self.obj._impl_object.delete = Mock(return_value=None)

        with pytest.raises(ModelError):
            self.obj.delete()

    def test_delete_raise_error_if_deleted_flag_is_true(self):
        self.obj._deleted = True

        with pytest.raises(ModelError):
            self.obj.delete()

    def test_get_list_calls_impl_method(self):
        self.obj._impl_object.get_list = Mock()
        test_data = Mock()

        res = self.obj.get_list(test_data)

        self.obj._impl_object.get_list.assert_called_once_with(test_data)

    def test_get_list_returns_impl_method_result(self):
        self.obj._impl_object.get_list = Mock()
        test_data = Mock()

        res = self.obj.get_list(test_data)

        assert res == self.obj._impl_object.get_list.return_value

    def test_update_resets_deleted_flag(self, randomize_record):
        test_data = randomize_record(dict(self.obj))
        self.obj._deleted = True

        self.obj.update(test_data)

        assert self.obj._deleted is False

    def test_new_model_returns_new_object_the_same_class(self, randomize_record):
        test_data = randomize_record(dict(self.obj))

        res = self.obj.new_model(test_data)

        assert res is not self.obj
        assert res.__class__ == self.obj.__class__

    def test_new_model_returns_new_object_with_the_same_layer(self, randomize_record):
        test_data = randomize_record(dict(self.obj))

        res = self.obj.new_model(test_data)

        assert res._layer_class == self.obj._layer_class
