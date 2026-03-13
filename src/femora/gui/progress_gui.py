from __future__ import annotations

"""Singleton class providing a Qt-based progress bar that mirrors the
:pyclass:`femora.utils.progress.Progress` console helper.

The first time the callback is invoked, the progress bar widget is lazily
created and inserted *below the interactive console* in the right-hand panel
of the main application window.

Example:
    >>> from femora.gui.progress_gui import get_progress_callback_gui
    >>> cb = get_progress_callback_gui("Exporting")
    >>> cb(10, "initialising")
    >>> cb(100, "done")
"""

from typing import Callable, Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QProgressBar, QWidget, QVBoxLayout, QLabel

__all__ = ["ProgressGUI", "get_progress_callback_gui"]


class _ProgressWidget(QWidget):
    """Lightweight container bundling a label and a :class:`QProgressBar`.

    Attributes:
        _bar (QProgressBar): The Qt progress bar widget.
        _label (QLabel): The Qt label displaying messages.
    """

    def __init__(self, desc: str):
        """Initializes the _ProgressWidget.

        Args:
            desc: The initial description string for the progress bar format.
        """
        super().__init__()
        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        self._bar.setAlignment(Qt.AlignCenter)
        self._bar.setFormat(f"{desc} - %p%")

        self._label = QLabel("", self)
        self._label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._label)
        layout.addWidget(self._bar)

    # Expose convenient passthroughs ---------------------------------
    def set_value(self, value: int):  # noqa: D401
        """Sets the current value of the progress bar.

        Args:
            value: The integer value to set (0-100).
        """
        self._bar.setValue(value)

    def set_message(self, message: str):  # noqa: D401
        """Sets the current message displayed below the progress bar.

        Args:
            message: The string message to display.
        """
        self._label.setText(message)

    def close(self):  # noqa: D401  (keep interface parity)
        """Closes the progress widget."""
        super().close()


