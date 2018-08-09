import pytest
from model.model import ModelMeta


@pytest.fixture(autouse=True, scope='module')
def clear_model_meta_collected_models():
    ModelMeta.models = {}
