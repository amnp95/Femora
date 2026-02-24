from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QListWidget, QListWidgetItem, QCheckBox, QPushButton, QMessageBox
)
from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Mesh.meshPartInstance import SingleLineMesh, StructuredLineMesh
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
from femora.components.interface.interface_base import InterfaceBase


class EmbeddedInterfaceCreationDialog(QDialog):
    """A dialog for creating new EmbeddedBeamSolidInterface instances.

    This dialog allows users to define the properties of an embedded
    beam-solid interface, including selecting beam and solid MeshParts,
    and specifying numeric parameters like radius, penalization, etc.

    Attributes:
        name_edit (QLineEdit): Input field for the interface name.
        beam_combo (QComboBox): Dropdown for selecting the beam MeshPart.
        solid_list (QListWidget): Multi-select list for solid MeshParts.
        radius_edit (QLineEdit): Input field for the interface radius.
        n_peri_edit (QLineEdit): Input field for the number of elements
            around the beam perimeter.
        n_long_edit (QLineEdit): Input field for the number of elements
            along the beam length.
        penalty_edit (QLineEdit): Input field for the penalty parameter.
        gpenalty_chk (QCheckBox): Checkbox for the -gPenalty flag.
        created_interface (EmbeddedBeamSolidInterface or None): Stores
            the newly created interface instance upon successful creation.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QDialog
        >>> # A QApplication instance is typically required for Qt dialogs.
        >>> # app = QApplication([]) # Uncomment if running standalone
        >>>
        >>> dialog = EmbeddedInterfaceCreationDialog()
        >>> dialog.setWindowTitle("New Interface Dialog Demo")
        >>> # In a real application, you would populate inputs and call dialog.exec_()
        >>> dialog.close()
    """

    def __init__(self, parent=None):
        """Initializes the EmbeddedInterfaceCreationDialog.

        Args:
            parent (QWidget, optional): The parent widget for this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create Embedded Beam–Solid Interface")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI building
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QGridLayout()
        row = 0

        # Interface name
        form.addWidget(QLabel("Interface Name:"), row, 0)
        self.name_edit = QLineEdit()
        form.addWidget(self.name_edit, row, 1)
        row += 1

        # Beam MeshPart selector (single-line or structured-line meshes)
        form.addWidget(QLabel("Beam MeshPart:"), row, 0)
        self.beam_combo = QComboBox()
        beam_parts = [mp for mp in MeshPart.get_mesh_parts().values()
                      if isinstance(mp, (SingleLineMesh, StructuredLineMesh))]
        self._beam_lookup = {mp.user_name: mp for mp in beam_parts}
        self.beam_combo.addItems(self._beam_lookup.keys())
        form.addWidget(self.beam_combo, row, 1)
        row += 1

        # Solid MeshParts (multi-select – optional)
        form.addWidget(QLabel("Solid MeshParts (multi-select):"), row, 0, 1, 2)
        row += 1
        self.solid_list = QListWidget()
        self.solid_list.setSelectionMode(QListWidget.MultiSelection)
        solid_parts = [mp for mp in MeshPart.get_mesh_parts().values()
                       if mp.category.lower().startswith("volume")]
        for mp in solid_parts:
            self.solid_list.addItem(QListWidgetItem(mp.user_name))
        form.addWidget(self.solid_list, row, 0, 1, 2)
        row += 1

        # Numeric / flag parameters
        self.radius_edit = QLineEdit("0.5")
        self.n_peri_edit = QLineEdit("8")
        self.n_long_edit = QLineEdit("10")
        self.penalty_edit = QLineEdit("1.0e12")
        self.gpenalty_chk = QCheckBox("Use -gPenalty flag")
        self.gpenalty_chk.setChecked(True)

        for label, widget in (
            ("Radius", self.radius_edit),
            ("n_peri", self.n_peri_edit),
            ("n_long", self.n_long_edit),
            ("Penalty Param", self.penalty_edit),
        ):
            form.addWidget(QLabel(f"{label} :"), row, 0)
            form.addWidget(widget, row, 1)
            row += 1
        # gPenalty checkbox spans both columns
        form.addWidget(self.gpenalty_chk, row, 0, 1, 2)
        row += 1

        layout.addLayout(form)

        # Buttons
        btns = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self._create)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(create_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------
    def _create(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a unique interface name.")
            return
        if InterfaceBase.get(name):
            QMessageBox.warning(self, "Input Error", f"Interface '{name}' already exists.")
            return

        beam_mp = self._beam_lookup.get(self.beam_combo.currentText())
        if beam_mp is None:
            QMessageBox.warning(self, "Input Error", "Please select a beam MeshPart.")
            return

        solid_mps = [item.text() for item in self.solid_list.selectedItems()] or None
        try:
            radius = float(self.radius_edit.text())
            n_peri = int(self.n_peri_edit.text())
            n_long = int(self.n_long_edit.text())
            penalty_param = float(self.penalty_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Numeric fields are invalid.")
            return
        g_penalty = self.gpenalty_chk.isChecked()

        try:
            self.created_interface = EmbeddedBeamSolidInterface(
                name=name,
                beam_part=beam_mp,
                soild_parts=solid_mps,
                radius=radius,
                n_peri=n_peri,
                n_long=n_long,
                penalty_param=penalty_param,
                g_penalty=g_penalty,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self.accept()


class EmbeddedInterfaceEditDialog(QDialog):
    """A dialog for editing an existing EmbeddedBeamSolidInterface.

    This dialog displays the current properties of an embedded
    beam-solid interface and allows the user to modify parameters
    such as radius, penalization, and flags.

    Attributes:
        interface (EmbeddedBeamSolidInterface): The interface instance
            being edited.
        radius_edit (QLineEdit): Input field for the interface radius.
        n_peri_edit (QLineEdit): Input field for the number of elements
            around the beam perimeter.
        n_long_edit (QLineEdit): Input field for the number of elements
            along the beam length.
        penalty_edit (QLineEdit): Input field for the penalty parameter.
        gpenalty_chk (QCheckBox): Checkbox for the -gPenalty flag.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QDialog
        >>> from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
        >>> from femora.components.Mesh.meshPartBase import MeshPart
        >>>
        >>> # A QApplication instance is typically required for Qt dialogs.
        >>> # app = QApplication([]) # Uncomment if running standalone
        >>>
        >>> # Create a minimal mock MeshPart for the EmbeddedBeamSolidInterface
        >>> class MinimalMeshPart(MeshPart):
        ...     def __init__(self, name):
        ...         super().__init__()
        ...         self.user_name = name
        ...         # Do not add to global registry to avoid side effects
        ...
        >>> # Create a dummy EmbeddedBeamSolidInterface instance
        >>> # This requires a minimal setup for its constructor
        >>> dummy_beam_part = MinimalMeshPart("MockBeam")
        >>>
        >>> # A minimal mock for EmbeddedBeamSolidInterface if the actual class is not available
        >>> # or for simpler testing:
        >>> class MockEmbeddedBeamSolidInterface:
        ...     def __init__(self, name, beam_part, soild_parts, radius, n_peri, n_long, penalty_param, g_penalty):
        ...         self.name = name
        ...         self.beam_part = beam_part
        ...         self.soild_parts = soild_parts
        ...         self.radius = radius
        ...         self.n_peri = n_peri
        ...         self.n_long = n_long
        ...         self.penalty_param = penalty_param
        ...         self.g_penalty = g_penalty
        >>>
        >>> initial_interface = MockEmbeddedBeamSolidInterface(
        ...     name="ExampleEditInterface",
        ...     beam_part=dummy_beam_part,
        ...     soild_parts=["MockSolid1", "MockSolid2"],
        ...     radius=0.75,
        ...     n_peri=8,
        ...     n_long=10,
        ...     penalty_param=1.0e10,
        ...     g_penalty=False
        ... )
        >>>
        >>> dialog = EmbeddedInterfaceEditDialog(interface=initial_interface)
        >>> dialog.setWindowTitle("Edit Dialog Demo")
        >>> # In a real application, user would modify inputs and call dialog.exec_()
        >>> dialog.close()
    """

    def __init__(self, interface: EmbeddedBeamSolidInterface, parent=None):
        """Initializes the EmbeddedInterfaceEditDialog.

        Args:
            interface: The `EmbeddedBeamSolidInterface` instance to be edited.
            parent (QWidget, optional): The parent widget for this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.interface = interface
        self.setWindowTitle(f"Edit Interface – {interface.name}")
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QGridLayout()
        row = 0

        # Name (read-only)
        form.addWidget(QLabel("Name:"), row, 0)
        form.addWidget(QLabel(self.interface.name), row, 1)
        row += 1

        # Editable fields
        self.radius_edit = QLineEdit(str(self.interface.radius))
        self.n_peri_edit = QLineEdit(str(self.interface.n_peri))
        self.n_long_edit = QLineEdit(str(self.interface.n_long))
        self.penalty_edit = QLineEdit(str(self.interface.penalty_param))
        self.gpenalty_chk = QCheckBox("Use -gPenalty flag")
        self.gpenalty_chk.setChecked(self.interface.g_penalty)

        for label, widget in (
            ("Radius", self.radius_edit),
            ("n_peri", self.n_peri_edit),
            ("n_long", self.n_long_edit),
            ("Penalty Param", self.penalty_edit),
        ):
            form.addWidget(QLabel(f"{label} :"), row, 0)
            form.addWidget(widget, row, 1)
            row += 1
        form.addWidget(self.gpenalty_chk, row, 0, 1, 2)
        row += 1

        layout.addLayout(form)

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    # ------------------------------------------------------------------
    def _save(self):
        try:
            self.interface.radius = float(self.radius_edit.text())
            self.interface.n_peri = int(self.n_peri_edit.text())
            self.interface.n_long = int(self.n_long_edit.text())
            self.interface.penalty_param = float(self.penalty_edit.text())
            self.interface.g_penalty = self.gpenalty_chk.isChecked()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Numeric fields are invalid.")
            return
        self.accept()