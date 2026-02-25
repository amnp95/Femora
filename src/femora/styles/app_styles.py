class AppStyles:
    """Defines a collection of sophisticated styles and a color palette for a UI application.

    This class provides a curated set of QSS (Qt Style Sheets) for various
    Qt widgets, designed with a luxurious aesthetic. It centralizes color
    definitions and style rules for consistency across the application.

    Attributes:
        COLORS (dict[str, str]): A comprehensive color palette with descriptive names
            and their hexadecimal or RGBA values.
        MAIN_STYLE (str): Base styling for `QMainWindow` and `QWidget`, including
            custom scrollbar designs.
        BUTTON_STYLE (str): Styling rules for `QPushButton` widgets, featuring
            gradients and hover/pressed states.
        INPUT_STYLE (str): Styling rules for `QLineEdit` widgets, including
            focus and hover effects.
        COMBOBOX_STYLE (str): Styling rules for `QComboBox` widgets and their
            dropdown views.
        TAB_STYLE (str): Styling rules for `QTabWidget` panes and `QTabBar`
            tabs, including selected and hover states.
        MENU_STYLE (str): Styling rules for `QMenuBar` and `QMenu` widgets,
            including item selection and separators.
        PROGRESS_STYLE (str): Styling rules for `QProgressBar` widgets,
            featuring gradient chunks.
        COMBINED_STYLE (str): All individual QSS style components combined
            into a single string for easy application.

    Example:
        >>> from PySide6.QtWidgets import QApplication, QWidget
        >>> from AppStyles import AppStyles # Assuming AppStyles is in current scope
        >>> app = QApplication([])
        >>> widget = QWidget()
        >>> widget.setStyleSheet(AppStyles.COMBINED_STYLE)
        >>> # To use a specific color:
        >>> print(AppStyles.COLORS['royal_gold'])
        #FFD700
    """
    # Sophisticated color palette with gradient possibilities
    COLORS = {
        'royal_gold': '#FFD700',
        'soft_gold': '#F0E68C',
        'deep_purple': '#2C1810',
        'elegant_purple': '#4A154B',
        'midnight': '#1A1B35',
        'twilight': '#2D2E4E',
        'cream': '#FFFAF0',
        'pearl': '#F5F5F5',
        'rose_gold': '#B76E79',
        'silver': '#E8E8E8',
        'charcoal': '#36454F',
        'shadow': 'rgba(0, 0, 0, 0.1)'
    }

    # Main styling with luxurious details
    MAIN_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {COLORS['midnight']};
        color: {COLORS['cream']};
    }}

    /* Elegant Scrollbars */
    QScrollBar:vertical {{
        background: {COLORS['twilight']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['soft_gold']}
        );
        min-height: 20px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {COLORS['twilight']};
        height: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['soft_gold']}
        );
        min-width: 20px;
        border-radius: 6px;
        margin: 2px;
    }}
    """

    # Luxurious button styling
    BUTTON_STYLE = f"""
    QPushButton {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['twilight']},
            stop:1 {COLORS['midnight']}
        );
        color: {COLORS['cream']};
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: bold;
        min-width: 100px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    QPushButton:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['soft_gold']}
        );
        color: {COLORS['midnight']};
        border: 2px solid {COLORS['royal_gold']};
    }}

    QPushButton:pressed {{
        background: {COLORS['deep_purple']};
        color: {COLORS['royal_gold']};
        border: 2px solid {COLORS['royal_gold']};
        padding-top: 12px;
        padding-left: 22px;
    }}
    """

    # Sophisticated input field styling
    INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {COLORS['twilight']};
        color: {COLORS['cream']};
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        padding: 8px 12px;
        selection-background-color: {COLORS['rose_gold']};
        selection-color: {COLORS['cream']};
    }}

    QLineEdit:focus {{
        border: 2px solid {COLORS['royal_gold']};
        background-color: {COLORS['midnight']};
    }}

    QLineEdit:hover {{
        border: 2px solid {COLORS['soft_gold']};
    }}
    """

    # Elegant ComboBox (Dropdown) styling
    COMBOBOX_STYLE = f"""
    QComboBox {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['twilight']},
            stop:1 {COLORS['midnight']}
        );
        color: {COLORS['cream']};
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        padding: 8px 12px;
        min-width: 100px;
    }}

    QComboBox:hover {{
        border: 2px solid {COLORS['royal_gold']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox::down-arrow {{
        image: url(down_arrow.png);
        width: 12px;
        height: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['midnight']};
        color: {COLORS['cream']};
        selection-background-color: {COLORS['rose_gold']};
        selection-color: {COLORS['midnight']};
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        padding: 4px;
    }}
    """

    # Luxurious Tab styling
    TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        background: {COLORS['midnight']};
        top: -2px;
    }}

    QTabBar::tab {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['twilight']},
            stop:1 {COLORS['midnight']}
        );
        color: {COLORS['cream']};
        border: 2px solid {COLORS['rose_gold']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 15px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['soft_gold']}
        );
        color: {COLORS['midnight']};
        border: 2px solid {COLORS['royal_gold']};
        border-bottom: none;
    }}

    QTabBar::tab:hover:!selected {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['twilight']},
            stop:1 {COLORS['elegant_purple']}
        );
        border: 2px solid {COLORS['soft_gold']};
        border-bottom: none;
    }}
    """

    # Elegant Menu styling
    MENU_STYLE = f"""
    QMenuBar {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['midnight']},
            stop:1 {COLORS['twilight']}
        );
        color: {COLORS['cream']};
        border-bottom: 2px solid {COLORS['rose_gold']};
        padding: 4px;
    }}

    QMenuBar::item:selected {{
        background: {COLORS['rose_gold']};
        color: {COLORS['midnight']};
        border-radius: 4px;
    }}

    QMenu {{
        background-color: {COLORS['midnight']};
        color: {COLORS['cream']};
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        padding: 5px;
    }}

    QMenu::item {{
        padding: 8px 25px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['soft_gold']}
        );
        color: {COLORS['midnight']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {COLORS['rose_gold']};
        margin: 5px 15px;
    }}
    """

    # Progress Bar with golden accents
    PROGRESS_STYLE = f"""
    QProgressBar {{
        border: 2px solid {COLORS['rose_gold']};
        border-radius: 8px;
        text-align: center;
        color: {COLORS['cream']};
        background-color: {COLORS['midnight']};
    }}

    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['rose_gold']},
            stop:1 {COLORS['royal_gold']}
        );
        border-radius: 6px;
    }}
    """

    # Combine all styles
    COMBINED_STYLE = (
        MAIN_STYLE +
        BUTTON_STYLE +
        INPUT_STYLE +
        COMBOBOX_STYLE +
        TAB_STYLE +
        MENU_STYLE +
        PROGRESS_STYLE
    )

    @staticmethod
    def get_dynamic_style(font_size: int = 10) -> str:
        """Returns a combined QSS style string with a dynamically set font size.

        This method generates a comprehensive QSS stylesheet that includes all
        predefined styles from the AppStyles class, along with a global font
        family and size. It also adds styling for QToolTip widgets.

        Args:
            font_size: The base font size in points to apply globally to all
                widgets. Defaults to 10.

        Returns:
            A string containing the complete QSS style sheet.

        Example:
            >>> from PySide6.QtWidgets import QApplication, QWidget
            >>> from AppStyles import AppStyles # Assuming AppStyles is in current scope
            >>> app = QApplication([])
            >>> widget = QWidget()
            >>> # Apply a style with a custom font size
            >>> widget.setStyleSheet(AppStyles.get_dynamic_style(font_size=12))
        """
        return f"""
        * {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: {font_size}pt;
        }}

        QToolTip {{
            background-color: {AppStyles.COLORS['midnight']};
            color: {AppStyles.COLORS['cream']};
            border: 2px solid {AppStyles.COLORS['rose_gold']};
            border-radius: 4px;
            padding: 5px;
        }}
        """ + AppStyles.COMBINED_STYLE