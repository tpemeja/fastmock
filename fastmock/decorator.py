"""
This module provides the FastMockDecorator class for adding mock data attributes to functions.
"""
from fastmock.model import MockData


class FastMockDecorator:
    """
    A decorator class for adding mock data attributes to functions.

    This class allows you to define default mock data and update it when applying the decorator
    to functions.
    The mock data is stored as an attribute on the decorated function.

    Attributes:
        attribute_name (str): The name of the attribute that will be added to the decorated
        function to store the mock data.

    Args:
        **kwargs: Keyword arguments that are used to initialize the default mock data.

    Methods:
        __call__(func=None, **kwargs):
            If `func` is None, updates the default mock data with the provided kwargs and
            returns a new instance of FastMockDecorator.
            If `func` is provided, updates the default mock data with the provided kwargs,
            sets it as an attribute on the function, and returns the function.
    """

    attribute_name = "mock_data"

    def __init__(self, **kwargs):
        """
        Initializes the FastMockDecorator with default mock data.

        Args:
            **kwargs: Keyword arguments to initialize the default mock data.
        """
        self.default_data = MockData(**kwargs)

    def __call__(self, func=None, **kwargs):
        """
        Updates the default mock data and decorates the given function with the updated mock data.

        If `func` is None, returns a new instance of FastMockDecorator with the updated mock data.
        If `func` is provided, sets the updated mock data as an attribute on the function
        and returns the function.

        Args:
            func (callable, optional): The function to be decorated with the mock data.
            **kwargs: Keyword arguments to update the default mock data.

        Returns:
            If `func` is None, returns a new instance of FastMockDecorator
            with the updated mock data.
            If `func` is provided, returns the decorated function with the updated mock data.
        """
        if func is None:
            updated_data = self.default_data.copy(update=kwargs)
            return self.__class__(**updated_data.dict())

        updated_data = self.default_data.copy(update=kwargs)
        setattr(func, self.attribute_name, updated_data)
        return func
