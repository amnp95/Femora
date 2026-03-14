class PlotterManager:
    """Manages a global plotter instance for the application.

    This class provides a centralized way to set, retrieve, and manage a single
    plotter instance, effectively breaking circular import dependencies. It
    ensures that the plotter is initialized before use and provides utility
    methods for its management.

    Attributes:
        _plotter (object or None): The globally accessible plotter instance, or
            None if not yet set.

    Example:
        >>> class MockPlotter:
        ...     def __init__(self):
        ...         self.cleared = False
        ...     def clear(self):
        ...         self.cleared = True
        ...     def __repr__(self):
        ...         return "MockPlotter()"
        >>> PlotterManager.set_plotter(MockPlotter())
        >>> plotter_instance = PlotterManager.get_plotter()
        >>> print(plotter_instance)
        MockPlotter()
        >>> PlotterManager.clear_plotter()
        >>> print(plotter_instance.cleared)
        True
        >>> PlotterManager.remove_plotter()
        >>> try:
        ...     PlotterManager.get_plotter()
        ... except RuntimeError as e:
        ...     print(e)
        Plotter has not been initialized. Ensure MainWindow is created before accessing the plotter.
    """
    _plotter = None

    @classmethod
    def set_plotter(cls, plotter) -> None:
        """Sets the global plotter instance.

        This method assigns the provided plotter instance to the global
        manager, making it accessible application-wide.

        Args:
            plotter (object): The plotter instance to be set globally. This
                object should ideally have a `clear()` method if
                `clear_plotter` is to be used.

        Example:
            >>> class MockPlotter:
            ...     def clear(self): pass
            >>> PlotterManager.set_plotter(MockPlotter())
            >>> assert PlotterManager.get_plotter() is not None
        """
        cls._plotter = plotter

    @classmethod
    def get_plotter(cls):
        """Gets the global plotter instance.

        Retrieves the currently set global plotter. If no plotter has been
        initialized, a RuntimeError is raised.

        Returns:
            object: The global plotter instance.

        Raises:
            RuntimeError: If no plotter has been set via `set_plotter`.

        Example:
            >>> class MockPlotter:
            ...     def clear(self): pass
            >>> PlotterManager.set_plotter(MockPlotter())
            >>> plotter_instance = PlotterManager.get_plotter()
            >>> assert isinstance(plotter_instance, MockPlotter)
            >>> PlotterManager.remove_plotter()
            >>> try:
            ...     PlotterManager.get_plotter()
            ... except RuntimeError as e:
            ...     print(e)
            Plotter has not been initialized. Ensure MainWindow is created before accessing the plotter.
        """
        if cls._plotter is None:
            raise RuntimeError("Plotter has not been initialized. "
                             "Ensure MainWindow is created before accessing the plotter.")
        return cls._plotter

    @classmethod
    def remove_plotter(cls) -> None:
        """Removes the global plotter instance.

        This effectively unsets the plotter, making it unavailable until
        `set_plotter` is called again. It is particularly useful for testing
        or resetting the application state.

        Example:
            >>> class MockPlotter:
            ...     def clear(self): pass
            >>> PlotterManager.set_plotter(MockPlotter())
            >>> assert PlotterManager.get_plotter() is not None
            >>> PlotterManager.remove_plotter()
            >>> try:
            ...     PlotterManager.get_plotter()
            ... except RuntimeError:
            ...     print("Plotter successfully removed.")
            Plotter successfully removed.
        """
        cls._plotter = None

    @classmethod
    def clear_plotter(cls) -> None:
        """Clears the currently set global plotter.

        This method calls the `clear()` method on the currently active
        plotter instance.

        Raises:
            AttributeError: If no plotter has been set (i.e., `_plotter` is
                `None`) or if the set plotter instance does not have a
                `clear` method.

        Example:
            >>> class MockPlotterWithClear:
            ...     def __init__(self): self.data = []
            ...     def clear(self): self.data = []
            >>> PlotterManager.set_plotter(MockPlotterWithClear())
            >>> plotter = PlotterManager.get_plotter()
            >>> plotter.data.append(1)
            >>> assert plotter.data == [1]
            >>> PlotterManager.clear_plotter()
            >>> assert plotter.data == []
            >>> PlotterManager.remove_plotter()
            >>> try:
            ...     PlotterManager.clear_plotter()
            ... except AttributeError as e:
            ...     print(e)
            'NoneType' object has no attribute 'clear'
            >>> class MockPlotterWithoutClear:
            ...     pass
            >>> PlotterManager.set_plotter(MockPlotterWithoutClear())
            >>> try:
            ...     PlotterManager.clear_plotter()
            ... except AttributeError as e:
            ...     print(e)
            'MockPlotterWithoutClear' object has no attribute 'clear'
        """
        cls._plotter.clear()