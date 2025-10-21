import pyvista as pv
import numpy as np
import os
import h5py
from typing import Optional, Dict

# ----------------------------------------------------------------------------
# Helper to write a minimal PolyData VTKHDF file with transient displacement
# ---------------------------------------------------------------------------


# Use Optional / Dict for Python < 3.10 compatibility
def write_vtkhdf_unstructured(
    points: np.ndarray,
    filename: str,
    time: Optional[np.ndarray] = None,
    arrays: Optional[Dict[str, np.ndarray]] = None,
) -> None:
    """Write an *UnstructuredGrid* VTKHDF file.

    Parameters
    ----------
    points
        (n_points, 3) array of coordinates.
    filename
        Output file path (``.vtkhdf``).
    time
        Optional (n_steps,) array of time values. Required if *arrays* are
        provided.
    arrays
        Optional mapping ``{array_name: data}`` where *data* has shape
        ``(n_steps, n_points, 3)``. Each array is written in PointData.
    """

    n_points = points.shape[0]

    has_time = arrays is not None and len(arrays) > 0 and time is not None
    if has_time:
        n_steps = time.shape[0]
    else:
        n_steps = 0

    # ---- index dtype (VTK convention) ----
    idx_dtype = np.int32  # match working file

    if has_time:
        # Pre-compute offsets required by the `Steps` group
        point_offsets = np.zeros(n_steps, dtype=idx_dtype)
        part_offsets = np.zeros(n_steps, dtype=idx_dtype)
        n_parts = np.ones(n_steps, dtype=idx_dtype)
        pd_offsets = np.arange(0, n_steps * n_points, n_points, dtype=idx_dtype)

    with h5py.File(filename, "w") as f:
        root = f.create_group("VTKHDF")

        # ----- Metadata -----
        root.attrs["Version"] = (2, 3)
        root.attrs.create("Type", b"UnstructuredGrid", dtype=h5py.string_dtype("ascii"))

        # ---------------- Geometry (static in time) ----------------
        root.create_dataset("NumberOfPoints", data=np.array([n_points], dtype=idx_dtype))
        root.create_dataset("Points", data=points.astype(np.float64))

        # ---------------- Topology as VTK_VERTEX cells ----------------
        connectivity = np.arange(n_points, dtype=idx_dtype)
        offsets = np.arange(0, n_points + 1, dtype=idx_dtype)  # length = cells+1
        types_arr = np.ones(n_points, dtype=np.uint8)  # 1 = VTK_VERTEX

        root.create_dataset("Connectivity", data=connectivity)
        root.create_dataset("Offsets", data=offsets)
        root.create_dataset("Types", data=types_arr)

        # per-part summary datasets (shape (1,))
        root.create_dataset("NumberOfCells", data=np.array([n_points], dtype=idx_dtype))
        root.create_dataset("NumberOfConnectivityIds", data=np.array([connectivity.size], dtype=idx_dtype))

        if has_time:
            # ---------------- PointData arrays ----------------
            pd = root.create_group("PointData")
            for name, data in arrays.items():
                flat = data.reshape(n_steps * n_points, 3).astype(np.float64)
                pd.create_dataset(name, data=flat, maxshape=(None, 3))

        if has_time:
            steps = root.create_group("Steps")
            steps.attrs["NSteps"] = n_steps
            steps.create_dataset("Values", data=time.astype(np.float32))
            steps.create_dataset("PartOffsets", data=part_offsets)
            steps.create_dataset("NumberOfParts", data=n_parts)
            steps.create_dataset("PointOffsets", data=point_offsets)

            # Cell-related offsets – mesh is static
            zeros1 = np.zeros((n_steps, 1), dtype=idx_dtype)
            steps.create_dataset("CellOffsets", data=zeros1)
            steps.create_dataset("ConnectivityIdOffsets", data=zeros1)

            # PointData offsets
            pdo = steps.create_group("PointDataOffsets")
            for name in arrays.keys():
                pdo.create_dataset(name, data=pd_offsets)

    print(f"Wrote VTKHDF file: {filename}")

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
files = os.listdir("./Results")
path = "./Results"
for filename in files:
    if filename.startswith("EmbeddedBeamSolidInterface_"):
        fname = os.path.join(path, filename)
        points = np.loadtxt(fname, 
                            delimiter="\t",
                            usecols=(1, 2, 3))
        interface_name = filename.split("EmbeddedBeamSolidInterface")[1].split(".")[0]
        print(f"Processing interface: {interface_name}")
        disp_file = os.path.join(path, f"EmbeddedBeamSolid{interface_name}_displacement.out")
        arrays = {}

        # --- mandatory displacement (reference for time axis) ---
        if os.path.exists(disp_file):
            raw = np.loadtxt(disp_file, delimiter=" ")
            time = raw[:, 0]
            disp = raw[:, 1:]
            assert disp.shape[1] / 3 == points.shape[0], "Displacement data does not match points"
            arrays["Displacement"] = disp.reshape(len(time), points.shape[0], 3)
            

        # Optional additional responses
        extras = [
            "localDisplacement",
            "axialDisp",
            "radialDisp",
            "tangentialDisp",
            "globalForce",
            "localForce",
            "axialForce",
            "radialForce",
            "tangentialForce",
        ]

        for suffix in extras:
            extra_path = os.path.join(path, f"EmbeddedBeamSolid{interface_name}_{suffix}.out")
            if os.path.exists(extra_path):
                raw = np.loadtxt(extra_path, delimiter=" ")
                # verify time consistency with displacement
                if "time" in locals():
                    assert np.allclose(raw[:, 0], time), f"Time mismatch in {suffix}"
                else:
                    time = raw[:, 0]
                data = raw[:, 1:]
                assert data.shape[1] / 3 == points.shape[0], f"{suffix} data does not match points"
                arrays[suffix] = data.reshape(len(raw[:, 0]), points.shape[0], 3)

        # Determine if we have temporal data
        interface_name = interface_name.replace("_", "", 1)
        if arrays:
            out_name = os.path.join(path, f"{interface_name}.vtkhdf")
            write_vtkhdf_unstructured(points, out_name, time, arrays)
        else:
            # Write just the mesh without Steps group
            out_name = os.path.join(path, f"{interface_name}.vtkhdf")
            write_vtkhdf_unstructured(points, out_name)