class ProgressGUI:
    """Singleton that manages a GUI progress bar and provides a callback.

    This class ensures that only one GUI progress bar instance is active at a
    time, facilitating a consistent visual feedback mechanism across the
    application.

    Attributes:
        _widget (Optional[_ProgressWidget]): The singleton progress widget instance.
            None if the GUI has not been launched or the widget has been closed.
        _last_value (int): The last value set on the progress bar, used for
            internal state management.

    Example:
        >>> from femora.gui.progress_gui import ProgressGUI
        >>> ProgressGUI.show("Loading Data")
        >>> ProgressGUI.callback(50, "Processing step 1")
        >>> ProgressGUI.callback(100, "Done")
        >>> ProgressGUI.close()
    """

    _widget: Optional[_ProgressWidget] = None
    _last_value: int = 0

    # --------------------------------------------------------------
    @classmethod
    def _ensure_widget(cls, desc: str) -> None:
        """Lazy-initializes the underlying widget and attaches it to the UI.

        Args:
            desc: The initial description for the progress bar's format.

        Raises:
            RuntimeError: If `MainWindow` instance cannot be retrieved, indicating
                the GUI has not been launched. In this case, the widget
                initialization is silently ignored.
        """
        if cls._widget is not None:
            return

        # Import here to avoid circular dependencies
        from femora.gui.main_window import MainWindow

        try:
            main_window = MainWindow.get_instance()
        except RuntimeError:
            # GUI has not been launched; silently ignore
            return

        cls._widget = _ProgressWidget(desc)

        # Insert as the last widget in the right-hand splitter (index 2)
        right_panel = getattr(main_window, "right_panel", None)
        if right_panel is not None:
            right_panel.addWidget(cls._widget)
        else:
            # Fallback: add to the status bar if available
            main_window.statusBar().addPermanentWidget(cls._widget)

    # --------------------------------------------------------------
    @classmethod
    def callback(cls, value: float, message: str = "", *, desc: str = "Processing") -> None:
        """Qt-aware progress callback mirroring :meth:`Progress.callback`.

        This method updates the GUI progress bar with the given value and message.
        It handles lazy initialization of the widget and ensures thread-safe
        updates by dispatching GUI manipulations to the main thread.

        Args:
            value: The current progress value, expected to be between 0 and 100.
            message: An optional message string to display below the progress bar.
            desc: An optional description for the progress bar title. This allows
                the progress bar to adapt its title if different tasks use the
                same callback.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.show("Heavy Computation")
            >>> for i in range(10):
            ...     ProgressGUI.callback(i * 10, f"Step {i+1} of 10")
            >>> ProgressGUI.callback(100, "Computation Complete")
            >>> ProgressGUI.close()
        """
        value_int = int(value)

        # All GUI manipulations must happen in the main thread.  We wrap the
        # logic inside a closure dispatched via *invokeMethod* to guarantee
        # thread-safety even when the callback is triggered from worker threads.
        def _update():
            cls._ensure_widget(desc)
            if cls._widget is None:
                return  # GUI not available

            cls._widget.set_message(message)
            cls._widget.set_value(value_int)
            # Keep the description in sync if different tasks supply different *desc*.
            cls._widget._bar.setFormat(f"{desc} - %p%")
            cls._last_value = value_int

            if value_int >= 100:
                # After showing 100 % for a moment, reset to idle but keep widget.
                from qtpy.QtCore import QTimer

                def _reset_idle():
                    if cls._widget is not None:
                        cls._widget.set_message("Idle")
                        cls._widget.set_value(0)

                QTimer.singleShot(1500, _reset_idle)

        # Execute immediately if already in the GUI thread; otherwise queue.
        from qtpy.QtCore import QThread, QTimer
        from qtpy.QtWidgets import QApplication

        if cls._widget is not None and cls._widget.thread() == QThread.currentThread():
            _update()
            # Process events so the bar repaints during long loops running in
            # the same thread.
            QApplication.processEvents()
        else:
            QTimer.singleShot(0, _update)

    # --------------------------------------------------------------
    @classmethod
    def close(cls):
        """Removes the widget from the UI and resets the singleton state.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.show("Starting task")
            >>> # ... do some work ...
            >>> ProgressGUI.close()
        """
        if cls._widget is not None:
            cls._widget.close()
            cls._widget.setParent(None)
            cls._widget = None
            cls._last_value = 0

    # --------------------------------------------------------------
    @classmethod
    def show(cls, desc: str = "Progress") -> None:  # noqa: D401
        """Ensures the progress widget exists and displays an *Idle* state.

        This method will create the progress bar widget if it doesn't already
        exist and set its state to 0% with an "Idle" message, ready for
        updates.

        Args:
            desc: The initial description to set for the progress bar's title.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.show("Preparing files")
            >>> # The progress bar is now visible with "Preparing files - 0%" and "Idle" message.
            >>> ProgressGUI.close()
        """
        cls._ensure_widget(desc)
        if cls._widget is not None:
            cls._widget.set_message("Idle")
            cls._widget.set_value(0)


# Convenience helper --------------------------------------------------


def get_progress_callback_gui(desc: str = "Processing") -> Callable[[float, str], None]:
    """Returns a partially-applied :pyattr:`ProgressGUI.callback` with *desc* preset.

    This convenience helper allows easily creating a progress callback function
    that always uses a specific description for the progress bar.

    Args:
        desc: The default description string to use for the progress bar title
            when the callback is invoked.

    Returns:
        A callable function `(value: float, message: str) -> None` that
        internally calls `ProgressGUI.callback` with the provided `desc`.

    Example:
        >>> from femora.gui.progress_gui import get_progress_callback_gui
        >>> my_callback = get_progress_callback_gui("Batch Processing")
        >>> my_callback(10, "Initializing batch")
        >>> my_callback(50, "Processing item 5")
        >>> my_callback(100, "Batch complete")
        >>> ProgressGUI.close() # Assuming ProgressGUI is imported from the same module
    """

    def _cb(value: float, message: str = "") -> None:  # noqa: D401
        ProgressGUI.callback(value, message, desc=desc)

    return _cb