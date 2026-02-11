import warnings
warnings.filterwarnings("ignore", message="sipPyTypeDict\(\) is deprecated", category=DeprecationWarning)

from qtpy.QtGui import QDrag, QPixmap, QColor, QPainter
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, 
    QListWidgetItem, QTabWidget, QDialog, QMessageBox, QMenu, QAction, 
    QAbstractItemView, QFrame, QSplitter, QApplication
)
from qtpy.QtCore import Qt, QMimeData, QPoint, QEvent, QDragEvent, QKeyEvent

from femora.components.Process.process import ProcessManager
from femora.components.Recorder.recorderBase import Recorder, RecorderManager
from femora.components.Analysis.analysis import Analysis, AnalysisManager
from femora.components.Pattern.patternBase import Pattern, PatternManager


class ComponentDragItem(QListWidgetItem):
    """Represents a draggable list item for a specific component.

    This item displays a component's name and tag and carries its
    identifier for drag-and-drop operations within the GUI.

    Attributes:
        tag (int): The unique integer ID of the component.
        component_type (str): The type of the component (e.g., 'Analysis', 'Recorder', 'Pattern').

    Example:
        >>> from qtpy.QtWidgets import QApplication, QListWidget
        >>> from femora.gui.process.process_gui_widgets import ComponentDragItem
        >>> app = QApplication([])
        >>> list_widget = QListWidget()
        >>> item = ComponentDragItem(tag=1, component_type="Analysis", name="Static Analysis")
        >>> list_widget.addItem(item)
        >>> print(item.text())
        Static Analysis (Tag: 1)
        >>> print(item.component_type)
        Analysis
        >>> app.quit()
    """

    def __init__(self, tag: int, component_type: str, name: str, parent: QListWidget = None):
        """Initializes the ComponentDragItem.

        Args:
            tag: The unique integer ID for the component.
            component_type: The type of the component (e.g., 'Analysis', 'Recorder', 'Pattern').
            name: The display name of the component.
            parent: The parent QListWidget of this item.
        """
        super().__init__(f"{name} (Tag: {tag})", parent)
        self.tag = tag
        self.component_type = component_type
        self.setToolTip(f"Drag to add {component_type} with tag {tag} to process")
        

class ComponentListWidget(QListWidget):
    """A QListWidget subclass that supports drag operations for components.

    This widget displays a list of available components of a specific type
    and allows them to be dragged and dropped into a process list.

    Attributes:
        component_type (str): The type of component managed by this list
            (e.g., 'Analysis', 'Recorder', 'Pattern').

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.gui.process.process_gui_widgets import ComponentListWidget, ComponentDragItem
        >>> app = QApplication([])
        >>> component_list = ComponentListWidget(component_type="Analysis")
        >>> item = ComponentDragItem(tag=1, component_type="Analysis", name="Static Analysis")
        >>> component_list.addItem(item)
        >>> print(component_list.count())
        1
        >>> app.quit()
    """

    def __init__(self, component_type: str, parent: QWidget = None):
        """Initializes the ComponentListWidget.
        
        Args:
            component_type: Type of component ('Analysis', 'Recorder' or 'Pattern').
            parent: The parent widget.
        """
        super().__init__(parent)
        self.component_type = component_type
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
    def startDrag(self, supportedActions: Qt.DropActions):
        """Starts a drag operation when an item is dragged from the list.

        Args:
            supportedActions: The supported drop actions (e.g., Qt.CopyAction).
        """
        item = self.currentItem()
        if not item:
            return
            
        # Create mime data
        mimeData = QMimeData()
        mimeData.setText(f"{self.component_type}:{item.tag}")
        
        # Create drag object
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        
        # Create a pixmap for the drag icon
        pixmap = QPixmap(200, 30)
        pixmap.fill(QColor(230, 230, 250))  # Light lavender color
        
        # Add text to the pixmap
        painter = QPainter(pixmap)
        painter.drawText(10, 20, f"{self.component_type}: {item.tag}")
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(10, 15))
        
        # Execute drag - Replace exec_ with exec to fix deprecation warning
        result = drag.exec(Qt.CopyAction)


