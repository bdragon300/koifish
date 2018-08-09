import pytest

import fields
from model.model import Model, ModelMeta


@pytest.fixture(autouse=True)
def setup():
    yield

    ModelMeta.models = {}


def test_import_class_from_current_package():
    class TargetModelStub(Model):
        primary_key_field = fields.IntegerField(primary_key=True)
        ordinary_field = fields.IntegerField()
        my_model_stub_id = fields.IntegerField()

    class MyModelStub(Model):
        id = fields.IntegerField(primary_key=True)
        otm_field = fields.OneToManyField('TargetModelStub', on_delete=None)
        mto_field = fields.ManyToOneField('TargetModelStub', on_delete=None)

    assert MyModelStub.otm_field._related is TargetModelStub \
           and MyModelStub.mto_field._related is TargetModelStub


def test_import_subclass_from_current_package():
    class Container:
        class TargetModelStub(Model):
            primary_key_field = fields.IntegerField(primary_key=True)
            ordinary_field = fields.IntegerField()
            my_model_stub_id = fields.IntegerField()

    class MyModelStub(Model):
        id = fields.IntegerField(primary_key=True)
        otm_field = fields.OneToManyField('TargetModelStub', on_delete=None)
        mto_field = fields.ManyToOneField('TargetModelStub', on_delete=None)

    assert MyModelStub.otm_field._related is Container.TargetModelStub \
           and MyModelStub.mto_field._related is Container.TargetModelStub


def test_import_self():
    class MyModelStub(Model):
        id = fields.IntegerField(primary_key=True)
        my_model_stub_id = fields.IntegerField()
        otm_field = fields.OneToManyField('MyModelStub', on_delete=None)
        mto_field = fields.ManyToOneField('MyModelStub', on_delete=None)

    assert MyModelStub.otm_field._related is MyModelStub \
           and MyModelStub.mto_field._related is MyModelStub
