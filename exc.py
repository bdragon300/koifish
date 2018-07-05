import booby.errors


class BaseKoifishError(RuntimeError):
    """
    Base exception class for runtime errors
    Since it derived from Slotinit its slots can be initialized in constructor as parameters
    """
    pass


class ModelError(BaseKoifishError):
    """
    Model-specific errors such as:
    * Some of the required fields are missed while saving
    * Wrong data came from implementation layer
    * Incorrect internal model state
    """
    pass


class NotFoundError(BaseKoifishError):
    """Record was not found while underlying requests was successful"""
    pass


class ValidationError(BaseKoifishError, booby.errors.ValidationError):
    """Model validation failed"""
    pass
