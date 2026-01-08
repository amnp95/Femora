class AppStyles:
    """A central repository for application-wide QSS (Qt Style Sheet) styles.

    This class provides a consistent, luxurious theme with a sophisticated color
    palette and detailed styling for various Qt widgets, including main windows,
    buttons, input fields, combo boxes, tabs, menus, and progress bars.

    Attributes:
        COLORS (dict[str, str]): A dictionary defining a sophisticated color palette
            used throughout the application's styles.
        MAIN_STYLE (str): QSS for QMainWindow and QWidget, including elegant
            scrollbar styling for both vertical and horizontal orientations.
        BUTTON_STYLE (str): QSS for QPushButton, featuring luxurious gradient
            backgrounds and distinct hover and pressed states.
        INPUT_STYLE (str): QSS for QLineEdit, providing sophisticated focus and
            hover effects with a clear visual hierarchy.
        COMBOBOX_STYLE (str): QSS for QComboBox (dropdown), including styling for
            the dropdown button and the abstract item view.
        TAB_STYLE (str): QSS for QTabWidget and QTabBar, defining luxurious
            selected and hover states for tabs and the tab pane.
        MENU_STYLE (str): QSS for QMenuBar and QMenu, offering elegant styling for
            menu items, separators, and selected states.
        PROGRESS_STYLE (str): QSS for QProgressBar, featuring golden accents
            and a clear progress chunk visualization.
        COMBINED_STYLE (str): All individual style components concatenated into
            a single, comprehensive QSS string for easy application.

    Example:
        >>> from PyQt5.QtWidgets import QApplication
        >>> # Assuming AppStyles is in 'your_module'
        >>> # from your_module import AppStyles
        >>> app = QApplication([])
        >>> app.setStyleSheet(AppStyles.COMBINED_STYLE)
        >>> # Or with dynamic font size:
        >>> app.setStyleSheet(AppStyles.get_dynamic_style(font_size=12))
        >>> # Now your application widgets will display with these styles.
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
    def get_dynamic_style(font_size: int = 10):
        """Generates a combined style string including dynamic font sizing.

        This method integrates the base `COMBINED_STYLE` with global font settings
        and specific tooltip styling, allowing for customization of the base
        font size across the application.

        Args:
            font_size: The base font size in points to be applied to all widgets.
                Defaults to 10.

        Returns:
            str: A complete QSS string incorporating dynamic font size and the
                predefined application styles.

        Example:
            >>> from PyQt5.QtWidgets import QApplication
            >>> # Assuming AppStyles is in 'your_module'
            >>> # from your_module import AppStyles
            >>> app = QApplication([])
            >>> # Apply styles with a custom font size
            >>> app.setStyleSheet(AppStyles.get_dynamic_style(font_size=14))
            >>> # All widgets will now use a 14pt font.
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