"""
Compute 1‑D shear‑wave transfer functions for a layered soil column
using the classic Kramer (1996) frequency‑domain transfer‑matrix method.

This module implements the transfer matrix method for computing 1D seismic site response
in layered soil profiles. It calculates both the transfer function between the top and
base of the soil column (TF_uu) and the transfer function between the top and incident
wave (TF_inc).

* Inputs  :
    soil_profile = [ {h, vs, rho, damping}, … ]   # top ↧ bottom
    rock         = {vs, rho, damping}             # elastic half‑space
    f_max   (Hz) – highest frequency of interest   (default 20 Hz)
    n_freqs       – number of frequency points     (default 2000)
* Outputs :
    f        – 1‑D array of frequencies (Hz)
    TF_uu    – complex transfer function  u_top / u_base
    TF_inc   – complex transfer function  u_top / u_incident

Example:
    >>> soil_profile = [
    ...     {"h": 2.0, "vs": 200.0, "rho": 1500.0, "damping": 0.05},
    ...     {"h": 54.0, "vs": 400.0, "rho": 1500.0, "damping": 0.05}
    ... ]
    >>> rock = {"vs": 850.0, "rho": 1500.0, "damping": 0.05}
    >>> tf = TransferFunction(soil_profile, rock, f_max=25.0)
    >>> f, TF_uu, TF_inc = tf.compute()
"""
import numpy as np
from numpy.fft import fft, ifft, fftfreq
import matplotlib.pyplot as plt
from typing import List, Dict, Union, Optional, Tuple, Any
from pyvista import UnstructuredGrid, Cube
import os
import re
from tqdm import tqdm
import h5py
from pykdtree.kdtree import KDTree

class TimeHistory:
    """
    Class to store and process acceleration time history data.
    This class supports loading time history data from various formats. The class give access to
    the time history data, computes velocity and displacement from acceleration, and provides
    methods to compute response spectra and transfer functions.

    Attributes:
        time (np.ndarray): Time array in seconds
        acceleration (np.ndarray): Acceleration array
        gravity (float): Gravitational acceleration in m/s² (default: 9.81)
        unit_in_g (bool): If True, acceleration is in g (default: True)
        metadata (Optional[Dict[str, Any]]): Metadata about the time history
        dt (Optional[float]): Time step if time is uniform, otherwise None
    Raises:
        ValueError: If time and acceleration arrays are not of the same length
        ValueError: If time array is not strictly increasing
        ValueError: If time or acceleration arrays are empty
    Returns:
        TimeHistory: An instance of the TimeHistory class containing the time and acceleration data.

    Examples:
        >>> from femora.tools.transferFunction import TimeHistory
        >>> import numpy as np

        # Create a TimeHistory instance with time and acceleration data
        >>> time = np.array([0.0, 0.1, 0.2, 0.3])
        >>> acceleration = np.array([0.0, 1.0, 0.5, -0.5])
        >>> th = TimeHistory(time, acceleration)
        >>> print(th.duration)  # Output: 0.3

        # create a TimeHistory from a file
        >>> th = TimeHistory.load(file_path='path/to/time_history.csv', format='csv')
        >>> th = TimeHistory.load(file_path='path/to/time_history.peer', format='peer')
        >>> th = TimeHistory.load(time_file='path/to/time_values.txt', acc_file='path/to/acceleration_values.txt', delimiter=',')
    """

    def __init__(self, time: np.ndarray, 
                       acceleration: np.ndarray, 
                       unit_in_g: bool = True,
                       gravity: float = 9.81,
                       metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize time history data.

        Args:
            time (np.ndarray): Time array in seconds
            acceleration (np.ndarray): Acceleration array
            unit_in_g (bool): If True, acceleration is in g (default: True)
            gravity (float): Gravitational acceleration in if unit is in g (default: 9.81 m/s²)
            metadata (Optional[Dict]): Dictionary containing metadata about the time history
        
        Raises:
            ValueError: If time and acceleration arrays are not of the same length
            ValueError: If time array is not strictly increasing
        
        Returns:
            None
        """
        # check if the time is increasing
        if not np.all(np.diff(time) >= 0):
            raise ValueError("Time array must be strictly increasing")
        if len(time) == 0 or len(acceleration) == 0:
            raise ValueError("Time and acceleration arrays must not be empty")
        if len(time) != len(acceleration):
            raise ValueError("Time and acceleration arrays must have the same length")
        
        self.time = np.array(time)
        self.acceleration = np.array(acceleration)
        self.gravity = gravity
        self.unit_in_g = unit_in_g
        self.metadata = metadata or {}
        if len(time) != len(acceleration):
            raise ValueError("Time and acceleration arrays must have the same length")
        # dt is optional, only if time is uniform
        diffs = np.diff(time)
        if len(diffs) < 1:
            raise ValueError("Time array must have at least two points") 
        if np.allclose(diffs, diffs[0]):
            self.dt = diffs[0]
        else:
            self.dt = np.min(diffs)
            self.time = np.arange(time[0], time[-1]+1.0e-6, self.dt) 
            self.acceleration = np.interp(self.time, time, acceleration)
        

    @staticmethod
    def load(file_path: str = None, 
             format: str = 'auto', 
             time_file: str = None, 
             dt: float = None,
             acc_file: str = None, 
             delimiter: str = ',', 
             unit_in_g: bool = True,
             gravity: float = 9.81,
             skiprows: int = 0) -> 'TimeHistory':
        """
        Load a time history from a single file (auto, peer, csv) or from two files (time and acceleration).
        Args:
            file_path (str): Path to the time history file (peer/csv)
            format (str): Format of the file ('peer', 'csv', 'auto').
            time_file (str): Path to file containing time values (for two-file mode)
            acc_file (str): Path to file containing acceleration values (for two-file mode)
            delimiter (str): Delimiter for text files (default ',')
            skiprows (int): Number of rows to skip (default 0)
        Returns:
            TimeHistory: Loaded time history object
        """
        if time_file is None and dt is None :
            raise ValueError("Either time_file or dt must be provided.")
        
        if dt is not None and time_file is not None:
            raise ValueError("Cannot provide both dt and time_file. Choose one.")
        
        if dt and acc_file:
            acc = np.loadtxt(acc_file, delimiter=delimiter, skiprows=skiprows)
            time = np.arange(0, len(acc) * dt, dt)
            return TimeHistory(time, 
                               acc, 
                               unit_in_g=unit_in_g, 
                               gravity=gravity,
                               metadata={'source': 'values', 'dt': dt, 'acc_file': acc_file})

        if time_file and acc_file:
            time = np.loadtxt(time_file, delimiter=delimiter, skiprows=skiprows)
            acc = np.loadtxt(acc_file, delimiter=delimiter, skiprows=skiprows)
            return TimeHistory(time, 
                               acc, 
                               unit_in_g=unit_in_g,
                               gravity=gravity,
                               metadata={'source': 'separate_files', 'time_file': time_file, 'acc_file': acc_file})
        if file_path is None:
            raise ValueError("file_path must be provided if not loading from two files.")
        if format == 'auto':
            format = TimeHistory._detect_format(file_path)
        if format == 'peer':
            return TimeHistory._load_peer_format(file_path)
        elif format == 'csv':
            return TimeHistory._load_csv_format(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def _detect_format(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return 'csv'
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if 'NPTS' in line and 'DT' in line:
                        return 'peer'
        except Exception:
            pass
        raise ValueError("Could not detect file format")

    @staticmethod
    def _load_peer_format(file_path: str) -> 'TimeHistory':
        import re
        from datetime import datetime
        with open(file_path, 'r') as f:
            lines = f.readlines()
        npts, dt = None, None
        data_start = 0
        for i, line in enumerate(lines):
            if 'NPTS' in line and 'DT' in line:
                match = re.search(r'NPTS\s*=\s*(\d+),\s*DT\s*=\s*([0-9.Ee+-]+)', line)
                if match:
                    npts = int(match.group(1))
                    dt = float(match.group(2))
                    data_start = i + 1
                    break
        if npts is None or dt is None:
            raise ValueError("Could not find NPTS and DT in PEER file header.")
        acc = []
        for line in lines[data_start:]:
            acc.extend([float(x) for x in line.strip().split() if x])
        acc = np.array(acc)
        if len(acc) != npts:
            raise ValueError(f"Expected {npts} points, found {len(acc)}.")
        time = np.arange(0, npts * dt, dt)
        if len(time) > len(acc):
            time = time[:len(acc)]
        elif len(acc) > len(time):
            acc = acc[:len(time)]
        metadata = {
            'format': 'peer',
            'npts': int(npts),
            'dt': dt,
            'filename': os.path.basename(file_path),
            'loaded_at': datetime.now().isoformat()
        }
        return TimeHistory(time, acc, metadata)

    @staticmethod
    def _load_csv_format(file_path: str) -> 'TimeHistory':
        from datetime import datetime
        data = np.loadtxt(file_path, delimiter=',', skiprows=1)
        time = data[:, 0]
        acc = data[:, 1]
        dt = time[1] - time[0] if len(time) > 1 else None
        metadata = {
            'format': 'csv',
            'npts': len(time),
            'dt': dt,
            'filename': os.path.basename(file_path),
            'loaded_at': datetime.now().isoformat()
        }
        return TimeHistory(time, acc, metadata)

    @property
    def duration(self) -> float:
        """Get the duration of the time history in seconds."""
        return self.time[-1] - self.time[0]

    @property
    def velocity(self) -> np.ndarray:
        """Compute the velocity from the acceleration time history."""
        if self.unit_in_g:
            return np.cumsum(self.acceleration * self.gravity) * self.dt
        else:
            return np.cumsum(self.acceleration) * self.dt
        
    @property
    def displacement(self) -> np.ndarray:
        """Compute the displacement from the acceleration time history."""
        return np.cumsum(self.velocity) * self.dt
    
    
    @property
    def npts(self) -> int:
        """Get the number of points in the time history."""
        return len(self.time)

    def get_spectrum(self, periods: Optional[np.ndarray] = None,
                    damping: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the response spectrum for the time history.

        Args:
            periods (Optional[np.ndarray]): Array of periods to compute spectrum at
            damping (float): Damping ratio (default: 0.05)

        Returns:
            Tuple[np.ndarray, np.ndarray]: Periods and spectral accelerations
        """
        if periods is None:
            # Default periods: 0.01 to 10 seconds, 100 points
            periods = np.logspace(-2, 1, 100)

        # Compute Fourier transform
        n = len(self.acceleration)
        freq = np.fft.rfftfreq(n, self.dt)
        acc_fft = np.fft.rfft(self.acceleration)

        # Compute response spectrum
        sa = np.zeros_like(periods)
        for i, T in enumerate(periods):
            omega = 2 * np.pi / T
            h = damping
            beta = np.sqrt(1 - h**2)
            
            # Transfer function for SDOF system
            H = 1 / (1 - (freq/omega)**2 + 2j*h*(freq/omega))
            
            # Compute response
            resp_fft = H * acc_fft
            resp = np.fft.irfft(resp_fft, n)
            
            # Get maximum absolute response
            sa[i] = np.max(np.abs(resp))

        return periods, sa
    

    def plot(self) -> None:
        """Plot the acceleration time history."""
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 4))
        plt.plot(self.time, self.acceleration, label='Acceleration')
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (g)' if self.unit_in_g else 'Acceleration (m/s²)')
        plt.title('Acceleration Time History')
        plt.grid()
        plt.legend()
        plt.show()



