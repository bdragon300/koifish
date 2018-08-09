import random
import re
import string
from unittest.mock import Mock

import pytest

import fields
from exc import ModelError
from fields import OneToManyField
from layer.impl import ListResponse
from model import QuerySet
from model.model import Model, ModelMeta
from model.restrictions import Filters


@pytest.fixture()
def model_stubs():
    class TargetModelStub(Model):
        primary_key_field = fields.IntegerField(primary_key=True)
        ordinary_field = fields.IntegerField()
        my_model_stub_id = fields.IntegerField(choices=[1, 2, 3])

    class MyModelStub(Model):
        id = fields.IntegerField(primary_key=True, choices=[1, 2])
        choice_otm_field = fields.OneToManyField(TargetModelStub, on_delete=None)

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


@pytest.fixture()
def empty_records():
    res = ListResponse()
    res.total_count = 100500

    return res


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

        obj = OneToManyField(target, self.on_delete_param)

        assert obj._on_delete is self.on_delete_param
        assert obj._my_model_cls is None
        assert obj._to_model_cached is None

    def test_to_field_prop_error_if_not_initialized(self, model_stubs):
        my, target = model_stubs

        obj = OneToManyField(target, on_delete=self.on_delete_param)

        with pytest.raises(ModelError):
            obj.to_field

    def test_init_set_model_name(self, model_stubs):
        my, target = model_stubs

        obj = OneToManyField(target, on_delete=self.on_delete_param)
        obj.init(my)

        assert obj._my_model_cls == my

    def test_init_determine_to_field_if_not_specified(self, model_stubs):
        my, target = model_stubs
        # Class name in snake case + 'id'
        check_data = re.sub('([a-z0-9])([A-Z])', r'\1_\2',
                            re.sub('(.)([A-Z][a-z]+)', r'\1_\2', my.__name__)
                            ).lower() + '_id'

        obj = OneToManyField(target, on_delete=self.on_delete_param)
        obj.init(my)

        assert obj.to_field == check_data

    def test_init_leave_to_field_if_specified(self, model_stubs):
        my, target = model_stubs
        test_data = 'ordinary_field'
        check_data = test_data

        obj = OneToManyField(target, on_delete=self.on_delete_param, to_field=test_data)
        obj.init(my)

        assert obj.to_field == check_data

    def test_init_error_when_to_field_not_found_in_target(self, model_stubs):
        my, target = model_stubs
        test_data = 'field_does_not_exist'

        with pytest.raises(ModelError):
            obj = OneToManyField(target, on_delete=self.on_delete_param, to_field=test_data)
            obj.to_field

    def test_get_filter_params(self, model_stubs, target_records):
        self.test_impl_obj.get_list.return_value = target_records

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        my_val = random.choice(my.id.choices)
        check_data = Filters(**{my.choice_otm_field.to_field + '__eq': my_val})

        myobj.id = my_val
        res = myobj.choice_otm_field

        assert res.filters == check_data

    @pytest.mark.parametrize('pk', (None, 123))
    def test_get_return_queryset(self, model_stubs, target_records, empty_records, pk):
        self.test_impl_obj.get_list.side_effect = (target_records, empty_records)

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        myobj.id = pk

        res = myobj.choice_otm_field

        assert isinstance(res, QuerySet) and isinstance(res.model_obj, target)

    def test_get_return_records(self, model_stubs, target_records, empty_records):
        self.test_impl_obj.get_list.side_effect = (target_records, empty_records)

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        myobj.id = 123

        res = myobj.choice_otm_field

        assert len(res) > 0 and all(a == target(self.test_layer_class, **b) for a, b in zip(res, target_records))

    def test_get_return_empty_queryset_if_primary_key_is_none(self, model_stubs, target_records, empty_records):
        self.test_impl_obj.get_list.side_effect = (target_records, empty_records)

        my, target = model_stubs
        myobj = my(self.test_layer_class)
        myobj.id = None

        res = myobj.choice_otm_field

        assert len(res) == 0 and list(res) == []

    def test_get_return_empty_queryset_if_no_results(self, model_stubs, empty_records):
        self.test_impl_obj.get_list.return_value = empty_records

        my, target = model_stubs
        myobj = my(self.test_layer_class)

        res = myobj.choice_otm_field

        assert len(res) == 0 and list(res) == []

    def test_get_return_self_on_class_access(self, model_stubs):
        my, target = model_stubs

        res = my.choice_otm_field

        assert res is my.choice_otm_field

    def test_set_error(self, model_stubs):
        my, target = model_stubs
        myobj = my(self.test_layer_class)

        with pytest.raises(AttributeError):
            myobj.choice_otm_field = 'test_value'
