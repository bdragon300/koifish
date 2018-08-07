from fields import Field


class TestField:
    def test_default_prop_values(self):
        obj = Field()

        assert obj.primary_key is False
        assert obj.virtual is False

    def test_primary_key_prop_initialized(self):
        obj = Field(
            primary_key=True
        )

        assert obj.primary_key is True

    def test_virtual_prop_initialized(self):
        obj = Field(
            virtual=True
        )

        assert obj.virtual is True
