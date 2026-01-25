from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel, QTabWidget
)
from femora.components.transformation.transformation import GeometricTransformation2D, GeometricTransformation3D

class TransformationWidget2D(QWidget):
    """Widget for configuring a 2D geometric transformation.

    This widget provides input fields for selecting the type of 2D
    transformation (Linear, PDelta, Corotational) and defining
    the relative displacements at the 'i' and 'j' nodes.

    Attributes:
        type_combo (QComboBox): Dropdown for selecting transformation type.
        d_xi (QDoubleSpinBox): Displacement component in x-direction at node i.
        d_yi (QDoubleSpinBox): Displacement component in y-direction at node i.
        d_xj (QDoubleSpinBox): Displacement component in x-direction at node j.
        d_yj (QDoubleSpinBox): Displacement component in y-direction at node j.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> # Assuming this file is part of femora.gui.transformation.transformation_widgets
        >>> from femora.gui.transformation.transformation_widgets import TransformationWidget2D
        >>> app = QApplication([])
        >>> widget = TransformationWidget2D()
        >>> widget.d_xi.setValue(0.1)
        >>> widget.d_yj.setValue(-0.05)
        >>> transformation = widget.get_transformation()
        >>> print(transformation.transf_type)
        Linear
        >>> app.quit()
    """
    def __init__(self, parent=None):
        """Initializes the TransformationWidget2D.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Linear", "PDelta", "Corotational"])
        form.addRow(QLabel("Type:"), self.type_combo)
        self.d_xi = QDoubleSpinBox(); self.d_xi.setRange(-1e6, 1e6)
        self.d_yi = QDoubleSpinBox(); self.d_yi.setRange(-1e6, 1e6)
        self.d_xj = QDoubleSpinBox(); self.d_xj.setRange(-1e6, 1e6)
        self.d_yj = QDoubleSpinBox(); self.d_yj.setRange(-1e6, 1e6)
        form.addRow("dXi:", self.d_xi)
        form.addRow("dYi:", self.d_yi)
        form.addRow("dXj:", self.d_xj)
        form.addRow("dYj:", self.d_yj)
        self.layout().addLayout(form)

    def get_transformation(self):
        """Retrieves the configured 2D geometric transformation object.

        Returns:
            GeometricTransformation2D: The 2D transformation object based on
                the current widget settings.
        """
        return GeometricTransformation2D(
            self.type_combo.currentText(),
            self.d_xi.value(),
            self.d_yi.value(),
            self.d_xj.value(),
            self.d_yj.value()
        )

class TransformationWidget3D(QWidget):
    """Widget for configuring a 3D geometric transformation.

    This widget provides input fields for selecting the type of 3D
    transformation (Linear, PDelta, Corotational), defining the orientation
    of the local x-z plane (vecXZ), and specifying the relative displacements
    at the 'i' and 'j' nodes.

    Attributes:
        type_combo (QComboBox): Dropdown for selecting transformation type.
        vecxz_x (QDoubleSpinBox): X-component of the vector defining the
            local x-z plane.
        vecxz_y (QDoubleSpinBox): Y-component of the vector defining the
            local x-z plane.
        vecxz_z (QDoubleSpinBox): Z-component of the vector defining the
            local x-z plane.
        d_xi (QDoubleSpinBox): Displacement component in x-direction at node i.
        d_yi (QDoubleSpinBox): Displacement component in y-direction at node i.
        d_zi (QDoubleSpinBox): Displacement component in z-direction at node i.
        d_xj (QDoubleSpinBox): Displacement component in x-direction at node j.
        d_yj (QDoubleSpinBox): Displacement component in y-direction at node j.
        d_zj (QDoubleSpinBox): Displacement component in z-direction at node j.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.transformation.transformation import GeometricTransformation3D
        >>> # Assuming this file is part of femora.gui.transformation.transformation_widgets
        >>> from femora.gui.transformation.transformation_widgets import TransformationWidget3D
        >>> app = QApplication([])
        >>> widget = TransformationWidget3D()
        >>> widget.type_combo.setCurrentText("Corotational")
        >>> widget.d_zi.setValue(0.2)
        >>> transformation = widget.get_transformation()
        >>> print(transformation.transf_type)
        Corotational
        >>> # Demonstrate loading a transformation
        >>> existing_transf = GeometricTransformation3D('PDelta', 0, 0, -1, 0.1, 0, 0, 0, 0.05, 0)
        >>> widget.load_transformation(existing_transf)
        >>> print(widget.d_xi.value())
        0.1
        >>> app.quit()
    """
    def __init__(self, parent=None):
        """Initializes the TransformationWidget3D.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Linear", "PDelta", "Corotational"])
        form.addRow(QLabel("Type:"), self.type_combo)
        self.vecxz_x = QDoubleSpinBox(); self.vecxz_x.setRange(-1e6, 1e6); self.vecxz_x.setValue(0)
        self.vecxz_y = QDoubleSpinBox(); self.vecxz_y.setRange(-1e6, 1e6); self.vecxz_y.setValue(0)
        self.vecxz_z = QDoubleSpinBox(); self.vecxz_z.setRange(-1e6, 1e6); self.vecxz_z.setValue(-1)
        self.d_xi = QDoubleSpinBox(); self.d_xi.setRange(-1e6, 1e6)
        self.d_yi = QDoubleSpinBox(); self.d_yi.setRange(-1e6, 1e6)
        self.d_zi = QDoubleSpinBox(); self.d_zi.setRange(-1e6, 1e6)
        self.d_xj = QDoubleSpinBox(); self.d_xj.setRange(-1e6, 1e6)
        self.d_yj = QDoubleSpinBox(); self.d_yj.setRange(-1e6, 1e6)
        self.d_zj = QDoubleSpinBox(); self.d_zj.setRange(-1e6, 1e6)
        form.addRow("vecXZ X:", self.vecxz_x)
        form.addRow("vecXZ Y:", self.vecxz_y)
        form.addRow("vecXZ Z:", self.vecxz_z)
        form.addRow("dXi:", self.d_xi)
        form.addRow("dYi:", self.d_yi)
        form.addRow("dZi:", self.d_zi)
        form.addRow("dXj:", self.d_xj)
        form.addRow("dYj:", self.d_yj)
        form.addRow("dZj:", self.d_zj)
        self.layout().addLayout(form)

    def get_transformation(self):
        """Retrieves the configured 3D geometric transformation object.

        Returns:
            GeometricTransformation3D: The 3D transformation object based on
                the current widget settings.
        """
        return GeometricTransformation3D(
            self.type_combo.currentText(),
            self.vecxz_x.value(),
            self.vecxz_y.value(),
            self.vecxz_z.value(),
            self.d_xi.value(),
            self.d_yi.value(),
            self.d_zi.value(),
            self.d_xj.value(),
            self.d_yj.value(),
            self.d_zj.value()
        )
    
    def load_transformation(self, transformation):
        """Loads transformation parameters into the widget.

        If `transformation` is None, the widget's fields are not modified.
        Otherwise, the widget fields are updated to reflect the properties
        of the provided transformation object.

        Args:
            transformation (GeometricTransformation3D or None): The 3D transformation
                object to load, or None to do nothing.
        """
        if transformation is None:
            return
        self.type_combo.setCurrentText(getattr(transformation, 'transf_type', 'Linear'))
        self.vecxz_x.setValue(getattr(transformation, 'vecxz_x', 0))
        self.vecxz_y.setValue(getattr(transformation, 'vecxz_y', 0))
        self.vecxz_z.setValue(getattr(transformation, 'vecxz_z', -1))
        self.d_xi.setValue(getattr(transformation, 'd_xi', 0))
        self.d_yi.setValue(getattr(transformation, 'd_yi', 0))
        self.d_zi.setValue(getattr(transformation, 'd_zi', 0))
        self.d_xj.setValue(getattr(transformation, 'd_xj', 0))
        self.d_yj.setValue(getattr(transformation, 'd_yj', 0))
        self.d_zj.setValue(getattr(transformation, 'd_zj', 0))

# Optionally, you can keep the following demo for manual testing:
if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    tabs = QTabWidget()
    tabs.addTab(TransformationWidget2D(), "2D Transformation")
    tabs.addTab(TransformationWidget3D(), "3D Transformation")
    tabs.show()
    sys.exit(app.exec_())