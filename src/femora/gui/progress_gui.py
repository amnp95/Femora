from __future__ import annotations

"""Provides a singleton Qt-based progress bar mirroring the console helper.

This module offers a GUI-based progress mechanism that integrates with
the Femora main application window. The progress bar widget is lazily
created and inserted into the UI upon the first invocation of the callback.

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
    """Lightweight container for a progress bar and its associated label.

    This widget bundles a `QLabel` and a `QProgressBar` for displaying
    task progress and messages within the Femora GUI.

    Attributes:
        _bar (QProgressBar): The underlying Qt progress bar widget.
        _label (QLabel): The underlying Qt label widget for messages.
    """

    def __init__(self, desc: str):
        """Initializes the _ProgressWidget with a description.

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

    def set_value(self, value: int):
        """Sets the current value of the progress bar.

        Args:
            value: The integer percentage (0-100) to set the progress bar to.
        """
        self._bar.setValue(value)

    def set_message(self, message: str):
        """Sets the text message displayed above the progress bar.

        Args:
            message: The string message to display.
        """
        self._label.setText(message)

    def close(self):
        """Closes and hides the progress widget."""
        super().close()


class ProgressGUI:
    """Manages a singleton GUI progress bar and provides a unified callback.

    This class ensures a single `_ProgressWidget` instance is present in the
    application UI, facilitating progress updates from various parts of the
    application, including worker threads.

    Attributes:
        _widget (Optional[_ProgressWidget]): The singleton progress widget instance,
            or None if not yet initialized.
        _last_value (int): The last integer value set on the progress bar.
    """

    _widget: Optional[_ProgressWidget] = None
    _last_value: int = 0

    @classmethod
    def _ensure_widget(cls, desc: str) -> None:
        """Lazy-initializes the underlying widget and attaches it to the UI.

        The widget is added to the right-hand panel of the `MainWindow`
        or to the status bar as a fallback.

        Args:
            desc: The initial description string for the progress bar format
                if the widget is being created.
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

    @classmethod
    def callback(cls, value: float, message: str = "", *, desc: str = "Processing") -> None:
        """Updates the GUI progress bar, mirroring `Progress.callback`.

        This method is thread-safe, dispatching updates to the main GUI thread
        if called from a worker thread. It ensures the progress widget is
        visible and updated with the given value and message. When the progress
        reaches 100%, it briefly displays "100% - done" then resets to "Idle".

        Args:
            value: The current progress value, typically between 0.0 and 100.0.
            message: An optional message to display alongside the progress.
            desc: An optional description for the progress bar title. This allows
                the bar to show different descriptions for different tasks.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.callback(10, "Starting export")
            >>> ProgressGUI.callback(50, "Processing items")
            >>> ProgressGUI.callback(100, "Export complete")
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

    @classmethod
    def close(cls):
        """Removes the progress widget from the UI and resets its state.

        This effectively hides and cleans up the GUI progress bar.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.callback(50, "Working")
            >>> ProgressGUI.close()
        """
        if cls._widget is not None:
            cls._widget.close()
            cls._widget.setParent(None)
            cls._widget = None
            cls._last_value = 0

    @classmethod
    def show(cls, desc: str = "Progress") -> None:
        """Ensures the progress widget exists and displays an 'Idle' state.

        This method can be used to make the progress bar visible without
        starting an actual progress update, showing it in a ready state.

        Args:
            desc: The initial description for the progress bar if it is
                being created or updated.

        Example:
            >>> from femora.gui.progress_gui import ProgressGUI
            >>> ProgressGUI.show("Loading data")
            # ... later, actual progress updates can begin ...
            >>> ProgressGUI.callback(10, "Fetching records")
        """
        cls._ensure_widget(desc)
        if cls._widget is not None:
            cls._widget.set_message("Idle")
            cls._widget.set_value(0)


def get_progress_callback_gui(desc: str = "Processing") -> Callable[[float, str], None]:
    """Returns a partially-applied callback function for `ProgressGUI.callback`.

    This helper function pre-sets the `desc` argument, making it convenient
    to use `ProgressGUI` with specific task descriptions.

    Args:
        desc: The default description to use for the progress bar.

    Returns:
        A callable function `(value: float, message: str = "") -> None`
        that updates the GUI progress bar.

    Example:
        >>> from femora.gui.progress_gui import get_progress_callback_gui
        >>> my_task_cb = get_progress_callback_gui("Uploading Files")
        >>> my_task_cb(25, "File 1 of 4")
        >>> my_task_cb(75, "File 3 of 4")
        >>> my_task_cb(100, "Upload complete")
    """

    def _cb(value: float, message: str = "") -> None:
        ProgressGUI.callback(value, message, desc=desc)

    return _cb