class ProcessListWidget(QListWidget):
    """A QListWidget subclass that displays process steps and supports drop operations.

    This widget allows users to drag and drop components (Analysis, Recorder, Pattern)
    from other lists into its own list to build a sequential process.
    It also supports removing steps via context menu or Delete key.

    Attributes:
        process_manager (ProcessManager): An instance of ProcessManager to manage
            the underlying process steps.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from qtpy.QtCore import QMimeData, Qt
        >>> from femora.gui.process.process_gui_widgets import ProcessListWidget
        >>> from femora.components.Analysis.analysis import AnalysisManager
        >>> from femora.components.Analysis.constraint_handlers import ConstraintHandlerManager
        >>> from femora.components.Analysis.numberers import NumbererManager
        >>> from femora.components.Analysis.systems import SystemManager
        >>> from femora.components.Analysis.algorithms import AlgorithmManager
        >>> from femora.components.Analysis.convergenceTests import TestManager
        >>> from femora.components.Analysis.integrators import IntegratorManager
        >>> app = QApplication([])
        >>> process_list = ProcessListWidget()
        >>> # Set up a mock Analysis for the example to work
        >>> analysis_manager = AnalysisManager()
        >>> if not analysis_manager.get_all_analyses():
        >>>     constraint_handler = ConstraintHandlerManager().create_handler("transformation")
        >>>     numberer = NumbererManager().get_numberer("rcm")
        >>>     system = SystemManager().create_system("bandspd")
        >>>     algorithm = AlgorithmManager().create_algorithm("newton")
        >>>     test = TestManager().create_test("normunbalance", tol=1e-6, max_iter=100)
        >>>     integrator = IntegratorManager().create_integrator("loadcontrol", incr=0.1)
        >>>     analysis_manager.create_analysis(
        ...         name="Test Analysis", analysis_type="Static",
        ...         constraint_handler=constraint_handler, numberer=numberer,
        ...         system=system, algorithm=algorithm, test=test,
        ...         integrator=integrator, num_steps=10
        ...     )
        >>> # Simulate a drop event for an Analysis component
        >>> mime_data = QMimeData()
        >>> mime_data.setText("Analysis:1")
        >>> event = type('DragDropEvent', (object,), {
        ...     'mimeData': lambda: mime_data,
        ...     'acceptProposedAction': lambda: None,
        ...     'source': lambda: None # Mock source, if needed by Qt
        ... })()
        >>> process_list.dropEvent(event)
        >>> print(process_list.count() > 0)
        True
        >>> app.quit()
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the ProcessListWidget.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Allow multiple selection
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def dragEnterEvent(self, event: QDragEvent):
        """Accepts drag events from component lists if they contain text data.

        Args:
            event: The QDragEvent.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event: QDragEvent):
        """Accepts move events for component drops if they contain text data.

        Args:
            event: The QDragEvent.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDragEvent):
        """Handles drop events to add components to the process.

        Parses the component type and tag from the mime data and adds the
        corresponding component to the internal process manager. The list
        is then refreshed.

        Args:
            event: The QDragEvent containing the component's mime data.
        """
        if event.mimeData().hasText():
            text = event.mimeData().text()
            component_type, tag = text.split(':')
            tag = int(tag)
            
            # Get the component based on type
            component = None
            description = ""
            
            if component_type == "Analysis":
                component = AnalysisManager().get_analysis(tag)
                if component:
                    description = f"Analysis: {component.name} ({component.analysis_type})"
            elif component_type == "Recorder":
                component = RecorderManager().get_recorder(tag)
                if component:
                    description = f"Recorder: {component.recorder_type}"
            elif component_type == "Pattern":
                component = PatternManager().get_pattern(tag)
                if component:
                    description = f"Pattern: {component.pattern_type}"
            
            if component:
                # Add to process manager
                self.process_manager.add_step(component, description)
                
                # Refresh the list
                self.refresh_process_list()
            
            event.acceptProposedAction()
    
    def refresh_process_list(self):
        """Clears the current list and re-populates it with steps from the process manager.
        """
        self.clear()
        
        # Add each step from the process manager
        for i, step in enumerate(self.process_manager.get_steps()):
            component_ref = step["component"]
            component = component_ref()  # Get the actual component from weak reference
            
            if component:
                # Create list item
                description = step["description"] or f"Step {i+1}"
                item = QListWidgetItem(f"{i+1}. {description}")
                item.setToolTip(f"Step {i+1}: {description}")
                self.addItem(item)
    
    def show_context_menu(self, position: QPoint):
        """Displays a context menu for selected process items.

        The menu currently includes an option to remove selected steps.

        Args:
            position: The position where the context menu was requested, in
                widget coordinates.
        """
        # Get selected items
        selected_items = self.selectedItems()
        if not selected_items:
            return
        
        # Create menu
        menu = QMenu()
        remove_action = QAction("Remove from process", self)
        remove_action.triggered.connect(self.remove_selected_steps)
        menu.addAction(remove_action)
        
        # Execute menu
        menu.exec(self.mapToGlobal(position))
    
    def remove_selected_steps(self):
        """Removes all currently selected steps from the process.

        The list is refreshed after removal.
        """
        # Get selected rows in reverse order (to avoid index shifting when removing)
        selected_rows = sorted([self.row(item) for item in self.selectedItems()], reverse=True)
        
        if not selected_rows:
            return
            
        for row in selected_rows:
            self.process_manager.remove_step(row)
        
        # Refresh list
        self.refresh_process_list()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handles key press events for the process list.

        Specifically, handles the 'Delete' key to remove selected steps.

        Args:
            event: The QKeyEvent generated by the key press.
        """
        if event.key() == Qt.Key_Delete:
            self.remove_selected_steps()
        else:
            # Pass other key events to parent class
            super().keyPressEvent(event)


