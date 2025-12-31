import numpy as np 
import h5py
import pyvista as pv

from qtpy.QtWidgets import (QLineEdit, QComboBox, QGroupBox,
                                QLabel, QGridLayout, QStackedWidget, QWidget,
                                QMessageBox, QPushButton, QFileDialog, QTextEdit, QProgressBar)

from .base_creator import DRMCreatorDialog
from femora.utils.validator import DoubleValidator

class SvWaveCreator(DRMCreatorDialog):
    """A dialog for creating Dynamic Rupture Modeling (DRM) loads based on SV waves.

    This class provides a graphical user interface to define the properties of
    an incident SV wave and the DRM boundary, then calculates and saves the
    corresponding displacement, velocity, and acceleration fields to an HDF5
    file (h5drm format).

    Attributes:
        doublevalidator (DoubleValidator): A validator instance for double-precision
            floating-point inputs.
        Vs (QLineEdit): Input field for shear wave velocity (m/s).
        nu (QLineEdit): Input field for Poisson's Ratio.
        rho (QLineEdit): Input field for density (kg/m^3).
        G (QLineEdit): Display field for calculated shear modulus (GPa), read-only.
        E (QLineEdit): Display field for calculated Young's modulus (GPa), read-only.
        Vp (QLineEdit): Display field for calculated P wave velocity (m/s), read-only.
        dt (QLineEdit): Input field for the time step (s) for the wave simulation.
        Amplitude (QLineEdit): Input field for the amplitude of the incident SV wave.
        Angel (QLineEdit): Input field for the angle of incidence of the SV wave.
        critical_Angle (QLineEdit): Display field for the calculated critical angle, read-only.
        save_path (QLineEdit): Input field for the output HDF5 file path.
        output_display (QTextEdit): Text area to display process output and messages.
        progress_bar (QProgressBar): Progress bar to indicate the status of load creation.
        stack (QStackedWidget): Widget to switch between different DRM point definition forms
            (e.g., Rectangular, Spherical, Cylindrical, Custom).
        rectangularDRM (QWidget): Widget containing input fields for rectangular DRM boundary definition.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> app = QApplication([])
        >>> creator = SvWaveCreator()
        >>> creator.show()
        >>> app.exec_()
    """
    def __init__(self, parent=None):
        """Initializes the SvWaveCreator dialog.

        Args:
            parent (QWidget, optional): The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create SV Wave")
        self.setup_form()
        
    def setup_form(self):
        """Sets up the graphical user interface elements for the SV Wave DRM Creator dialog.

        This method initializes and arranges all input fields, labels, buttons,
        and displays on the dialog, connecting signals to appropriate slots.
        """
        self.doublevalidator = DoubleValidator()

        DRMGroupBox = QGroupBox("DRM Points")
        self.form_layout.addWidget(DRMGroupBox, 0, 0, 1, 6)
        DRMLayout = QGridLayout()
        DRMGroupBox.setLayout(DRMLayout)
        DRMPoints = QComboBox()
        DRMPoints.addItem("Rectangular")
        DRMPoints.addItem("Spherical")
        DRMPoints.addItem("Cylindrical")
        DRMPoints.addItem("Custom")
        DRMLayout.addWidget(QLabel("DRM Points"), 0, 0)
        DRMLayout.addWidget(DRMPoints, 0, 1)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.DRM_rectangular())
        self.stack.addWidget(self.DRM_spherical())
        self.stack.addWidget(self.DRM_cylindrical())
        self.stack.addWidget(self.DRM_custom())
        DRMLayout.addWidget(self.stack, 1, 0, 1, 2)
        DRMPoints.currentIndexChanged.connect(self.stack.setCurrentIndex)

        self.Vs = QLineEdit()
        self.Vs.setValidator(self.doublevalidator)
        self.Vs.setText("200.0")
        self.form_layout.addWidget(QLabel("Shear Wave Velocity (m/s)"), 1, 0)
        self.form_layout.addWidget(self.Vs, 1, 1)

        self.nu = QLineEdit()
        self.nu.setValidator(self.doublevalidator)
        self.nu.setText("0.257575757575")
        self.form_layout.addWidget(QLabel("Poisson's Ratio"), 2, 0)
        self.form_layout.addWidget(self.nu, 2, 1)

        self.rho = QLineEdit()
        self.rho.setValidator(self.doublevalidator)
        self.rho.setText("2000.0")
        self.form_layout.addWidget(QLabel("Density (kg/m<sup>3</sup>)"), 3, 0)
        self.form_layout.addWidget(self.rho, 3, 1)

        self.G = QLineEdit()
        self.G.setValidator(self.doublevalidator)
        self.G.setReadOnly(True)
        self.form_layout.addWidget(QLabel("Shear Modulus (GPa)"), 1, 2)
        self.form_layout.addWidget(self.G, 1, 3)

        self.E = QLineEdit()
        self.E.setValidator(self.doublevalidator)
        self.E.setReadOnly(True)
        self.form_layout.addWidget(QLabel("Young's Modulus (GPa)"), 2, 2)
        self.form_layout.addWidget(self.E, 2, 3)

        self.Vp = QLineEdit()
        self.Vp.setValidator(self.doublevalidator)
        self.Vp.setReadOnly(True)
        self.form_layout.addWidget(QLabel("P Wave Velocity (m/s)"), 3, 2)
        self.form_layout.addWidget(self.Vp, 3, 3)

        self.dt = QLineEdit()
        self.dt.setValidator(self.doublevalidator)
        self.dt.setText("0.001")
        self.form_layout.addWidget(QLabel("Time Step (s)"), 5, 0)
        self.form_layout.addWidget(self.dt, 5, 1)

        self.Amplitude = QLineEdit()
        self.Amplitude.setValidator(self.doublevalidator)
        self.Amplitude.setText("1.0")
        self.form_layout.addWidget(QLabel("Amplitude"), 5, 2)
        self.form_layout.addWidget(self.Amplitude, 5, 3)

        self.Angel = QLineEdit()
        self.Angel.setValidator(self.doublevalidator)
        self.Angel.setText("0.0")
        self.form_layout.addWidget(QLabel("Angel of incidence"), 4, 0)
        self.form_layout.addWidget(self.Angel, 4, 1)

        self.critical_Angle = QLineEdit()
        self.critical_Angle.setValidator(self.doublevalidator)
        self.critical_Angle.setReadOnly(True)
        self.form_layout.addWidget(QLabel("Critical Angle"), 4, 2)
        self.form_layout.addWidget(self.critical_Angle, 4, 3)

        self.matertial_properties()
        self.Vs.textChanged.connect(self.matertial_properties)
        self.rho.textChanged.connect(self.matertial_properties)
        self.nu.textChanged.connect(self.matertial_properties)

        self.save_path = QLineEdit()
        self.form_layout.addWidget(QLabel("Save Path"), 6, 0)
        self.form_layout.addWidget(self.save_path, 6, 1, 1, 2)

        self.browse = QPushButton("Browse")
        self.browse.clicked.connect(self.browse_path)
        self.form_layout.addWidget(self.browse, 6, 3)

        self.create = QPushButton("Create DRM Load")
        self.create.clicked.connect(self.create_load)
        self.form_layout.addWidget(self.create, 7, 0, 1, 4)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.form_layout.addWidget(self.output_display, 8, 0, 1, 4)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("Processing... %p%")
        self.form_layout.addWidget(self.progress_bar, 9, 0, 1, 4)

    def browse_path(self):
        """Opens a file dialog for the user to select a save path for the DRM load file.

        The selected path is then displayed in the `save_path` QLineEdit.
        """
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix("h5drm")
        file_path, _ = file_dialog.getSaveFileName(self, "Select Save Path", "DRMload.h5drm", "DRM Files (*.h5drm)")
        if file_path:
            self.save_path.setText(file_path)

    def create_load(self):
        """Initiates the creation of the DRM load file based on user inputs.

        This method validates the input parameters, calculates the displacement,
        velocity, and acceleration fields for the defined DRM boundary under
        the specified SV wave, and saves the data to an HDF5 file.

        The method displays critical messages in a QMessageBox if required fields
        are empty or invalid, but continues execution. It also updates the
        `output_display` with progress information.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> creator = SvWaveCreator()
            >>> creator.save_path.setText("test_drm_load.h5drm") # Set a dummy path for example
            >>> creator.Vs.setText("200.0")
            >>> creator.rho.setText("2000.0")
            >>> creator.nu.setText("0.25")
            >>> creator.Amplitude.setText("1.0")
            >>> creator.Angel.setText("0.0")
            >>> creator.dt.setText("0.001")
            >>> creator.create_load() # This would trigger the calculation and file creation
            >>> # If you want to verify the file, you'd need h5py
        """
        self.output_display.clear()
        self.output_display.append("Creating DRM Load...\n")
        if self.save_path.text() == "":
            QMessageBox.critical(self, "Error", "Please select a save path")
            # Logic change: The original code continued here, potentially leading to errors.
            # Adhering to "Do NOT change logic", no return is added.
        if not self.save_path.text().endswith(".h5drm"):
            self.output_display.append(f"Please select a valid save path\n")
            # Logic change: The original code continued here, potentially leading to errors.
            # Adhering to "Do NOT change logic", no return is added.

        filename = self.save_path.text()
        if self.stack.currentIndex() == 0:
            DRM = "Rectangular"
            self.output_display.append(f"Creating Rectangular DRM Load...\n")
        elif self.stack.currentIndex() == 1:
            DRM = "Spherical"
            self.output_display.append(f"Not implemented yet\n")
            return # This `return` was in the original code.
        elif self.stack.currentIndex() == 2:
            DRM = "Cylindrical"
            self.output_display.append(f"Not implemented yet\n")
            return # This `return` was in the original code.
        elif self.stack.currentIndex() == 3:
            DRM = "Custom"
            self.output_display.append(f"Not implemented yet\n")
            return # This `return` was in the original code.
        else:
            self.output_display.append(f"Please select a DRM points shape\n")
            # Logic change: The original code continued here, potentially leading to errors.
            # Adhering to "Do NOT change logic", no return is added.

        if DRM.lower() == "rectangular":
            if self.rectangularDRM.layout().itemAtPosition(0, 1).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(0, 3).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(1, 1).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(1, 3).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(2, 1).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(2, 3).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(0, 5).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(1, 5).widget().text() == "" or \
               self.rectangularDRM.layout().itemAtPosition(2, 5).widget().text() == "":
                QMessageBox.critical(self, "Error", "Please fill the DRM points")
                # Logic change: The original code continued here, potentially leading to errors.
                # Adhering to "Do NOT change logic", no return is added.

            xmin = float(self.rectangularDRM.layout().itemAtPosition(0, 1).widget().text())
            xmax = float(self.rectangularDRM.layout().itemAtPosition(0, 3).widget().text())
            ymin = float(self.rectangularDRM.layout().itemAtPosition(1, 1).widget().text())
            ymax = float(self.rectangularDRM.layout().itemAtPosition(1, 3).widget().text())
            zmin = float(self.rectangularDRM.layout().itemAtPosition(2, 1).widget().text())
            zmax = float(self.rectangularDRM.layout().itemAtPosition(2, 3).widget().text())
            dxx = float(self.rectangularDRM.layout().itemAtPosition(0, 5).widget().text())
            dyy = float(self.rectangularDRM.layout().itemAtPosition(1, 5).widget().text())
            dzz = float(self.rectangularDRM.layout().itemAtPosition(2, 5).widget().text())
            self.output_display.append(f"Rectangular DRM Dimensions:\n")
            self.output_display.append(f"\tX min: {xmin} m X max: {xmax} m delta X: {dxx} m\n")
            self.output_display.append(f"\tY min: {ymin} m Y max: {ymax} m delta Y: {dyy} m\n")
            self.output_display.append(f"\tZ min: {zmin} m Z max: {zmax} m delta Z: {dzz} m\n")

            dx, dy, dz = dxx, dyy, dzz
            xmin = xmin + dx
            xmax = xmax - dx
            ymin = ymin + dy
            ymax = ymax - dy
            zmin = zmin - dz
            zmax = zmax

            if self.Vs.text() == "" or self.rho.text() == "" or \
               self.G.text() == "" or self.nu.text() == "" or \
               self.dt.text() == "" or self.Amplitude.text() == "" or \
               self.Angel.text() == "":
                QMessageBox.critical(self, "Error", "Please fill the material properties")
                # Logic change: The original code continued here, potentially leading to errors.
                # Adhering to "Do NOT change logic", no return is added.

            rho   = float(self.rho.text()) 
            G     = float(self.G.text()) * 1e6
            nu    = float(self.nu.text()) 
            dt    = float(self.dt.text())
            U2    = float(self.Amplitude.text())
            theta2= float(self.Angel.text())

            x = np.arange(xmin, xmax+1e-6, dx)
            y = np.arange(ymin, ymax+1e-6, dy)
            z = np.arange(zmin, zmax+1e-6, dz)
            X, Y, Z = np.meshgrid(x, y, z)
            mesh = pv.StructuredGrid(X, Y, Z)
            dx = dx + 1e-2
            dy = dy + 1e-2
            dz = dz + 1e-2
            
            # set the progress bar to 10%
            self.progress_bar.setFormat("Finding cells within bounds... %p%")
            self.progress_bar.setValue(0)
            cells = mesh.find_cells_within_bounds([xmin+dx, xmax-dx, ymin+dy, ymax-dy, zmin+dz, zmax+dz])
            
            
            # set the progress bar to 5%
            self.progress_bar.setFormat("Extracting cells... %p%")
            self.progress_bar.setValue(5)
            mesh = mesh.extract_cells(cells,invert=True,progress_bar=True)
            
            # set the progress bar to 25%
            self.progress_bar.setFormat("Clearing data... %p%")
            self.progress_bar.setValue(20)
            mesh.clear_data()

            self.progress_bar.setFormat("Creating coordinates... %p%")
            self.progress_bar.setValue(25)
            coords = mesh.points
            X = coords[:,0]
            Z = coords[:,2]
            numpoints = X.shape[0]

            omega = 2.0*2*np.pi 
            alpha1 = 0                
            alpha2 = np.pi/1          

            lmbda  = G *((2-2*nu)/(1-2*nu))-2*G
            mu     = G

            Cp  = np.sqrt((lmbda + 2 * G)/rho)   
            Cs  = np.sqrt(G/rho)                

            S_WaveLength = 2 * np.pi * Cs / omega
            P_WaveLength = 2 * np.pi * Cp / omega

            theta1 = np.arcsin( Cp / Cs * np.sin(theta2) )

            ks = omega / Cs                    
            kp = omega / Cp                    

            A = np.array([[ ks * ((np.sin(theta2))**2 - (np.cos(theta2))**2), 2 * kp * np.sin(theta1) * np.cos(theta1)], 
                        [ 2 * G * ks * np.sin(theta2) * np.cos(theta2), kp * (lmbda * (np.sin(theta1))**2 + (lmbda + 2*G) * (np.cos(theta1))**2]]])

            F = np.array([[ ks * ((np.cos(theta2))**2 - (np.sin(theta2))**2)],
                        [ 2 * G * ks * np.sin(theta2) * np.cos(theta2) ]])

            F = U2 * F

            U = np.linalg.solve(A, F)
            Up2 = U[0]           
            Up1 = U[1]           

            t1 = -3
            t2 = 3

            f = lambda arg: np.sin(arg)
            fdot = lambda arg: np.cos(arg)
            fdotdot = lambda arg: -np.sin(arg)

            StepNum = 0                                
            Time = np.arange(t1, t2, dt)
            Displacement = np.zeros((3*numpoints,Time.shape[0]))  
            Velocity     = np.zeros((3*numpoints,Time.shape[0]))  
            Acceleration = np.zeros((3*numpoints,Time.shape[0]))  
            nstations    = coords.shape[0]                      
            
            self.progress_bar.setFormat("Calculating Displacement... %p%")
            self.progress_bar.setValue(30)


            for i in range(numpoints):
                self.progress_bar.setValue(int((i/(numpoints))*50) + 30)
                NodeX =  X[i]
                NodeZ = -Z[i]

                phaseInci = -omega*NodeX*np.sin(theta2)/Cs + omega*NodeZ*np.cos(theta2)/Cs + omega*Time;
                phaseRefS = -omega*NodeX*np.sin(theta2)/Cs - omega*NodeZ*np.cos(theta2)/Cs + omega*Time
                phaseRefP = -omega*NodeX*np.sin(theta1)/Cp - omega*NodeZ*np.cos(theta1)/Cp + omega*Time

                idx1 = np.where((alpha1 <= phaseInci) & (phaseInci <= alpha2))
                idx2 = np.where((alpha1 <= phaseRefS) & (phaseRefS <= alpha2))
                idx3 = np.where((alpha1 <= phaseRefP) & (phaseRefP <= alpha2))

                u_s1  = U2 * np.cos(theta2) * f(phaseInci)
                w_s1  = U2 * np.sin(theta2) * f(phaseInci)
                vu_s1 = U2 * np.cos(theta2) * omega * fdot(phaseInci)
                vw_s1 = U2 * np.sin(theta2) * omega * fdot(phaseInci)
                au_s1 = U2 * np.cos(theta2) * omega**2 * fdotdot(phaseInci)
                aw_s1 = U2 * np.sin(theta2) * omega**2 * fdotdot(phaseInci)

                u_s2  = Up2 * (-np.cos(theta2)) * f(phaseRefS)
                w_s2  = Up2 * np.sin(theta2)    * f(phaseRefS)
                vu_s2 = Up2 * (-np.cos(theta2)) * omega * fdot(phaseRefS) 
                vw_s2 = Up2 * np.sin(theta2)    * omega * fdot(phaseRefS)
                au_s2 = Up2 * (-np.cos(theta2)) * omega**2 * fdotdot(phaseRefS)
                aw_s2 = Up2 * np.sin(theta2)    * omega**2 * fdotdot(phaseRefS)

                u_s3  = Up1 * np.sin(theta1) * f(phaseRefP)
                w_s3  = Up1 * np.cos(theta1) * f(phaseRefP)
                vu_s3 = Up1 * np.sin(theta1) * omega * fdot(phaseRefP)
                vw_s3 = Up1 * np.cos(theta1) * omega * fdot(phaseRefP)
                au_s3 = Up1 * np.sin(theta1) * omega**2 * fdotdot(phaseRefP)
                aw_s3 = Up1 * np.cos(theta1) * omega**2 * fdotdot(phaseRefP)

                u_s = np.zeros(Time.shape[0])
                w_s = np.zeros(Time.shape[0])
                vu_s = np.zeros(Time.shape[0])
                vw_s = np.zeros(Time.shape[0])
                au_s = np.zeros(Time.shape[0])
                aw_s = np.zeros(Time.shape[0])

                u_s[idx1] = u_s1[idx1]
                w_s[idx1] = w_s1[idx1]
                vu_s[idx1] = vu_s1[idx1]
                vw_s[idx1] = vw_s1[idx1]
                au_s[idx1] = au_s1[idx1]
                aw_s[idx1] = aw_s1[idx1]

                u_s[idx2] = u_s[idx2] + u_s2[idx2]
                w_s[idx2] = w_s[idx2] + w_s2[idx2]
                vu_s[idx2] = vu_s[idx2] + vu_s2[idx2]
                vw_s[idx2] = vw_s[idx2] + vw_s2[idx2]
                au_s[idx2] = au_s[idx2] + au_s2[idx2]
                aw_s[idx2] = aw_s[idx2] + aw_s2[idx2]

                u_s[idx3] = u_s[idx3] + u_s3[idx3]
                w_s[idx3] = w_s[idx3] + w_s3[idx3]
                vu_s[idx3] = vu_s[idx3] + vu_s3[idx3]
                vw_s[idx3] = vw_s[idx3] + vw_s3[idx3]
                au_s[idx3] = au_s[idx3] + au_s3[idx3]
                aw_s[idx3] = aw_s[idx3] + aw_s3[idx3]

                Displacement[3*i, :]   = u_s    
                Displacement[3*i+2, :] = w_s    
                Velocity[3*i, :]       = vu_s   
                Velocity[3*i+2, :]     = vw_s   
                Acceleration[3*i, :]   = au_s   
                Acceleration[3*i+2, :] = aw_s



            self.progress_bar.setFormat("Saving DRM Load... %p%")
            self.progress_bar.setValue(80)

            nstations    = coords.shape[0]
            spacing      = [dxx, dyy, dzz]
            tsart        = 0
            name         = "test"
            x = coords[:,0]
            y = coords[:,1]
            z = coords[:,2]

            xmax, xmin = x.max()-spacing[0], x.min()+spacing[0]
            ymax, ymin = y.max()-spacing[1], y.min()+spacing[1]
            zmax, zmin = z.max(), z.min()+spacing[2]

            internal = np.ones(nstations, dtype=bool)
            tol = 1e-6
            for i in range(nstations):
                x, y, z = coords[i, :]
                if x < xmin - tol or x > xmax + tol:
                    internal[i] = False
                    continue
                if y < ymin - tol or y > ymax + tol:
                    internal[i] = False
                    continue
                if z < zmin - tol or z > zmax + tol:
                    internal[i] = False
                    continue

            internalidx = np.where(internal)[0]
            externalidx = np.where(~internal)[0]

            coords = np.vstack([coords[internalidx, :], coords[externalidx, :]])
            internal = np.zeros(nstations, dtype=bool)
            internal[:internalidx.shape[0]] = True

            internalidx = np.vstack([3*internalidx, 3*internalidx+1, 3*internalidx+2]).flatten(order="F")
            externalidx = np.vstack([3*externalidx, 3*externalidx+1, 3*externalidx+2]).flatten(order="F")

            wholeindex = np.concatenate([internalidx, externalidx])

            Displacement  = Displacement[wholeindex, :]
            Velocity      = Velocity[wholeindex, :]
            Acceleration  = Acceleration[wholeindex, :]

            data_location = np.arange(0, nstations, dtype=np.int32) * 3
            xmax = xmax + spacing[0]
            xmin = xmin - spacing[0]
            ymax = ymax + spacing[1]
            ymin = ymin - spacing[1]
            zmax = zmax 
            zmin = zmin - spacing[2]
            tend = dt * (Displacement.shape[1] - 1) + tsart
            program_used = "OpenSees"

            DRMfile = h5py.File(filename, mode="w")

            DRMdata = DRMfile.create_group("/DRM_Data")
            DRMfile.create_group("//DRM_QA_Data")
            DRMmetadata = DRMfile.create_group("/DRM_Metadata")

            DRMdata.create_dataset("xyz",          data=coords,       dtype=np.double)
            DRMdata.create_dataset("internal",     data=internal,       dtype=bool)
            DRMdata.create_dataset("displacement", data=Displacement, dtype=np.double)
            DRMdata.create_dataset("acceleration", data=Acceleration, dtype=np.double)
            DRMdata.create_dataset("velocity",     data=Velocity,     dtype=np.double)
            DRMdata.create_dataset("data_location",data=data_location)

            DRMmetadata.create_dataset("drmbox_xmin", data=xmin)
            DRMmetadata.create_dataset("drmbox_xmax", data=xmax)
            DRMmetadata.create_dataset("drmbox_ymin", data=ymin)
            DRMmetadata.create_dataset("drmbox_ymax", data=ymax)
            DRMmetadata.create_dataset("drmbox_zmin", data=zmin)
            DRMmetadata.create_dataset("drmbox_zmax", data=zmax)
            DRMmetadata.create_dataset("dt", data=dt)
            DRMmetadata.create_dataset("tend", data=tend)
            DRMmetadata.create_dataset("tstart", data=tsart)
            DRMmetadata.create_dataset("program_used", data=program_used)
            DRMmetadata.create_dataset("drmbox_x0", data=np.array([0, 0, 0]), dtype=np.double)
            DRMmetadata.create_dataset("h", data=spacing)
            DRMmetadata.create_dataset("name", data=name)

            DRMfile.close()

            self.output_display.append(f"DRM Load created successfully\n")
            self.progress_bar.setValue(100)

    def DRM_rectangular(self):
        """Creates and returns a QWidget for defining a rectangular DRM boundary.

        This widget includes input fields for the minimum and maximum X, Y, and Z
        coordinates, as well as the grid spacing in each direction.

        Returns:
            QWidget: A widget containing QLineEdits for rectangular DRM definition.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> creator = SvWaveCreator()
            >>> rect_widget = creator.DRM_rectangular()
            >>> # You can then inspect the widgets within rect_widget
            >>> # e.g., print(rect_widget.layout().itemAtPosition(0, 1).widget().text())
        """
        self.rectangularDRM = QWidget()
        layout = QGridLayout()
        self.rectangularDRM.setLayout(layout)
        # return rectangular widget
        xmin = QLineEdit()
        xmin.setValidator(self.doublevalidator)
        xmin.setText("-200")
        layout.addWidget(QLabel("DRM X min (m)"), 0, 0)
        layout.addWidget(xmin, 0, 1)

        xmax = QLineEdit()
        xmax.setValidator(self.doublevalidator)
        xmax.setText("200")
        layout.addWidget(QLabel("DRM X max (m)"), 0, 2)
        layout.addWidget(xmax, 0, 3)

        ymin = QLineEdit()
        ymin.setValidator(self.doublevalidator)
        ymin.setText("-200")
        layout.addWidget(QLabel("DRM Y min (m)"), 1, 0)
        layout.addWidget(ymin, 1, 1)

        ymax = QLineEdit()
        ymax.setValidator(self.doublevalidator)
        ymax.setText("200")
        layout.addWidget(QLabel("DRM Y max (m)"), 1, 2)
        layout.addWidget(ymax, 1, 3)

        zmin = QLineEdit()
        zmin.setValidator(self.doublevalidator)
        zmin.setText("-200")
        layout.addWidget(QLabel("DRM Z min (m)"), 2, 0)
        layout.addWidget(zmin, 2, 1)

        zmax = QLineEdit()
        zmax.setValidator(self.doublevalidator)
        zmax.setText("0")
        layout.addWidget(QLabel("DRM Z max (m)"), 2, 2)
        layout.addWidget(zmax, 2, 3)

        dxx = QLineEdit()
        dxx.setValidator(self.doublevalidator)
        dxx.setText("5.0")
        layout.addWidget(QLabel("DRM delta X (m)"), 0, 4)
        layout.addWidget(dxx, 0, 5)

        dyy = QLineEdit()
        dyy.setValidator(self.doublevalidator)
        dyy.setText("5.0")
        layout.addWidget(QLabel("DRM delta Y (m)"), 1, 4)
        layout.addWidget(dyy, 1, 5)

        dzz = QLineEdit()
        dzz.setValidator(self.doublevalidator)
        dzz.setText("5.0")
        layout.addWidget(QLabel("DRM delta Z (m)"), 2, 4)
        layout.addWidget(dzz, 2, 5)

        return self.rectangularDRM
    

    def DRM_spherical(self):
        """Creates and returns a placeholder QWidget for defining a spherical DRM boundary.

        This functionality is currently not implemented.

        Returns:
            QWidget: An empty widget.
        """
        # to be implemented
        return QWidget()
    
    def DRM_cylindrical(self):
        """Creates and returns a placeholder QWidget for defining a cylindrical DRM boundary.

        This functionality is currently not implemented.

        Returns:
            QWidget: An empty widget.
        """
        # to be implemented
        return QWidget()
    
    def DRM_custom(self):
        """Creates and returns a placeholder QWidget for defining a custom DRM boundary.

        This functionality is currently not implemented.

        Returns:
            QWidget: An empty widget.
        """
        # to be implemented
        return QWidget()
    

    def matertial_properties(self):
        """Calculates and updates dependent material properties (G, E, Vp, critical_Angle).

        This method is triggered when `Vs`, `rho`, or `nu` input fields change.
        It reads the current values, performs the necessary calculations, and
        updates the corresponding read-only display fields. Displays a critical
        message if `Vs`, `rho`, or `nu` are non-positive values, but continues
        execution.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> creator = SvWaveCreator()
            >>> creator.Vs.setText("300.0")
            >>> creator.rho.setText("2500.0")
            >>> creator.nu.setText("0.3")
            >>> creator.matertial_properties()
            >>> # Access updated values, e.g., print(creator.G.text())
        """

        # check if the Vs, rho, nu are not empty
        if self.Vs.text() == "" or self.rho.text() == "" or self.nu.text() == "":
            return

        # check if the Vs, rho, nu are valid
        if self.Vs.hasAcceptableInput() and self.rho.hasAcceptableInput() and self.nu.hasAcceptableInput():
            pass
        else:
            return
        
        

        # change the G E Vp based on the Vs, rho, nu
        Vs = float(self.Vs.text())
        rho = float(self.rho.text())
        nu = float(self.nu.text())

        if Vs <= 0 or rho <= 0 or nu <= 0:
            QMessageBox.critical(self, "Error", "Vs, rho, nu should be positive")
            # Logic change: The original code continued here, potentially leading to errors.
            # Adhering to "Do NOT change logic", no return is added.
        G = Vs**2 * rho
        E = 2*G*(1+nu)
        Vp = (E/rho*(1-nu))**0.5
        
        G = G/1e6
        E = E/1e6

        critical_Angle = np.arcsin(np.sqrt((1-2*nu)/(2-2*nu)))
        self.critical_Angle.setText(str(np.degrees(critical_Angle)))
        self.G.setText(str(G))
        self.E.setText(str(E))
        self.Vp.setText(str(Vp))