class TransferFunction:
    _instance = None
    _initialized = False

    def __new__(cls, soil_profile: List[Dict] = None, rock: Dict = None, f_max: float = 20.0, n_freqs: int = 2000):
        """
        Create or return the singleton instance of TransferFunction.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        #  update the soil profile and rock properties
        cls._instance.update_soil_profile(soil_profile)
        cls._instance.update_rock(rock)
        cls._instance.computed = False
        cls._instance.f_max = f_max
        return cls._instance

    def __init__(self, soil_profile: List[Dict] = None, rock: Dict = None, f_max: float = 20.0, n_freqs: int = 2000):
        """
        Initialize the transfer function calculator.

        This constructor sets up the transfer function calculator with the given soil profile
        and rock properties. The transfer function is computed immediately upon initialization.
        Since this is a singleton, subsequent initializations with different parameters will
        update the existing instance.

        Args:
            soil_profile (List[Dict]): List of dictionaries containing soil layer properties.
                Each dictionary must contain:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio (default: 0.0)
            rock (Dict): Dictionary containing rock properties:
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio (default: 0.0)
            f_max (float, optional): Highest frequency of interest in Hz. Defaults to 20.0.
            n_freqs (int, optional): Number of frequency points. Defaults to 2000.

        Raises:
            ValueError: If required properties are missing in soil_profile or rock
            TypeError: If input types are incorrect

        Example:
            >>> soil_profile = [
            ...     {"h": 2.0, "vs": 200.0, "rho": 1500.0, "damping": 0.05},
            ...     {"h": 54.0, "vs": 400.0, "rho": 1500.0, "damping": 0.05}
            ... ]
            >>> rock = {"vs": 850.0, "rho": 1500.0, "damping": 0.05}
            >>> tf = TransferFunction(soil_profile, rock, f_max=25.0)
        """
        # Only initialize once or if parameters are provided
        if soil_profile is not None and rock is not None:
            self.soil_profile = soil_profile
            self.rock = rock
            self.f_max = f_max
            self.n_freqs = n_freqs
            
            # Initialize results
            self.f = None
            self.TF_uu = None
            self.TF_inc = None
            
            self.computed = False


    @staticmethod 
    def _get_DRM_points(mesh: UnstructuredGrid,
                        props: Dict[str, Any]) -> np.ndarray:
        """
        Extract DRM points from a mesh.
        Args:
            mesh (UnstructuredGrid): The mesh from which to extract points.
            Props (Dict[str, Any]): Dictionary containing properties of the mesh.
                - 'shape': Shape of the mesh (e.g., 'box', 'cylinder')

        Returns:
            np.ndarray: Array of DRM points.
        """
        # Extract DRM points from the mesh
        if props['shape'] == 'box':
            # Extract points from a box mesh
            bounds = mesh.bounds
            eps = 1e-6
            bounds = tuple(np.array(bounds) + np.array([eps, -eps, eps, -eps, eps, 10]))
            normal = [0, 0, 1]
            origin = [0, 0, bounds[5]-eps]

            cube = Cube(bounds=bounds)
            cube = cube.clip(normal=normal, origin=origin)
            clipped = mesh.copy().clip_surface(cube, invert=False, crinkle=True)
            cellCenters = clipped.cell_centers(vertex=True)

            Coords = clipped.points
            xmin, xmax, ymin, ymax, zmin, zmax = cellCenters.bounds
            # print(f"Bounds: {xmin}, {xmax}, {ymin}, {ymax}, {zmin}, {zmax}")
            # print(clipped.bounds)
            # filter out points inside the bounds with a small tolerance

            internal =  (Coords[:, 0] > xmin) & (Coords[:, 0] < xmax) & \
                    (Coords[:, 1] > ymin) & (Coords[:, 1] < ymax) & \
                    (Coords[:, 2] > zmin) 
            
            # clipped.point_data['inside'] = inside
            # clipped.plot(show_edges=True, scalars='inside', cmap='coolwarm')



            # Correct vlalues
            bin_size = 1e-3
            Coords = np.round(Coords / bin_size) * bin_size
        else:
            raise ValueError("other shape not supported not implemented yet. Please use box shape for now. props['shape'] = 'box')")


        # organize the coordinates by z
        return Coords, internal
    

    def _get_DRM_soil_profile(self, coords: np.ndarray):
        """
        Refine the soil profile based on the coordinates of the mesh.

        Args:
            coords (np.ndarray): Array of coordinates from the mesh.

        Returns:
            List[Dict]: Refined soil profile.
        """
        # Refine the soil profile based on the coordinates

        coords = coords[np.argsort(-coords[:, 2])]
        
        # Create a new soil profile based on the coordinates
        unique_z, indices = np.unique(coords[:, 2], return_inverse=True)
        unique_z = unique_z[::-1]  # Reverse order to match zmax to zmin
        indices = indices[::-1]  # Reverse order to match zmax to zmin
        # print(f"Unique z values: {unique_z}")
        # print(f"Indices: {indices}")
        # print(f"z values: {coords[:, 2]}")
        # print(f"z values: {unique_z[indices]}")


        # from the uniq z calcute h
        h = -np.diff(unique_z)  # negative because z is descending
        depth = np.cumsum(h)
        # add zero at the beginning of depth
        maxdepth = depth[-1]


        if np.abs(maxdepth - self.get_total_depth()) > 1e-2:
            raise ValueError(f"the length of the soil profile is not equal to the length of the mesh")
        

        # Create a depth array from soil profile
        ProfileDepth = []
        for i in range(len(self.soil_profile)):
            ProfileDepth.append(self.soil_profile[i]['h'])
        ProfileDepth = np.cumsum(ProfileDepth)
        
        # combine profiel depth with the depth
        ProfileDepth = np.array(ProfileDepth)
        combinedepth = np.concatenate((ProfileDepth, depth))
        combinedepth = np.unique(combinedepth)
        # now create the new soil profile
        new_soil_profile = []
        i = 0
        j = 0
        elev = 0
        for j,zz in enumerate(ProfileDepth):
            while zz > combinedepth[i]-1e-2:
                # print(f"zz: {zz}, depth[index]: {combinedepth[i]}, h:{combinedepth[i] - elev}")
                new_layer = self.soil_profile[j].copy()
                new_layer['h'] = float(combinedepth[i] - elev)
                new_soil_profile.append(new_layer)
                elev = combinedepth[i]
                i += 1
                if i >= len(combinedepth):
                    break
            

        return new_soil_profile
    

    
    def createDRM(self, 
                  mesh: UnstructuredGrid, 
                  props: Dict[str, Any], 
                  time_history: TimeHistory,
                  filename: str = "drmload.h5drm",
                  pad_factor: float = 0.05,
                  progress_bar: Optional[tqdm] = None) -> None:
        """
        Generates a Dynamic Response Modification (DRM) load file for use in OpenSees simulations.
        This method computes the DRM loads by applying a transfer function to the input acceleration time history,
        processes the resulting acceleration, velocity, and displacement histories, and writes the results to an HDF5 file.
        Parameters

        mesh : UnstructuredGrid
            The finite element mesh representing the domain for which the DRM loads are to be computed.
        props : Dict[str, Any]
            Dictionary containing the shape and other properties of the mesh.
        time_history : TimeHistory
            Object containing the acceleration time history and related metadata (e.g., time step, units).
        filename : str, optional
            Name of the output HDF5 file to store the DRM loads (default is "drmload.h5drm").
        pad_factor : float, optional
            Fraction of the time history length to use for zero-padding at the beginning and end (default is 0.05).
        progress_bar : Optional[tqdm], optional
            Progress bar object for tracking computation progress. If None, a new tqdm progress bar is created.
        Returns
        -------
        None
        Raises
        ------
        Notes
        -----
        - The method applies zero-padding to the acceleration time history to minimize edge effects in the frequency domain.
        - The transfer function is computed for all soil layers and applied in the frequency domain.
        - Baseline correction and trend removal are performed on the displacement history.
        - The resulting acceleration, velocity, and displacement histories are written to an HDF5 file compatible with OpenSees DRM input.
        """


        if progress_bar is None:
            progress_bar = tqdm(total=100, desc="Computing DRM", unit="%", leave=False)
        progress_bar.update(0)
        coords, internal = self._get_DRM_points(mesh, props)
        progress_bar.update(5)
        newProfile = self._get_DRM_soil_profile(coords)
        progress_bar.update(5)

        # compute the transfer function for the 
        # f, bh, ind = self.compute(soil_profile=newProfile, allLayers=True)
        h = np.array([l['h'] for l in newProfile], dtype=float)

        dt = time_history.dt
        n_pad = int(time_history.npts * pad_factor)
        acc = time_history.acceleration
        delta_T = n_pad * dt

        if n_pad > 0:
            acc = np.pad(acc, (n_pad, n_pad), mode='constant')
        
        time = np.arange(0, len(acc) * dt, dt)
        n = len(acc)
        freq = np.fft.rfftfreq(len(acc), d=dt)
        acc_fft = np.fft.rfft(acc)
        

        f, H = self.compute_all_layers(soil_profile=newProfile,
                                        frequency=freq,
                                        )
        
        if len(H) != len(freq):
            raise ValueError("Transfer function length does not match frequency length")
        
        acc_fft = H * acc_fft.reshape(-1,1)  # complex multiplication

        acc = np.fft.irfft(acc_fft, axis=0)


        if len(acc) != len(time):
            # make them equal length
            min_length = min(len(acc), len(time))
            acc = acc[:min_length,:]
            time = time[:min_length]
        
        mask = time >= delta_T
        acc = acc[mask,:]
        time = time[mask]
        time = time - time[0]  # start time at 0
        time = time + time_history.time[0]  # align with original time history


        if time_history.unit_in_g:
            g = time_history.gravity
            vel = np.cumsum(acc, axis=0) * dt * g
            disp = np.cumsum(vel, axis=0) * dt

        else:
            vel = np.cumsum(acc, axis=0) * dt
            disp = np.cumsum(vel, axis=0) * dt


        # baseline correction for displacement
        base =disp[:,-1]
        disp = disp - base.reshape(-1,1)
        X = np.vstack([time, np.ones_like(time)]).T   # Shape: 
        coeffs, _, _, _ = np.linalg.lstsq(X, disp, rcond=None)
        trend = X @ coeffs  # Shape: (n_time, n_signals)
        disp = disp - trend

        tmax = np.max(time_history.time)
        # print(f"tmax: {tmax}")
        mask = time > tmax
        ind = np.argmax(mask)
        base_end  = base[ind]
        # print(f"base_end: {base_end}")
        base[mask] = base_end

        disp = disp + base.reshape(-1,1)  # add the base to the displacement


        depth = -np.cumsum(np.append([0],h)) # negative because z is descending

        # return f, H, acc, h, time,vel, disp,coords,internal
        # now creating the drm load file for opensees
        self._write_h5drm(acc, h, time, vel, disp, coords, internal, filename=filename)
    



    # def _write_h5drm(self, f, bh, acc, h, time, vel, disp, coords, internal):
    def _write_h5drm(self, acc, h, time, vel, disp, coords, internal , filename: str = "drmload.h5drm"):
        """
            Writes DRM (Domain Reduction Method) data to an H5DRM file in HDF5 format.
            This method organizes and stores acceleration, velocity, displacement, and coordinate data,
            along with relevant metadata, into a structured HDF5 file for use in DRM-based simulations.
                acc (np.ndarray): Acceleration data array of shape (n_layers, n_timesteps).
                h (np.ndarray): Layer thicknesses or heights, used to compute cumulative depth.
                time (np.ndarray): 1D array of time steps.
                vel (np.ndarray): Velocity data array of shape (n_layers, n_timesteps).
                disp (np.ndarray): Displacement data array of shape (n_layers, n_timesteps).
                coords (np.ndarray): Array of node coordinates, shape (n_nodes, 3).
                internal (np.ndarray): Boolean array indicating internal nodes, shape (n_nodes,).
            Raises:
                ValueError: If any coordinate's depth does not match a DRM depth within a tolerance.
            Notes:
                - The output file is overwritten if it exists.
                - Data is organized into two main groups: "DRM_Data" (containing the main arrays)
                  and "DRM_Metadata" (containing simulation and box metadata).
                - Only the x-component of input data is used; y and z components are set to zero.
                - The function assumes that the input arrays are properly shaped and consistent.
        Write the DRM data to an H5DRM file.
        
        Args:
            ...: Parameters for writing the DRM data.
        
        Returns:
            None
        """
        # Implement the logic to write the DRM data to an H5DRM file
        depth = -np.cumsum(np.append([0],h))  # Cumulative depth from the base

        accx = acc.T
        accy = np.zeros_like(accx)
        accz = np.zeros_like(accx)
        acc  = np.stack([accx, accy, accz], axis=1)
        acc  = acc.reshape(-1, accx.shape[1])

        velx = vel.T
        vely = np.zeros_like(velx)
        velz = np.zeros_like(velx)
        vel  = np.stack([velx, vely, velz], axis=1)
        vel  = vel.reshape(-1, velx.shape[1])

        disp_x = disp.T
        disp_y = np.zeros_like(disp_x)
        disp_z = np.zeros_like(disp_x)
        disp  = np.stack([disp_x, disp_y, disp_z], axis=1)
        disp  = disp.reshape(-1, disp_x.shape[1])

        dt = time[1] - time[0]

        # find which index of the depth is each coordinate row
        kdtree = KDTree(depth.reshape(-1, 1))
        # Find the index of the closest depth for each coordinate
        dist, data_location = kdtree.query(coords[:, 2].reshape(-1, 1), k=1)

        if np.any(dist > 1e-5):
            raise ValueError(f"Some coordinates are not close to any depth in the DRM . Distances: {dist[dist > 1e-5]}")

        data_location = data_location*3

        zmin = np.min(coords[:, 2])
        zmax = np.max(coords[:, 2])
        xmin = np.min(coords[:, 0])
        xmax = np.max(coords[:, 0])
        ymin = np.min(coords[:, 1])
        ymax = np.max(coords[:, 1])

        dh = np.array([0,0,0])
        drmbox_x0 = np.array([0,0,0])


        file_name = "drmload.h5drm"
        with h5py.File(file_name, "w") as f:
            # DRM_Data group
            drm_data = f.create_group("DRM_Data")
            # Create a dataset for coordinates
            # Path	/DRM_Data/xyz
            # Name	xyz
            # Type	Float, 64-bit, little-endian
            # Shape	? x 3 = 25854
            drm_data.create_dataset("xyz", data=coords, dtype='f8', shape=coords.shape)
            # /DRM_Data/internal
            # Name	internal
            # Type	Boolean
            # Shape	
            # Raw	
            # Inspect
            drm_data.create_dataset("internal", data=internal, dtype='b', shape=internal.shape)
            # Path	/DRM_Data/acceleration
            # Name	acceleration
            # Type	Float, 64-bit, little-endian
            # Shape	acc.shape[0] x acc.shape[1] = ?
            # Chunk shape	3 x acc.shape[1] = ?
            drm_data.create_dataset("acceleration", data=acc, dtype='f8', shape=acc.shape, chunks=(3, acc.shape[1]))
            # Path	/DRM_Data/velocity
            # Name	velocity
            # Type	Float, 64-bit, little-endian
            # Shape	vel.shape[0] x vel.shape[1] = ?
            # Chunk shape	3 x vel.shape[1] = ?
            drm_data.create_dataset("velocity", data=vel, dtype='f8', shape=vel.shape, chunks=(3, vel.shape[1]))
            # Path	/DRM_Data/displacement
            # Name	displacement
            # Type	Float, 64-bit, little-endian
            # Shape	disp.shape[0] x disp.shape[1] = ?
            # Chunk shape	3 x disp.shape[1] = ?
            drm_data.create_dataset("displacement", data=disp, dtype='f8', shape=disp.shape, chunks=(3, disp.shape[1]))
            # /DRM_Data/data_location
            # Name	data_location
            # Type	Integer (signed), 32-bit, little-endian
            # Shape	
            # Raw	
            # Inspect
            drm_data.create_dataset("data_location", data=data_location, dtype='i4', shape=data_location.shape)

            # /DRM_Metadata group
            drm_metadata = f.create_group("DRM_Metadata")
            # /DRM_Metadata/dt
            # Name	dt
            # Type	Float, 64-bit, little-endian
            # Shape	Scalar
            drm_metadata.create_dataset("dt", data=dt)
            # /DRM_Metadata/tend
            # Name	tend
            # Type	Float, 64-bit, little-endian
            # Shape	Scalar
            drm_metadata.create_dataset("tend", data=time[-1])

            # /DRM_Metadata/tstart
            # Name	tstart
            # Type	Float, 64-bit, little-endian
            # Shape	Scalar
            drm_metadata.create_dataset("tstart", data=time[0]  )
            # /DRM_Metadata/drmbox_zmin
            drm_metadata.create_dataset("drmbox_zmin", data=zmin  )
            # /DRM_Metadata/drmbox_zmax
            drm_metadata.create_dataset("drmbox_zmax", data=zmax  )
            # /DRM_Metadata/drmbox_xmin
            drm_metadata.create_dataset("drmbox_xmin", data=xmin  )
            # /DRM_Metadata/drmbox_xmax
            drm_metadata.create_dataset("drmbox_xmax", data=xmax  )
            # /DRM_Metadata/drmbox_ymin
            drm_metadata.create_dataset("drmbox_ymin", data=ymin  )
            # /DRM_Metadata/drmbox_ymax
            drm_metadata.create_dataset("drmbox_ymax", data=ymax  )

            # /DRM_Metadata/h
            # Name	h
            # Type	Float, 64-bit, little-endian
            # Shape	3
            # Raw	
            # Inspect
            drm_metadata.create_dataset("h", data=dh, dtype='f8', shape=(3,))

            # /DRM_Metadata/drmbox_x0
            # Name	drmbox_x0
            # Type	Float, 64-bit, little-endian
            # Shape	3
            # Raw	
            drm_metadata.create_dataset("drmbox_x0", data=drmbox_x0, dtype='f8', shape=(3,))

            





    def compute_surface_motion(self, 
                               time_history: TimeHistory,
                               freqFlag: bool = False,
                               acc_fftFlag: bool = False,
                               surface_fftFlag: bool = False,
                               pad_factor: float = 0.1
                               ) -> Dict[str, np.ndarray]:
        """
        Compute surface motion using the transfer function.

        Args:
            time_history (TimeHistory): Input time history.
            freqFlag (bool): If True, include frequency array in result.
            acc_fftFlag (bool): If True, include input FFT in result.
            surface_fftFlag (bool): If True, include output FFT in result.
            pad_factor (float): Zero-padding factor (0 to 1, default 0.02).

        Returns:
            Dict[str, np.ndarray]: Dictionary with results.
        """
        if time_history is None:
            raise ValueError("No time history available")
        if not (0 <= pad_factor < 1):
            raise ValueError("pad_factor must be between 0 (inclusive) and 1 (exclusive)")

        dt = time_history.dt
        n_pad = int(time_history.npts * pad_factor)
        acc = time_history.acceleration
        delta_T = n_pad * dt

        if n_pad > 0:
            acc = np.pad(acc, (n_pad, n_pad), mode='constant')
        
        
        time = np.arange(0, len(acc) * dt, dt)
        n = len(acc)
        freq = np.fft.rfftfreq(len(acc), d=dt)
        acc_fft = np.fft.rfft(acc)
        f, TF_uu, _ = self.compute(frequency=freq)

        if len(TF_uu) != len(freq):
            raise ValueError("Transfer function length does not match frequency length")
        # Apply transfer function in frequency domain
        surface_fft = TF_uu * acc_fft  # complex multiplication

        # Inverse FFT to get surface motion
        surface_acc = np.fft.irfft(surface_fft)

        if len(surface_acc) != len(acc):
            # make them equal length
            min_length = min(len(surface_acc), len(acc))
            surface_acc = surface_acc[:min_length]
            acc = acc[:min_length]
            time = time[:min_length]

        # print(len(surface_acc), len(time))
        mask = time >= delta_T
        surface_acc = surface_acc[mask]
        # surface_acc = surface_acc[:time_history.npts]  # match original time history length
        time = time[mask]
        time = time - time[0]  # start time at 0
        time = time + time_history.time[0]  # align with original time history

        result = {"surface_acc": (time,surface_acc)}
        if freqFlag:
            result["freq"] = freq
        if acc_fftFlag:
            result["acc_fft"] = acc_fft
        if surface_fftFlag:
            result["surface_fft"] = surface_fft

        return result
    

    def _convolve(self,
                 time_history: TimeHistory,
                 soil_profile: List[Dict] = None,
                 return_all:bool = False
                 ) -> TimeHistory:
        """
        Convolve the time history with the transfer function to get the surface motion.

        Args:
            time_history (TimeHistory): Input time history.
            soil_profile (List[Dict], optional): Soil profile to use for convolution. If None, uses the default soil profile.
        Returns:
            TimeHistory: Convolved time history object containing the surface motion.
        """
        acc = time_history.acceleration
        dt = time_history.dt
        tol = 1e-6
        tmin1 =  time_history.time[0]
        tmax1 = time_history.time[-1]

        # pad factor should be between determine in a wat that
        # dw is going to at least 0.01
        pad_factor = int(1 / (0.1 * dt)) / len(acc)
        pad_factor = max(pad_factor, 0.1)

        padwidth = int(pad_factor * len(acc))
        if padwidth > 0:
            tmax = len(acc) * dt
            acc = np.pad(acc, (padwidth, padwidth), mode='constant')

        time = np.arange(0, len(acc) * dt, dt)
        if soil_profile is None:
            soil_profile = self.soil_profile.copy()

        freq = np.fft.rfftfreq(len(acc), d=dt)
        acc_fft = np.fft.rfft(acc)
        f, TF_uu, _ = self.compute(soil_profile=soil_profile, frequency=freq)
        if len(TF_uu) != len(freq):
            raise ValueError("Transfer function length does not match frequency length")
        # complex multiplication to apply transfer function
        surface_acc_fft = TF_uu * acc_fft  # complex multiplication
        surface_acc_fft[f > self.f_max] = 0  # zero out frequencies above f_max
        surface_acc = np.fft.irfft(surface_acc_fft)
        # find the first time point where the surface motion is non-zero
        if len(surface_acc) != len(time):
            # make them equal length
            min_length = min(len(surface_acc), len(time))
            surface_acc = surface_acc[:min_length]
            time = time[:min_length]


        # remove the zero padding from the beginning 
        if padwidth > 0:
            surface_acc = surface_acc[padwidth:]
            time = time[padwidth:]

        lastindex = -np.argmax(np.abs(surface_acc[::-1]) > tol) - 1
        tmax2 = time[lastindex]
        tmin2 = time[np.argmax(np.abs(surface_acc) > tol)]
        tmin = min(tmin1, tmin2)
        tmax = max(tmax1, tmax2)
        mask = (time >= tmin) & (time <= tmax)
        time = time[mask]
        surface_acc = surface_acc[mask]
        time = time - time[0]  # start time at 0
        # print(f"tmin: {tmin}, tmax: {tmax}, time: {time[0]} to {time[-1]}")
        record = TimeHistory(time, surface_acc)
        tfs = {"TF":TF_uu,
               "ouputFFt":surface_acc_fft,
               "inputFFT":acc_fft,
               "freq":freq}
        
        if return_all:
            return record, tfs
        else:
            return record
        



    def plot_convolved_motion(self,
                                time_history: TimeHistory,
                                soil_profile: List[Dict] = None) -> 'matplotlib.figure.Figure':
            """
            Plot the convolved motion from the incident wave to the surface motion.
            Args:
                time_history (TimeHistory): Input time history.
                soil_profile (List[Dict], optional): Soil profile to use for convolution. If None, uses the default soil profile.
            Returns:
                matplotlib.figure.Figure: The figure object containing the plot.
            """
            surface, tfs = self._convolve(time_history, soil_profile=soil_profile, return_all=True)
            time = surface.time
            surface_acc = surface.acceleration
            bedrock = time_history.acceleration
            bedtime = time_history.time
            freq = tfs['freq']
            acc_fft = tfs['inputFFT']
            surface_acc_fft = tfs['ouputFFt']
            TF = tfs['TF']
            fig, ax = plt.subplots(5, 1, figsize=(8, 11))
            blue = '#3182bd'
            box = dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')
            ax[4].plot(bedtime, bedrock, label='Incident Wave', color=blue)
            ax[4].set_title('Incident Wave', loc='right', y=0.9, bbox=box)
            ax[4].set_xlabel('Time (s)')
            ax[4].set_ylabel('Acceleration')
            ax[3].plot(freq, 
                    np.abs(acc_fft), 
                    label='Input FFT', 
                    color=blue)
            ax[3].set_xlim(0, self.f_max)
            ax[3].set_title('Input FFT', loc='right', y=0.9, bbox=box)
            ax[3].set_xlabel('Frequency (Hz)')
            ax[3].set_ylabel('|FFT|')

            ax[2].plot(freq, 
                    np.abs(TF), 
                    label='Transfer Function', 
                    color=blue)
            ax[2].set_title('Transfer Function', loc='right', y=0.9, bbox=box)
            ax[2].set_xlabel('Frequency (Hz)')
            ax[2].set_ylabel('|TF|')
            ax[2].set_xlim(0, self.f_max)
            ax[1].plot(freq,
                    np.abs(surface_acc_fft), 
                    label='Output FFT', 
                    color=blue)
            ax[1].set_xlim(0, self.f_max)
            ax[1].set_title('Output FFT', loc='right', y=0.9, bbox=box)
            ax[1].set_xlabel('Frequency (Hz)')
            ax[1].set_ylabel('|FFT|')
            ax[0].plot(time, surface_acc, label='Surface Motion', color=blue)
            ax[0].plot(bedtime, bedrock, label='Incident Wave', color='orange', linestyle='--')
            ax[0].set_title('Surface Motion', loc='right', y=0.9, bbox=box)
            ax[0].set_xlabel('Time (s)')
            ax[0].set_ylabel('Acceleration')

            for a in ax:
                a.grid(True, which='both', linestyle='--', linewidth=0.5)
            
            fig.suptitle('Convolved Motion', fontsize=16, fontweight='bold')
            fig.subplots_adjust(top=0.95)  # Adjust top to make room for the title
            fig.tight_layout()
            return fig


    def _deconvolve(self,time_history: TimeHistory,
                        soil_profile: List[Dict] = None,
                        return_all: bool = False) -> TimeHistory:
        """
        Deconvolve the time history from the surface motion to get the incident wave.
        Args:
            time_history (TimeHistory): Input time history.
        Returns:
            TimeHistory: Deconvolved time history object containing the incident wave.
        """

        acc = time_history.acceleration
        dt = time_history.dt
        tol = 1e-8
        tmin1 =  np.argmax(np.abs(acc) > tol)
        tmax1 = time_history.time[-1] 

        # pad factor should be between determine in a wat that 
        # dw is going to at least 0.01
        pad_factor = int(1 / (0.1 * dt))/ len(acc)
        pad_factor = max(pad_factor, 0.1)


        padwidth = int(pad_factor * len(acc))
        if padwidth > 0:
            tmax = len(acc) * dt
            acc = np.pad(acc, (padwidth, padwidth), mode='constant')
        
        
        time = np.arange(0, len(acc) * dt, dt)

        if soil_profile is None:
            soil_profile = self.soil_profile.copy()


        freq = np.fft.rfftfreq(len(acc), d=dt)
        acc_fft = np.fft.rfft(acc)
        f,TF,_ = self.compute(soil_profile=soil_profile, frequency=freq)

        if len(TF) != len(freq):
            raise ValueError("Transfer function length does not match frequency length")
        
          # complex division to apply inverse transfer function
        # Inverse FFT to get incident wave
        incident_acc_fft = acc_fft / TF  # complex division
        incident_acc_fft[f> self.f_max] = 0  # zero out frequencies above f_max
        incident_acc = np.fft.irfft(incident_acc_fft)


        # find the first time point where the surface motion is non-zero
        if len(incident_acc) != len(time):
            # make them equal length
            min_length = min(len(incident_acc), len(time))
            incident_acc = incident_acc[:min_length]
            time = time[:min_length]


        lastindex   = -np.argmax(np.abs(incident_acc[::-1]) > tol) -1
        
        tmax2 = time[lastindex]
        tmin2 = time[np.argmax(np.abs(incident_acc) > tol)]

        tmin = min(tmin1, tmin2)
        tmax = max(tmax1, tmax2)

        
        mask = (time >= tmin) & (time <= tmax)
        time = time[mask]
        incident_acc = incident_acc[mask]
        acc = acc[mask]
        time = time - time[0]  # start time at 0


        
        incident = TimeHistory(time,incident_acc)
        surface  = TimeHistory(time, acc)
        if return_all:
            tfs = { "TF": TF,
                    "outputFFT": incident_acc_fft,
                    "inputFFT": acc_fft,
                    "freq": freq}
            return incident, surface, tfs
        else:
            return incident
        

    def plot_deconvolved_motion(self, 
                                time_history: TimeHistory,
                                soil_profile: List[Dict] = None) -> 'matplotlib.figure.Figure':
        """
        Plot the deconvolved motion from the surface motion to the incident wave.
        Args:
            time_history (TimeHistory): Input time history.
            soil_profile (List[Dict], optional): Soil profile to use for deconvolution. If None, uses the default soil profile.
        Returns:
            matplotlib.figure.Figure: The figure object containing the plot.
        """

        bedrock, surface, tfs = self._deconvolve(time_history, soil_profile=soil_profile, return_all=True)

        time = bedrock.time
        incident_acc = bedrock.acceleration
        acc = surface.acceleration
        freq = tfs['freq']
        acc_fft = tfs['inputFFT']
        incident_acc_fft = tfs['outputFFT']
        TF = tfs['TF']
        

        fig, ax = plt.subplots(5,1, figsize=(8, 11))
        blue = '#3182bd'
        box = dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')
        ax[4].plot(time, acc, label='Surface Motion', color= blue)
        ax[4].set_title('Surface Motion', loc='right', y=0.9, bbox=box)
        ax[4].set_xlabel('Time (s)')
        ax[4].set_ylabel('Acceleration (g)')

        ax[3].plot(freq, 
                np.abs(acc_fft), 
                label='Input FFT', 
                color= blue)
        
        ax[3].set_xlim(0, self.f_max)
        ax[3].set_title('Input FFT', loc='right', y=0.9, bbox=box)
        ax[3].set_xlabel('Frequency (Hz)')
        ax[3].set_ylabel('|FFT|')

        ax[2].plot(freq, 
                np.abs(TF), 
                label='Transfer Function', 
                color= blue)
        
        ax[2].set_title('Transfer Function', loc='right', y=0.9, bbox=box)
        ax[2].set_xlabel('Frequency (Hz)')
        ax[2].set_ylabel('|TF|')

        ax[2].set_xlim(0, self.f_max)
        ax[1].plot(freq, 
                np.abs(incident_acc_fft),
                label='Output FFT',
                color= blue)
        ax[1].set_xlim(0, self.f_max)
        
        ax[1].set_title('Output FFT', loc='right', y=0.9, bbox=box)
        ax[1].set_xlabel('Frequency (Hz)')
        ax[1].set_ylabel('|Output FFT|')

        ax[0].plot(time, incident_acc, label='Deconvolved Motion', color= blue)
        # ax[0].plot(time, acc, label='Surface Motion', color='red', alpha=0.5)

        ax[0].set_title('Deconvolved Motion', loc='right', y=0.9, bbox=box)
        ax[0].set_xlabel('Time (s)')
        ax[0].set_ylabel('Acceleration (g)')

        for a in ax:
            a.grid(True, which='both', linestyle='--', linewidth=0.5)
        fig.suptitle('Deconvolved Motion', fontsize=16, fontweight='bold')
        fig.subplots_adjust(top=0.95)  # Adjust top to make room for the title
        fig.tight_layout()
        return fig
    


    def plot_surface_motion(self, time_history: TimeHistory,
                            soil_profile: List[Dict] = None,
                            fig=None, **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot the surface motion.

        Args:
            time_history (TimeHistory): Input time history.
            fig (matplotlib.figure.Figure, optional): Existing figure to plot into.
                If None, a new figure will be created.
            **kwargs: Additional plotting parameters

        Returns:
            matplotlib.figure.Figure: The figure object containing the plot
        """
        import matplotlib.pyplot as plt

        if soil_profile is None:
            soil_profile = self.soil_profile.copy()
        
        acc = time_history.acceleration
        time = time_history.time

        res = self.compute_surface_motion(time_history,
                                          freqFlag=True,
                                          acc_fftFlag=True,
                                          surface_fftFlag=True)
        freq = res['freq']
        acc_fft = res['acc_fft']
        surface_fft = res['surface_fft']
        surface_acc = res['surface_acc']
        time_acc = surface_acc[0]
        surface_acc = surface_acc[1]

        # Use provided figure or create a new one
        if fig is None:
            fig = plt.figure(figsize=(8, 11))
        
        # Clear any existing axes
        fig.clear()
        
        # Create 5 subplots
        axs = [fig.add_subplot(5, 1, i+1) for i in range(5)]
        axs.reverse()
        box = dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')
        blue = '#3182bd'
        red = '#ef3b2c'

        # 1. Time history
        axs[0].plot(time, acc, color=blue)
        axs[0].set_title("Input Time History", loc="right", y=0.9, bbox=box)
        axs[0].set_xlabel("Time (s)")
        axs[0].set_ylabel("Acceleration (g)")

        # 2. Frequency content (FFT magnitude)
        axs[1].plot(freq, np.abs(acc_fft), color=blue)
        axs[1].set_title("Frequency Content (|FFT|)", loc="right", y=0.9, bbox=box)
        axs[1].set_xlabel("Frequency (Hz)")
        axs[1].set_ylabel("|FFT|")
        axs[1].set_xlim(0, self.f_max)

        # 3. Transfer function
        axs[2].plot(self.f, np.abs(self.TF_uu), color=blue)
        axs[2].set_title("Transfer Function", loc="right", y=0.9, bbox=box)
        axs[2].set_xlabel("Frequency (Hz)")
        axs[2].set_ylabel("|TF|")
        axs[2].set_xlim(0, self.f_max)

        # 4. Product in frequency domain
        axs[3].plot(freq, np.abs(surface_fft), color=blue)
        axs[3].set_title("Product: |FFT(input) * TF|", loc="right", y=0.9, bbox=box)
        axs[3].set_xlabel("Frequency (Hz)")
        axs[3].set_ylabel("|Output FFT|")
        axs[3].set_xlim(0, self.f_max)

        # 5. Inverse FFT (surface motion)
        axs[4].plot(time_acc, surface_acc, color=blue,label='Surface Motion')
        axs[4].set_title("Surface Motion (Inverse FFT)", loc="right", y=0.9, bbox=box)
        axs[4].set_xlabel("Time (s)")
        axs[4].set_ylabel("Acceleration (g)")
        axs[4].plot(time_history.time, acc, color=red, alpha=0.7, label='Input Motion')
        axs[4].legend(loc='lower right')

        for i, ax in enumerate(axs):
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        fig.tight_layout()
        return fig
        

    def compute(self, frequency: np.ndarray = None, 
                soil_profile:List[Dict] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute the transfer functions for the soil profile using the transfer matrix method.

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]:
                - Frequencies in Hz
                - TF_uu: u_top/u_base
                - TF_inc: u_top/u_incident
        """
        # Add bedrock layer
        if soil_profile is not None:
            self._check_soil_profile(soil_profile)
        else:
            soil_profile = self.soil_profile.copy()

        bedrock_layer = {**self.rock, 'h': 0.0}
        all_layers = soil_profile + [bedrock_layer]
        num_layers = len(all_layers)

        # Extract properties
        h = np.array([l['h'] for l in all_layers], dtype=float)
        Vs = np.array([l['vs'] for l in all_layers], dtype=float)
        rho = np.array([l['rho'] for l in all_layers], dtype=float)
        xi = np.array([l.get('damping', 0.0) for l in all_layers], dtype=float)
        damptype = np.array([l.get('damping_type', 'constant') for l in all_layers], dtype=str)
        F1 = np.array([l.get('f1', 1.0) for l in all_layers], dtype=float)
        F2 = np.array([l.get('f2', 10.0) for l in all_layers], dtype=float)

        # Pre-compute Rayleigh damping parameters
        omega1 = 2 * np.pi * F1
        omega2 = 2 * np.pi * F2
        A0 = 2 * xi * omega1 * omega2 / (omega1 + omega2)
        A1 = 2 * xi / (omega1 + omega2)

        # Handle frequency array
        if frequency is not None:
            freq_array = np.asarray(frequency, dtype=float)
            if np.any(freq_array < 0):
                raise ValueError("Frequency values must be positive.")
            freq_array = np.sort(freq_array)
            freq_array[0] = max(freq_array[0], 1.0e-8)
        else:
            self.freq_resolution = 0.05
            TF_size = int(np.floor(self.f_max / self.freq_resolution))
            freq_array = np.linspace(self.freq_resolution, self.freq_resolution * TF_size, num=TF_size)

        # Compute damping per layer and frequency
        damping = np.zeros((num_layers, len(freq_array)))
        for j in range(num_layers):
            if damptype[j].lower() == "constant":
                damping[j, :] = xi[j]
            elif damptype[j].lower() == "rayleigh":
                w = 2 * np.pi * freq_array
                damping[j, :] = A0[j] / (2 * w) + A1[j] * w / 2

        # Initialize output arrays
        TF_uu = np.ones(len(freq_array), dtype=np.complex128)
        TF_inc = np.ones(len(freq_array), dtype=np.complex128)
        j_index = np.arange(num_layers - 2, -1, -1, dtype=int)  # Loop from bottom to top

        # Compute complex Vs* and alpha* for all frequencies
        omega_all = 2 * np.pi * freq_array                             # (n_freq,)
        vs_star_f = Vs[:, None] * np.sqrt(1 + 2j * damping)            # (num_layers, n_freq)
        k_star_f  = omega_all[None, :] / vs_star_f                     # (num_layers, n_freq)
        alpha_star_f = (rho[:-1, None] * vs_star_f[:-1]) / (rho[1:, None] * vs_star_f[1:])  # (num_layers-1, n_freq)
        e_pos_f = np.exp(1j * k_star_f[:-1] * h[:-1, None])            # (num_layers-1, n_freq)
        e_neg_f = np.exp(-1j * k_star_f[:-1] * h[:-1, None])           # (num_layers-1, n_freq)


        for i in range(len(freq_array)):
            alpha_star = alpha_star_f[:, i]
            e_pos = e_pos_f[:, i]
            e_neg = e_neg_f[:, i]

            # Initialize transfer matrix
            E = np.eye(2, dtype=np.complex128)

            # Loop over layers (bottom to top)
            for j in j_index:
                alpha = alpha_star[j]
                D = 0.5 * np.array([
                    [(1 + alpha) * e_pos[j], (1 - alpha) * e_neg[j]],
                    [(1 - alpha) * e_pos[j], (1 + alpha) * e_neg[j]]
                ], dtype=np.complex128)
                E = E @ D

            # Compute transfer functions
            TF_inc[i] = 2.0 / (E[0, 0] + E[0, 1])
            TF_uu[i]  = 2.0 / (E[0, 0] + E[0, 1] + E[1, 0] + E[1, 1])

        # Store and return results
        self.f = freq_array
        self.TF_uu = TF_uu
        self.TF_inc = TF_inc
        self.TF_ro = TF_inc / 2.0
        self.computed = True

        return self.f, self.TF_uu, self.TF_inc
    


    def compute_all_layers(self, 
                           frequency: np.ndarray = None,
                           soil_profile: List[Dict] = None
                           ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        
        """
        Compute the transfer functions for all layers in the soil profile.
        This method computes the transfer functions for all layers in the soil profile
        using the transfer matrix method. It returns the frequencies, transfer function matrices. 

        Args:
            frequency (np.ndarray, optional): Array of frequencies in Hz.
                If None, uses default frequency range.
            soil_profile (List[Dict], optional): List of dictionaries containing soil layer properties.
                If None, uses the current soil profile.

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]:
                - Frequencies in Hz
                - TF_uu: Transfer function for u_top/u_base
                - TF_inc: Transfer function for u_top/u_incident
        """
        if soil_profile is not None:
            self._check_soil_profile(soil_profile)
        else:
            soil_profile = self.soil_profile.copy()

        # Add bedrock layer
        bedrock_layer = {**self.rock, 'h': 0.0}
        all_layers = soil_profile + [bedrock_layer]
        num_layers = len(all_layers)
        # Extract properties
        h = np.array([l['h'] for l in all_layers], dtype=float)
        Vs = np.array([l['vs'] for l in all_layers], dtype=float)
        rho = np.array([l['rho'] for l in all_layers], dtype=float)
        xi = np.array([l.get('damping', 0.0) for l in all_layers], dtype=float)
        damptype = np.array([l.get('damping_type', 'constant') for l in all_layers], dtype=str)

        F1 = np.array([l.get('f1', 1.0) for l in all_layers], dtype=float)
        F2 = np.array([l.get('f2', 10.0) for l in all_layers], dtype=float)
        # Pre-compute Rayleigh damping parameters
        omega1 = 2 * np.pi * F1
        omega2 = 2 * np.pi * F2
        A0 = 2 * xi * omega1 * omega2 / (omega1 + omega2)
        A1 = 2 * xi / (omega1 + omega2)
        # Handle frequency array
        if frequency is not None:
            freq_array = np.asarray(frequency, dtype=float)
            if np.any(freq_array < 0):
                raise ValueError("Frequency values must be positive.")
            freq_array = np.sort(freq_array)
            freq_array[0] = max(freq_array[0], 1.0e-8)
        else:
            self.freq_resolution = 0.05
            TF_size = int(np.floor(self.f_max / self.freq_resolution))
            freq_array = np.linspace(self.freq_resolution, self.freq_resolution * TF_size, num=TF_size)

        # Compute damping per layer and frequency
        damping = np.zeros((num_layers, len(freq_array)))
        for j in range(num_layers):
            if damptype[j].lower() == "constant":
                damping[j, :] = xi[j]
            elif damptype[j].lower() == "rayleigh":
                w = 2 * np.pi * freq_array
                damping[j, :] = A0[j] / (2 * w) + A1[j] * w / 2
        # Initialize output arrays

        # Compute complex Vs* and alpha* for all frequencies
        omega_all = 2 * np.pi * freq_array                             # (n_freq,)
        vs_star_f = Vs[:, None] * np.sqrt(1 + 2j * damping)            # (num_layers, n_freq)
        k_star_f  = omega_all[None, :] / vs_star_f                     # (num_layers, n_freq)
        k_star = k_star_f.T  # (n_freq, num_layers)

        alpha_star_f = (rho[:-1, None] * vs_star_f[:-1]) / (rho[1:, None] * vs_star_f[1:])  # (num_layers-1, n_freq)
        alpha_star_f = alpha_star_f.T 

        A = np.zeros((len(freq_array), num_layers), dtype=np.complex128)
        B = np.zeros((len(freq_array), num_layers), dtype=np.complex128)
        A[:, 0] = 1
        B[:, 0] = 1

        # Precompute exponentials for all (freq, layer)
        exp_pos = np.exp(1j * k_star[:, :-1] * h[:-1])   # (n_freq, num_layers-1)
        exp_neg = np.exp(-1j * k_star[:, :-1] * h[:-1])  # (n_freq, num_layers-1)

        # Propagate A, B through layers
        for k in range(num_layers - 1):
            a = A[:, k]
            b = B[:, k]
            alpha = alpha_star_f[:, k]
            A[:, k + 1] = 0.5 * a * (1 + alpha) * exp_pos[:, k] + 0.5 * b * (1 - alpha) * exp_neg[:, k]
            B[:, k + 1] = 0.5 * a * (1 - alpha) * exp_pos[:, k] + 0.5 * b * (1 + alpha) * exp_neg[:, k]

        # Compute transfer function
        H = (A + B) / (A[:, [-1]] + B[:, [-1]])  # (n_freq, num_layers)
        H[0] = np.real(H[0]) 

        return freq_array, H
    
    

    def plot_soil_profile(self, ax=None, **kwargs) -> 'matplotlib.figure.Figure':
        """
        Plot the soil profile.
        
        Args:
            ax (matplotlib.axes.Axes, optional): Existing axes to plot into.
                If None, a new figure and axes will be created
            **kwargs: Additional plotting parameters passed to matplotlib.pyplot
            
        Returns:
            matplotlib.figure.Figure: The figure object containing the plot
        """
        # Use provided axes if available, otherwise create a new figure and axes
        fig = None
        if ax is None:
            fig = plt.figure(figsize=(2, 8))
            ax = fig.add_subplot(111)
        else:
            fig = ax.figure
        
        # Calculate depths
        depths = np.cumsum([0] + [layer["h"] for layer in self.soil_profile])
        
        # Plot soil layers
        for i in range(len(depths)-1):
            ax.fill_between([0, 1], [depths[i], depths[i]], 
                           [depths[i+1], depths[i+1]], alpha=0.3)
            ax.plot([0, 1], [depths[i], depths[i]], 'k-')
            ax.plot([0, 1], [depths[i+1], depths[i+1]], 'k-')
        
        # Plot rock
        rockdepth = depths[-1] * 1.2
        ax.fill_between([0, 1], [depths[-1], depths[-1]], 
                        [rockdepth, rockdepth], alpha=0.3, color='gray',
                        hatch='//')
        ax.text(0.5, (depths[-1] + rockdepth) / 2, "∞", 
               ha='center', va='center', fontsize=12, color='black')
        
        ax.invert_yaxis()
        ax.set_ylim(top=0, bottom=rockdepth)
        ax.set_xlim(0, 1)
        ax.set_xticks([])  # Remove x-axis ticks
        ax.set_xticklabels([])  # Remove x-axis labels
        fig.tight_layout()
        
        return fig

    def add_layer(self, layer: Dict, position: Optional[int] = None) -> None:
        """
        Add a new soil layer to the profile.

        This method adds a new soil layer to the profile at the specified position
        and recomputes the transfer function.

        Args:
            layer (Dict): Dictionary containing layer properties:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float, optional): Material damping ratio
            position (Optional[int]): Position to insert the layer (0-based).
                If None, adds to the bottom of the profile.

        Raises:
            ValueError: If required layer properties are missing
            IndexError: If position is out of range

        Example:
            >>> tf.add_layer({"h": 5.0, "vs": 300.0, "rho": 1500.0, "damping": 0.05})
            >>> tf.add_layer({"h": 3.0, "vs": 250.0, "rho": 1500.0}, position=0)
        """
        if position is None:
            self.soil_profile.append(layer)
        else:
            self.soil_profile.insert(position, layer)

    def remove_layer(self, position: int) -> None:
        """
        Remove a soil layer from the profile.

        This method removes a soil layer from the profile at the specified position
        and recomputes the transfer function.

        Args:
            position (int): Position of the layer to remove (0-based)

        Raises:
            IndexError: If position is out of range

        Example:
            >>> tf.remove_layer(0)  # Remove the top layer
        """
        if 0 <= position < len(self.soil_profile):
            # check if the length of the soil profile is greater than 1
            if len(self.soil_profile) == 1:
                raise ValueError("Cannot remove the last layer")
            self.soil_profile.pop(position)
        else:
            raise IndexError("Layer position out of range")

    def modify_layer(self, position: int, **properties) -> None:
        """
        Modify properties of an existing soil layer.

        This method updates the properties of a soil layer at the specified position
        and recomputes the transfer function.

        Args:
            position (int): Position of the layer to modify (0-based)
            **properties: Layer properties to update:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Raises:
            IndexError: If position is out of range

        Example:
            >>> tf.modify_layer(0, vs=250.0, damping=0.06)
            >>> tf.modify_layer(1, h=10.0, rho=1600.0)
        """
        if 0 <= position < len(self.soil_profile):
            properties = dict(properties)
            
            if not self._check_soil_profile([properties]):
                raise ValueError("Invalid layer properties")
            self.soil_profile[position].update(properties)
        else:
            raise IndexError("Layer position out of range")
        
    def update_soil_profile(self, soil_profile: List[Dict]) -> None:
        """
        Update the soil profile.
        """
        if not self._check_soil_profile(soil_profile):
            raise ValueError("Invalid soil profile")
        self.soil_profile = soil_profile
        self.computed = False

    def _check_soil_profile(self, soil_profile: List[Dict]) -> bool:
        """
        Check if the soil profile is valid.
        Args:
            soil_profile (List[Dict]): The soil profile to check.

        Returns:
            bool: True if the soil profile is valid, False otherwise.
        
        Raises:
            ValueError: If the soil profile is not valid.
        """
        if not isinstance(soil_profile, list):
            raise ValueError("soil_profile must be a list")
        if len(soil_profile) == 0:
            raise ValueError("soil_profile must not be empty")
        if not all(isinstance(layer, dict) for layer in soil_profile):
            raise ValueError("soil_profile must be a list of dictionaries")
        if not all(key in layer for layer in soil_profile for key in ["h", "vs", "rho", "damping"]):
            raise ValueError("soil_profile must contain the keys: h, vs, rho, damping")
        if not all(isinstance(layer["h"], (int, float)) and layer["h"] > 0 for layer in soil_profile):
            raise ValueError("all layer thicknesses must be positive numbers")
        if not all(isinstance(layer["vs"], (int, float)) and layer["vs"] > 0 for layer in soil_profile):
            raise ValueError("all shear wave velocities must be positive numbers")
        if not all(isinstance(layer["rho"], (int, float)) and layer["rho"] > 0 for layer in soil_profile):
            raise ValueError("all mass densities must be positive numbers")
        if not all(isinstance(layer["damping"], (int, float)) and 0 <= layer["damping"] <= 1 for layer in soil_profile):
            raise ValueError("all damping values must be between 0 and 1")
        return True

    def update_rock(self, rock: Dict) -> None:
        """
        Update the rock properties.
        """
        if not self._check_rock(rock):
            raise ValueError("Invalid rock properties")
        self.rock = rock
        self.computed = False

    def _check_rock(self, rock: Dict) -> bool:
        """
        Check if the rock properties are valid.
        """
        if not isinstance(rock, dict):
            raise ValueError("rock must be a dictionary")
        if not all(key in rock for key in ["vs", "rho", "damping"]):
            raise ValueError("rock must contain the keys: vs, rho, damping")
        if not all(isinstance(value, (int, float)) for value in rock.values()):
            raise ValueError("all rock values must be numbers")
        if rock["vs"] <= 0 or rock["rho"] <= 0:
            raise ValueError("rock vs and rho must be positive")
        if rock["damping"] < 0 or rock["damping"] > 1:
            raise ValueError("rock damping must be between 0 and 1")
        return True
    
    def update_frequency(self, f_max: float) -> None:
        """
        Update the maximum frequency of interest.

        Args:
            f_max (float): New maximum frequency in Hz

        Example:
            >>> tf.update_frequency(30.0)
        """
        if f_max <= 0:
            raise ValueError("f_max must be positive")
        self.f_max = f_max
        self.computed = False

    def get_total_depth(self) -> float:
        """
        Get the total depth of the soil profile.

        Returns:
            float: Total depth of the soil profile in meters

        Example:
            >>> depth = tf.get_total_depth()
            >>> print(f"Total depth: {depth:.2f} m")
        """
        return sum(layer["h"] for layer in self.soil_profile)

    def get_fundamental_frequency(self) -> float:
        """
        Estimate the fundamental frequency of the soil profile.

        This method estimates the fundamental frequency by finding the frequency
        at which the transfer function has its maximum amplification.

        Returns:
            float: Fundamental frequency in Hz

        Example:
            >>> f0 = tf.get_fundamental_frequency()
            >>> print(f"Fundamental frequency: {f0:.2f} Hz")
        """
        return self.f[np.argmax(np.abs(self.TF_uu))]

    def get_amplification_factor(self) -> float:
        """
        Get the maximum amplification factor.

        This method returns the maximum amplification factor from the transfer function,
        which represents the maximum ratio of surface to base motion.

        Returns:
            float: Maximum amplification factor

        Example:
            >>> max_amp = tf.get_amplification_factor()
            >>> print(f"Maximum amplification: {max_amp:.2f}")
        """
        return np.max(np.abs(self.TF_uu))

    def get_layer_properties(self, position: int) -> Dict:
        """
        Get properties of a specific layer.

        This method returns a copy of the properties of the layer at the specified position.

        Args:
            position (int): Position of the layer (0-based)

        Returns:
            Dict: Dictionary containing layer properties:
                - h (float): Layer thickness in meters
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Raises:
            IndexError: If position is out of range

        Example:
            >>> props = tf.get_layer_properties(0)
            >>> print(f"Layer properties: {props}")
        """
        if 0 <= position < len(self.soil_profile):
            return self.soil_profile[position].copy()
        else:
            raise IndexError("Layer position out of range")

    def get_rock_properties(self) -> Dict:
        """
        Get properties of the rock layer.

        This method returns a copy of the properties of the underlying rock layer.

        Returns:
            Dict: Dictionary containing rock properties:
                - vs (float): Shear wave velocity in m/s
                - rho (float): Mass density in kg/m³
                - damping (float): Material damping ratio

        Example:
            >>> rock_props = tf.get_rock_properties()
            >>> print(f"Rock properties: {rock_props}")
        """
        return self.rock.copy()

    def get_profile_summary(self) -> Dict:
        """
        Get a comprehensive summary of the soil profile.

        This method returns a dictionary containing various properties and
        characteristics of the soil profile.

        Returns:
            Dict: Dictionary containing:
                - total_depth (float): Total depth of the soil profile in meters
                - num_layers (int): Number of soil layers
                - layer_thicknesses (List[float]): List of layer thicknesses
                - fundamental_frequency (float): Fundamental frequency in Hz
                - max_amplification (float): Maximum amplification factor

        Example:
            >>> summary = tf.get_profile_summary()
            >>> print(f"Profile summary: {summary}")
        """
        return {
            "total_depth": self.get_total_depth(),
            "num_layers": len(self.soil_profile),
            "layer_thicknesses": [layer["h"] for layer in self.soil_profile],
        }



# ------------------- example / quick test ------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt 
    import os
    os.chdir(os.path.dirname(__file__))
    soil = [
        {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
        {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    ]

    rock = {
        "vs": 850.0,
        "rho": 1500.0,
        "damping": 0.05,
    }

    soil = [
      {"h": 100,  "vs": 199.5, "rho": 15.3*1000/9.81, "damping": 0.03 },
       ]
    rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}

    # Create transfer function instance
    tf = TransferFunction(soil, rock, f_max=30.0)









    # # # Example: load a PEER file
    record = TimeHistory.load(acc_file="../../../examples/DRM/Example4/ricker.acc",
                              time_file="../../../examples/DRM/Example4/ricker.time")
    
    # record = TimeHistory.load(acc_file="C:\Users\aminp\OneDrive\Desktop\DRMGUI\examples\DRM\Example4\ricker.acc",
                            # time_file="C:/Users/aminp/OneDrive/Desktop/DRMGUI\examples\DRM\Example4\ricker.time")

    tf.compute()
    tf.plot_soil_profile()
    tf.plot_convolved_motion(record, soil_profile=soil)

    plt.show()