class ProcessTab(QWidget):
    """A QWidget representing a tab for managing components of a specific type.

    This tab displays a list of available components (e.g., Analysis, Recorder, Pattern)
    and provides functionality to refresh the list and add selected components
    to the global process manager. It also supports drag-and-drop.

    Attributes:
        component_type (str): The type of component managed by this tab
            (e.g., 'Analysis', 'Recorder', 'Pattern').
        component_list (ComponentListWidget): The list widget displaying the
            available components of this type.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QTabWidget
        >>> from femora.gui.process.process_gui_widgets import ProcessTab
        >>> from femora.components.Analysis.analysis import AnalysisManager
        >>> from femora.components.Analysis.constraint_handlers import ConstraintHandlerManager
        >>> from femora.components.Analysis.numberers import NumbererManager
        >>> from femora.components.Analysis.systems import SystemManager
        >>> from femora.components.Analysis.algorithms import AlgorithmManager
        >>> from femora.components.Analysis.convergenceTests import TestManager
        >>> from femora.components.Analysis.integrators import IntegratorManager
        >>> app = QApplication([])
        >>> tabs = QTabWidget()
        >>> analysis_manager = AnalysisManager()
        >>> if not analysis_manager.get_all_analyses():
        ...     constraint_handler = ConstraintHandlerManager().create_handler("transformation")
        ...     numberer = NumbererManager().get_numberer("rcm")
        ...     system = SystemManager().create_system("bandspd")
        ...     algorithm = AlgorithmManager().create_algorithm("newton")
        ...     test = TestManager().create_test("normunbalance", tol=1e-6, max_iter=100)
        ...     integrator = IntegratorManager().create_integrator("loadcontrol", incr=0.1)
        ...     analysis_manager.create_analysis(
        ...         name="Test Analysis", analysis_type="Static",
        ...         constraint_handler=constraint_handler, numberer=numberer,
        ...         system=system, algorithm=algorithm, test=test,
        ...         integrator=integrator, num_steps=10
        ...     )
        >>> analysis_tab = ProcessTab("Analysis")
        >>> tabs.addTab(analysis_tab, "Analysis")
        >>> analysis_tab.refresh_components()
        >>> print(analysis_tab.component_list.count() > 0)
        True
        >>> app.quit()
    """

    def __init__(self, component_type: str, parent: QWidget = None):
        """Initializes the ProcessTab.
        
        Args:
            component_type: Type of component ('Analysis', 'Recorder' or 'Pattern').
            parent: The parent widget.
        """
        super().__init__(parent)
        self.component_type = component_type
        self.init_ui()
    
    def init_ui(self):
        """Initializes the user interface elements for the tab.
        """
        layout = QVBoxLayout(self)
        
        # Label
        label = QLabel(f"Available {self.component_type} Components")
        layout.addWidget(label)
        
        # Component list
        self.component_list = ComponentListWidget(self.component_type)
        layout.addWidget(self.component_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_components)
        layout.addWidget(refresh_btn)
        
        # Add button (alternative to drag-and-drop)
        add_btn = QPushButton(f"Add Selected {self.component_type} to Process")
        add_btn.clicked.connect(self.add_to_process)
        layout.addWidget(add_btn)
        
        # Initial refresh
        self.refresh_components()
    
    def refresh_components(self):
        """Refreshes the list of components displayed in the `component_list`.

        It retrieves components from their respective managers based on
        `self.component_type` and populates the list.
        """
        self.component_list.clear()
        
        if self.component_type == "Analysis":
            # Get analyses from the manager
            manager = AnalysisManager()
            for tag, analysis in manager.get_all_analyses().items():
                item = ComponentDragItem(tag, self.component_type, analysis.name)
                self.component_list.addItem(item)
        
        elif self.component_type == "Recorder":
            # Get recorders from the manager
            manager = RecorderManager()
            for tag, recorder in manager.get_all_recorders().items():
                item = ComponentDragItem(tag, self.component_type, recorder.recorder_type)
                self.component_list.addItem(item)
        
        elif self.component_type == "Pattern":
            # Get patterns from the manager
            manager = PatternManager()
            for tag, pattern in manager.get_all_patterns().items():
                item = ComponentDragItem(tag, self.component_type, pattern.pattern_type)
                self.component_list.addItem(item)
    
    def add_to_process(self):
        """Adds the currently selected component from the list to the process.

        This method serves as an alternative to the drag-and-drop functionality.
        If no component is selected, a warning message is displayed.
        """
        selected_items = self.component_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", f"Please select a {self.component_type} to add to process")
            return
        
        item = selected_items[0]
        tag = item.tag
        
        # Get component
        component = None
        description = ""
        
        if self.component_type == "Analysis":
            component = AnalysisManager().get_analysis(tag)
            if component:
                description = f"Analysis: {component.name} ({component.analysis_type})"
        elif self.component_type == "Recorder":
            component = RecorderManager().get_recorder(tag)
            if component:
                description = f"Recorder: {component.recorder_type}"
        elif self.component_type == "Pattern":
            component = PatternManager().get_pattern(tag)
            if component:
                description = f"Pattern: {component.pattern_type}"
        
        if component:
            # Add to process manager
            ProcessManager().add_step(component, description)
            
            # Notify parent to refresh process list - Get the main dialog (window)
            parent_dialog = self.window()
            if hasattr(parent_dialog, 'refresh_process_panel'):
                parent_dialog.refresh_process_panel()


