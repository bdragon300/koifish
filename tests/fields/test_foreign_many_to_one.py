import random
import string
from unittest.mock import Mock

import pytest

import fields
from exc import ModelError
from fields import ManyToOneField
from layer.impl import ListResponse
from model.model import Model, ModelMeta
from model.restrictions import Filters


@pytest.fixture()
def model_stubs():
    class TargetModelStub(Model):
        primary_key_choice_field = fields.StringField(primary_key=True, choices=[1, 2, 3])
        ordinary_field = fields.StringField()

    class MyModelStub(Model):
        id = fields.StringField(primary_key=True)
        choice_mto_field = fields.ManyToOneField(TargetModelStub, on_delete=None, choices=[1, 2])

    return MyModelStub, TargetModelStub


@pytest.fixture()
def target_records(model_stubs):
    my, target = model_stubs
    target_fields = [k for k, v in target.__dict__.items()
                     if isinstance(v, fields.Field) and not v.virtual]

    recs = []
    for i in range(15):
        recs.append({
            f: (random.choice(list(getattr(target, f).choices))
                if getattr(target, f).choices
                else ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5)))
            for f in target_fields
        })

    d = ListResponse(initlist=recs)
    d.total_count = 100500
    return d


class TestManyToOne:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.on_delete_param = None
        self.test_impl_obj = Mock()
        self.test_layer_class = Mock(
            get_impl=Mock(return_value=lambda *a, **kw: self.test_impl_obj),
            __name__='TestLayer'
        )

        yield

        ModelMeta.models = {}

    def test_default_props(self, model_stubs):
        my, target = model_stubs

        obj = ManyToOneField(target, self.on_delete_param)

        assert obj._on_delete is self.on_delete_param
        assert obj._my_model_cls is None
        assert obj._to_model_cached is None

    def test_init_set_model_name(self, model_stubs):
        my, target = model_stubs

        obj = ManyToOneField(target, on_delete=self.on_delete_param)
        obj.init(my)

        assert obj._my_model_cls == my

    def test_init_determine_to_field_if_not_specified(self, model_stubs):
        my, target = model_stubs
        check_data = target.primary_key

        obj = ManyToOneField(target, on_delete=self.on_delete_param)
        obj.init(my)

        assert obj.to_field == check_data

    def test_init_leave_to_field_if_specified(self, model_stubs):
        my, target = model_stubs
        test_data = 'ordinary_field'
        check_data = test_data

        obj = ManyToOneField(target, on_delete=self.on_delete_param, to_field=test_data)
        obj.init(my)

        assert obj.to_field == check_data

    def test_init_error_when_to_field_not_found_in_target(self, model_stubs):
        my, target = model_stubs
        test_data = 'field_does_not_exist'

        with pytest.raises(ModelError):
            obj = ManyToOneField(target, on_delete=self.on_delete_param, to_field=test_data)
            obj.init(my)
            obj.to_field

    def test_get_filter_params(self, model_stubs, target_records):
        self.test_impl_obj.get_list.return_value = target_records

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        my_val = random.choice(my.choice_mto_field.choices)
        check_data = Filters(**{my.choice_mto_field.to_field + '__eq': my_val})

        myobj.choice_mto_field = my_val
        res = myobj.choice_mto_field

        assert self.test_impl_obj.get_list.call_args[0][0] == check_data

    def test_get_return_the_first_element(self, model_stubs, target_records):
        self.test_impl_obj.get_list.return_value = target_records

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        targetobj = target(self.test_layer_class)
        targetobj.update(target_records[0])

        myobj.choice_mto_field = random.choice(my.choice_mto_field.choices)
        res = myobj.choice_mto_field

        assert res == targetobj

    def test_get_return_none_if_field_is_empty(self, model_stubs, target_records):
        self.test_impl_obj.get_list.return_value = target_records

        my, target = model_stubs
        myobj = my(self.test_layer_class)

        myobj.choice_mto_field = None
        res = myobj.choice_mto_field

        assert res is None

    def test_get_return_none_if_no_results(self, model_stubs):
        r = ListResponse()
        r.total_count = 0
        self.test_impl_obj.get_list.return_value = r

        my, target = model_stubs
        myobj = my(self.test_layer_class)

        myobj.choice_mto_field = random.choice(my.choice_mto_field.choices)
        res = myobj.choice_mto_field

        assert res is None

    def test_get_return_self_on_class_access(self, model_stubs):
        my, target = model_stubs

        res = my.choice_mto_field

        assert res is my.choice_mto_field

    def test_set_model_object(self, model_stubs):
        my, target = model_stubs
        myobj = my(self.test_layer_class)
        targetobj = target(self.test_layer_class)
        targetobj.primary_key_choice_field = random.choice(target.primary_key_choice_field.choices)
        check_data = targetobj.primary_key_choice_field

        myobj.choice_mto_field = targetobj

        assert myobj._data[myobj.fields['choice_mto_field']] == check_data
