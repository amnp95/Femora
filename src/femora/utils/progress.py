from __future__ import annotations

"""Reusable progress-reporting helpers used across the Femora package.

To show progress in long-running operations we often need a simple callback
with the signature ``callback(value: float, message: str)`` where *value* is a
percentage in the 0–100 range.

This module centralises that logic so every component can obtain the same
consistent progress reporter (currently powered by *tqdm*). It avoids
duplicating the progress-bar code in many classes (e.g. MeshMaker).
"""

from typing import Callable, Optional
import tqdm

__all__ = ["Progress", "get_progress_callback"]


class Progress:
    """Manages a global progress bar for reporting operation progress.

    This singleton class provides a consistent way to display progress using
    `tqdm` across different parts of the Femora package. It ensures only
    one progress bar is active at a time and provides methods for updating
    and closing it.

    Attributes:
        _bar (Optional[tqdm.tqdm]): The internal `tqdm` progress bar instance,
            or `None` if the bar has not been initialized or has been closed.
        _last_value (int): The last integer progress value reported (0-100).

    Example:
        >>> from femora.progress import Progress
        >>> Progress.callback(value=0, desc="Loading Data")
        Loading Data:   0%|          | 0/100 [...]
        >>> Progress.callback(value=50, message="Processing chunk 1")
        Loading Data:  50%|█████     | 50/100 [...] Processing chunk 1
        >>> Progress.callback(value=100)
        Loading Data: 100%|██████████| 100/100 [...]
    """

    _bar: Optional[tqdm.tqdm] = None
    _last_value: int = 0

    @classmethod
    def _ensure_bar(cls, desc: str) -> None:
        if cls._bar is None:
            # Lazily create the bar when the first update happens
            cls._bar = tqdm.tqdm(
                total=100,
                desc=desc,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [" "{elapsed}<{remaining}] {postfix}",
            )
            cls._last_value = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @classmethod
    def callback(cls, value: float, message: str = "", *, desc: str = "Processing") -> None:
        """Updates the progress bar with the given value and message.

        This method ensures the progress bar is initialized (if not already)
        and updates its current value and postfix message. If the `value`
        reaches 100, the bar is automatically closed.

        Args:
            value: The current progress, a float between 0 and 100.
                It will be cast to an integer for display.
            message: An optional short status string to display next to the bar.
                Defaults to an empty string.
            desc: The description for the progress bar. This is only used
                when the bar is created for the first time. Defaults to
                "Processing".

        Example:
            >>> from femora.progress import Progress
            >>> Progress.callback(value=0, desc="File Transfer")
            File Transfer:   0%|          | 0/100 [...]
            >>> Progress.callback(value=25, message="Downloading part A")
            File Transfer:  25%|██½       | 25/100 [...] Downloading part A
            >>> Progress.callback(value=75, message="Verifying checksum")
            File Transfer:  75%|███████½  | 75/100 [...] Verifying checksum
            >>> Progress.callback(value=100, message="Complete")
            File Transfer: 100%|██████████| 100/100 [...] Complete
        """
        value_int = int(value)
        cls._ensure_bar(desc)
        if cls._bar is None:  # for type checkers
            return

        cls._bar.set_postfix_str(message)
        cls._bar.n = value_int
        cls._bar.refresh()
        cls._last_value = value_int

        if value_int >= 100:
            cls.close()

    # ------------------------------------------------------------------
    @classmethod
    def close(cls) -> None:
        """Closes the internal `tqdm` progress bar and resets its state.

        This method should be called explicitly if a progress operation is
        aborted or finishes without `value` reaching 100 (which automatically
        closes the bar). It ensures that no lingering `tqdm` bar remains open.

        Example:
            >>> from femora.progress import Progress
            >>> Progress.callback(value=0, desc="Long Operation")
            Long Operation:   0%|          | 0/100 [...]
            >>> # Some error occurs or operation is cancelled
            >>> Progress.close()
        """
        if cls._bar is not None:
            cls._bar.close()
            cls._bar = None
            cls._last_value = 0


# Convenience helpers --------------------------------------------------

def get_progress_callback(desc: str = "Processing") -> Callable[[float, str], None]:
    """Returns a pre-configured progress callback function.

    This function wraps `Progress.callback`, allowing a default description
    (`desc`) to be set once and then reused for subsequent progress updates
    without needing to pass `desc` every time.

    Args:
        desc: The default description string for the progress bar.
            This description is used when the progress bar is first initialized
            by the returned callback. Defaults to "Processing".

    Returns:
        A callable function `(value: float, message: str) -> None` that can
        be used to update the global progress bar.

    Example:
        >>> from femora.progress import get_progress_callback
        >>> export_progress = get_progress_callback(desc="Exporting Data")
        >>> export_progress(value=0, message="Starting export...")
        Exporting Data:   0%|          | 0/100 [...] Starting export...
        >>> export_progress(value=50, message="Writing chunks...")
        Exporting Data:  50%|█████     | 50/100 [...] Writing chunks...
        >>> export_progress(value=100, message="Export complete.")
        Exporting Data: 100%|██████████| 100/100 [...] Export complete.
    """

    def _cb(value: float, message: str = "") -> None:  # noqa: D401
        Progress.callback(value, message, desc=desc)

    return _cb