class ProcessGUI(QDialog):
    """Main dialog for the Femora process management graphical user interface.

    This dialog provides an interface for users to build a simulation process
    by dragging and dropping or adding components (Analysis, Recorder, Pattern)
    into a sequential list. It allows managing and visualizing the steps
    of a Femora analysis.

    Attributes:
        process_manager (ProcessManager): An instance of ProcessManager to
            manage the underlying process steps.
        tabs (QTabWidget): The tab widget containing lists of available
            component types.
        analysis_tab (ProcessTab): The tab for managing Analysis components.
        recorder_tab (ProcessTab): The tab for managing Recorder components.
        pattern_tab (ProcessTab): The tab for managing Pattern components.
        process_list (ProcessListWidget): The list widget displaying the
            current sequence of process steps.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.gui.process.process_gui_widgets import ProcessGUI
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> gui = ProcessGUI()
        >>> # gui.show() # This would open the window, but we don't want to block tests.
        >>> print(gui.windowTitle())
        Process Manager
        >>> # To make the process_list show items, one would typically add components
        >>> # For example, simulating an add:
        >>> # gui.analysis_tab.component_list.setCurrentRow(0) # Select first analysis
        >>> # gui.analysis_tab.add_to_process()
        >>> gui.process_list.refresh_process_list() # Ensure it's populated if components exist
        >>> app.quit()
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the ProcessGUI dialog.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Process Manager")
        self.resize(900, 600)
        self.process_manager = ProcessManager()
        self.init_ui()
    
    def init_ui(self):
        """Initializes the main user interface elements for the dialog.

        This sets up the splitter, component tabs, process list, and control buttons.
        """
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)
        
        # Top panel (component types)
        top_panel = QFrame()
        top_layout = QVBoxLayout(top_panel)
        
        # Create tabs for different component types
        self.tabs = QTabWidget()
        
        # Add tabs for component types
        self.analysis_tab = ProcessTab("Analysis")
        self.recorder_tab = ProcessTab("Recorder")
        self.pattern_tab = ProcessTab("Pattern")
        
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.recorder_tab, "Recorders")
        self.tabs.addTab(self.pattern_tab, "Patterns")
        
        top_layout.addWidget(self.tabs)
        
        # Bottom panel (process steps)
        bottom_panel = QFrame()
        bottom_layout = QVBoxLayout(bottom_panel)
        
        bottom_layout.addWidget(QLabel("Process Steps (Drop Components Here or Select and Delete)"))
        
        # Process list
        self.process_list = ProcessListWidget()
        bottom_layout.addWidget(self.process_list)
        
        # Control buttons - Removed run process button
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear All Steps")
        clear_btn.clicked.connect(self.clear_process)
        button_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("Refresh Process List")
        refresh_btn.clicked.connect(self.refresh_process_panel)
        button_layout.addWidget(refresh_btn)
        
        bottom_layout.addLayout(button_layout)
        
        # Add panels to splitter
        splitter.addWidget(top_panel)
        splitter.addWidget(bottom_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([250, 350])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Initial refresh
        self.refresh_process_panel()
    
    def refresh_process_panel(self):
        """Refreshes the display of the process steps list.
        """
        self.process_list.refresh_process_list()
    
    def clear_process(self):
        """Clears all steps from the process manager after user confirmation.

        The process list is then refreshed.
        """
        reply = QMessageBox.question(
            self, 'Clear Process',
            "Are you sure you want to clear all process steps?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.process_manager.clear_steps()
            self.refresh_process_panel()


# Run as standalone for testing
if __name__ == "__main__":
    import sys
    
    # Create some sample components for testing
    recorder_manager = RecorderManager()
    analysis_manager = AnalysisManager()
    pattern_manager = PatternManager()
    
    # Create sample recorders
    from femora.components.Recorder.recorderBase import NodeRecorder, VTKHDFRecorder
    recorder1 = NodeRecorder(file_name="disp.out", nodes=[1, 2, 3], dofs=[1, 2], resp_type="disp")
    recorder2 = VTKHDFRecorder(file_base_name="results", resp_types=["disp", "vel"])
    
    # Create sample patterns
    try:
        from femora.components.TimeSeries.timeSeriesBase import TimeSeries, TimeSeriesManager
        from femora.components.Pattern.patternBase import UniformExcitation, H5DRMPattern
        
        # Create a sample time series
        time_series = TimeSeriesManager().create_time_series("Path", filePath="accel.dat", fileTime="accel.time" )
        
        # Create a sample UniformExcitation pattern
        pattern1 = pattern_manager.create_pattern("uniformexcitation", 
                                                dof=1, 
                                                time_series=time_series,
                                                vel0=0.0,
                                                factor=1.0)
        
        # Create a sample H5DRM pattern
        pattern2 = pattern_manager.create_pattern("h5drm",
                                                filepath="/path/to/drm_data.h5",
                                                factor=1.0,
                                                crd_scale=1.0,
                                                distance_tolerance=0.1,
                                                do_coordinate_transformation=0,
                                                transform_matrix=[1,0,0, 0,1,0, 0,0,1],
                                                origin=[0,0,0])
    except Exception as e:
        print(f"Error creating pattern components: {e}")
    
    # Create sample analyses (Note: This is simplified as actual Analysis objects require many components)
    # In a real implementation, you would create proper Analysis objects with all required components
    try:
        from femora.components.Analysis.constraint_handlers import ConstraintHandlerManager
        from femora.components.Analysis.numberers import NumbererManager
        from femora.components.Analysis.systems import SystemManager
        from femora.components.Analysis.algorithms import AlgorithmManager
        from femora.components.Analysis.convergenceTests import TestManager
        from femora.components.Analysis.integrators import IntegratorManager
        
        # Create components for analysis
        constraint_handler = ConstraintHandlerManager().create_handler("transformation")
        numberer = NumbererManager().get_numberer("rcm")
        system = SystemManager().create_system("bandspd")
        algorithm = AlgorithmManager().create_algorithm("newton")
        test = TestManager().create_test("normunbalance", tol=1e-6, max_iter=100)
        integrator = IntegratorManager().create_integrator("loadcontrol", incr=0.1)
        
        # Create analysis
        analysis1 = AnalysisManager().create_analysis(
            name="Gravity Analysis", 
            analysis_type="Static",
            constraint_handler=constraint_handler,
            numberer=numberer,
            system=system,
            algorithm=algorithm,
            test=test,
            integrator=integrator,
            num_steps=10
        )
    except Exception as e:
        print(f"Error creating analysis components: {e}")
    
    app = QApplication(sys.argv)
    gui = ProcessGUI()
    gui.show()
    sys.exit(app.exec())