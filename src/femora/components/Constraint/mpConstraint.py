from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
from femora.components.Assemble.Assembler import Assembler
from pykdtree.kdtree import KDTree
import numpy as np

class mpConstraint(ABC):
    """Base class for OpenSees multi-point constraints"""
    
    # Class variable to store all MP constraints
    _constraints: Dict[int, 'mpConstraint'] = {}
    

    def __init__(self, master_node: int, slave_nodes: List[int]):
        """
        Initialize the base MP constraint
        
        Args:
            master_node: Tag of the master/retained node
            slave_nodes: List of slave/constrained node tags
        """
        self.master_node = master_node
        self.slave_nodes = slave_nodes
        self.tag = mpConstraint._next_tag()
        mpConstraint._constraints[self.tag] = self
        
    
    @classmethod
    def _next_tag(cls) -> int:
        """Get the next available tag"""
        return len(cls._constraints) + 1
    
    @classmethod
    def get_constraint(cls, tag: int) -> 'mpConstraint':
        """Get a constraint by its tag"""
        return cls._constraints.get(tag)
    
    @classmethod
    def remove_constraint(cls, tag: int) -> None:
        """Remove a constraint and reorder remaining tags"""
        if tag in cls._constraints:
            del cls._constraints[tag]
            # Reorder remaining constraints
            constraints = sorted(cls._constraints.items())
            cls._constraints.clear()
            for new_tag, (_, constraint) in enumerate(constraints, 1):
                constraint.tag = new_tag
                cls._constraints[new_tag] = constraint
    
    @abstractmethod
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        pass





class equalDOF(mpConstraint):
    """Equal DOF constraint"""
    
    def __init__(self, master_node: int, slave_nodes: List[int], dofs: List[int]):
        """
        Initialize EqualDOF constraint
        
        Args:
            master_node: Retained node tag
            slave_node: Constrained node tag
            dofs: List of DOFs to be constrained
        """
        super().__init__(master_node, slave_nodes)
        self.dofs = dofs
    
    def to_tcl(self) -> str:
        tcl_str = ""
        for slave in self.slave_nodes:
            dofs_str = " ".join(str(dof) for dof in self.dofs)
            tcl_str += f"equalDOF {self.master_node} {slave} {dofs_str}"
        return tcl_str







class rigidLink(mpConstraint):
    """Rigid link constraint"""
    
    def __init__(self, type_str: str, master_node: int, slave_nodes: List[int]):
        """
        Initialize RigidLink constraint
        
        Args:
            type_str: Type of rigid link ('bar' or 'beam')
            master_node: Retained node tag
            slave_node: Constrained node tag
        """
        super().__init__(master_node, slave_nodes)
        if type_str not in ['bar', 'beam']:
            raise ValueError("RigidLink type must be 'bar' or 'beam'")
        self.type = type_str
    
    def to_tcl(self) -> str:
        tcl_str = ""
        for slave in self.slave_nodes:
            tcl_str += f"rigidLink {self.type} {self.master_node} {slave}"
        # return f"rigidLink {self.type} {self.master_node} {self.slave_nodes[0]}"






class rigidDiaphragm(mpConstraint):
    """Rigid diaphragm constraint"""
    
    def __init__(self, direction: int, master_node: int, slave_nodes: List[int]):
        """
        Initialize RigidDiaphragm constraint
        
        Args:
            direction: Direction perpendicular to rigid plane (3D) or direction of motion (2D)
            master_node: Retained node tag
            slave_nodes: List of constrained node tags
        """
        super().__init__(master_node, slave_nodes)
        self.direction = direction
    
    def to_tcl(self) -> str:
        slaves_str = " ".join(str(node) for node in self.slave_nodes)
        return f"rigidDiaphragm {self.direction} {self.master_node} {slaves_str}"
    






class mpConstraintManager:
    """
    Singleton class to manage MP constraints.
    This class provides methods to create and manage different types of constraints
    such as EqualDOF, RigidLink, and RigidDiaphragm. It ensures that only one instance
    of the class exists and provides a global point of access to it.
    """   
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(mpConstraintManager, cls).__new__(cls)
        return cls._instance

    def create_equal_dof(self, master_node: int, slave_nodes: List[int], dofs: List[int]) -> equalDOF:
        """
        Create an EqualDOF constraint.

        Parameters:
        master_node (int): The master node ID.
        slave_nodes (List[int]): A list of slave node IDs.
        dofs (List[int]): A list of degrees of freedom to be constrained.

        Returns:
        equalDOF: An instance of the equalDOF constraint.
        """
        """Create an EqualDOF constraint"""
        return equalDOF(master_node, slave_nodes, dofs)


    def create_rigid_link(self, type_str: str, master_node: int, slave_nodes: List[int]) -> rigidLink:
        """
        Create a RigidLink constraint.

        Args:
            type_str (str): The type of the rigid link.
            master_node (int): The master node ID.
            slave_nodes (List[int]): A list of slave node IDs.

        Returns:
            rigidLink: An instance of the rigidLink class representing the constraint.
        """
        return rigidLink(type_str, master_node, slave_nodes)


    def create_rigid_diaphragm(self, direction: int, master_node: int, slave_nodes: List[int]) -> rigidDiaphragm:
        """
        Create a RigidDiaphragm constraint.

        Parameters:
        direction (int): The direction of the rigid diaphragm constraint.
        master_node (int): The master node ID for the rigid diaphragm.
        slave_nodes (List[int]): A list of slave node IDs that will be constrained by the rigid diaphragm.

        Returns:
        rigidDiaphragm: An instance of the rigidDiaphragm class representing the created constraint.
        """
        return rigidDiaphragm(direction, master_node, slave_nodes)


    def create_laminar_boundary(self, dofs: List[int], bounds: Tuple[float, float], direction: int = 3, tol: float = 1e-2) -> None:
        """
        Create a laminar boundary constraint.

        Parameters:
            dofs (List[int]): A list of degrees of freedom to be constrained.
            direction (int): The direction of the perpendicular plane that will be used to create the laminar boundary.
            tol (float): The tolerance value for the laminar boundary condition.

        Note:
            The direction must be 1, 2, or 3.
            This function will check if the mesh is 3D, and the boundaries will be box-shaped or cylinder-shaped.

        Returns:
            None
        """
        from femora.components.MeshMaker import MeshMaker

        assembler = Assembler()
        # check if the AssembeledMesh is not None
        if assembler.AssembeledMesh is None:
            raise ValueError("AssembeledMesh is not created yet")

        mesh = assembler.AssembeledMesh.copy()
        surface = mesh.extract_surface()
        xmin, xmax, ymin, ymax, zmin, zmax = surface.bounds
        eps = tol
        if direction == 3:
            xmin += eps
            xmax -= eps
            ymin += eps
            ymax -= eps
            zmin -= eps
            zmax += eps
        elif direction == 2:
            xmin += eps
            xmax -= eps
            ymin -= eps
            ymax += eps
            zmin += eps
            zmax -= eps
        elif direction == 1:
            xmin -= eps
            xmax += eps
            ymin += eps
            ymax -= eps
            zmin += eps
            zmax -= eps
        else:
            raise ValueError("Direction must be 1, 2, or 3")
        

        ind = surface.find_cells_within_bounds((xmin, xmax, ymin, ymax, zmin, zmax))
        surface = surface.extract_cells(ind,invert=True)
        points = surface.points
        tolerance = tol

        kdtree = KDTree(mesh.points)
        distances, indices = kdtree.query(points, k=1)
        nodeTags = indices + MeshMaker()._start_nodetag
        
        # attach the nodeTags to the points at the first column
        z = points[:, direction-1]

        # filter the z based on bounds
        boundmin = bounds[0]
        boundmax = bounds[1]
        mask = (z >= boundmin - tolerance) & (z <= boundmax + tolerance)
        z = z[mask]
        nodeTags = nodeTags[mask]
        points = points[mask]

        z_rounded = np.round(z / tolerance) * tolerance

        # Use np.unique with return_inverse to group fast
        unique_z, group_ids = np.unique(z_rounded, return_inverse=True)
    

        # Build dictionary-like grouping in NumPy style
        Taggroups = [nodeTags[group_ids == i] for i in range(len(unique_z))]
        groups = [points[group_ids == i] for i in range(len(unique_z))]

        # now add mp constraints
        for i, group in enumerate(Taggroups):
            if len(group) > 1:
                # self.create_equal_dof(master_node=group[0], slave_nodes=group[1:], dofs=dofs)
                for slave in group[1:]:
                    self.create_equal_dof(master_node=group[0], slave_nodes=[slave], dofs=dofs)

        # import pyvista as pv
        # pl = pv.Plotter()
        # for i, group in enumerate(groups):
        #     if len(group) > 1:  
        #         pl.add_mesh(pv.PolyData(group[0]), color='black', point_size=10, render_points_as_spheres=True)
        #         pl.add_mesh(pv.PolyData(group[1:]), color='red', point_size=5, render_points_as_spheres=True)

        # pl.add_mesh(assembler.AssembeledMesh, color='lightblue', opacity=0.5,show_edges=False)
        # pl.show()
        # exit(0)

    


    def create_equal_dof_between_meshparts(self, meshpart_master: str, meshpart_slave: str, dofs: List[int], tol: float = 1e-5) -> None:
        """
        Create equalDOF constraints between two mesh parts by matching coincident points.

        The master nodes are taken from the first mesh part and the slave nodes from the second.
        For each master point, the nearest slave point within the specified tolerance is paired
        and an equalDOF constraint is created for the requested DOFs.

        Args:
            meshpart_master: User name of the master mesh part.
            meshpart_slave: User name of the slave mesh part.
            dofs: List of 1-based DOF indices to constrain.
            tol: Spatial tolerance for coincidence detection.

        Raises:
            ValueError: If the assembled mesh is missing, mesh parts are not found, or DOFs invalid.
        """
        # Local imports to avoid circular dependencies
        from femora.components.Mesh.meshPartBase import MeshPart
        from femora.components.MeshMaker import MeshMaker

        assembler = Assembler()
        if assembler.AssembeledMesh is None:
            raise ValueError("AssembeledMesh is not created yet")

        master_part = MeshPart.get_mesh_parts().get(meshpart_master)
        slave_part = MeshPart.get_mesh_parts().get(meshpart_slave)
        if master_part is None:
            raise ValueError(f"MeshPart '{meshpart_master}' not found")
        if slave_part is None:
            raise ValueError(f"MeshPart '{meshpart_slave}' not found")

        # Validate DOFs against both parts' ndf
        ndf_master = master_part.element._ndof
        ndf_slave = slave_part.element._ndof
        max_common = min(ndf_master, ndf_slave)
        if any((d < 1 or d > max_common) for d in dofs):
            raise ValueError(f"Requested DOFs {dofs} invalid for master ndf={ndf_master} and slave ndf={ndf_slave}")

        assembled = assembler.get_mesh()
        points = assembled.points
        master_idx = assembled.extract_values(values = master_part.tag ,scalars= "MeshPartTag_celldata", preference="cell")
        slave_idx = assembled.extract_values(values = slave_part.tag ,scalars= "MeshPartTag_celldata", preference="cell")
        master_idx = master_idx.point_data["vtkOriginalPointIds"]
        slave_idx = slave_idx.point_data["vtkOriginalPointIds"]

        # check that length of master_idx is equal to number of points in master_part
        if len(master_idx) != master_part.mesh.n_points:
            print(f"Warning: Number of points in master mesh part '{meshpart_master}' ({master_part.number_of_points}) does not match points found in assembled mesh ({len(master_idx)}).")
        if len(slave_idx) != slave_part.mesh.n_points:
            print(f"Warning: Number of points in slave mesh part '{meshpart_slave}' ({slave_part.number_of_points}) does not match points found in assembled mesh ({len(slave_idx)}).")
        
        if master_idx.size == 0:
            raise ValueError(f"No points found for master mesh part '{meshpart_master}' in assembled mesh")
        if slave_idx.size == 0:
            raise ValueError(f"No points found for slave mesh part '{meshpart_slave}' in assembled mesh")

        master_pts = points[master_idx]
        slave_pts = points[slave_idx]

        tree = KDTree(slave_pts)
        distances, nearest = tree.query(master_pts, k=1)

        start_node_tag = MeshMaker()._start_nodetag

        for i, (dist, j) in enumerate(zip(distances, nearest)):
            if dist <= tol:
                master_point_idx = int(master_idx[i])
                slave_point_idx = int(slave_idx[j])
                master_node_tag = master_point_idx + start_node_tag
                slave_node_tag = slave_point_idx + start_node_tag
                self.create_equal_dof(master_node=master_node_tag, slave_nodes=[slave_node_tag], dofs=dofs)

    def create_constraint(self, constraint_type: str, *args) -> mpConstraint:
        """
        Create a constraint based on the specified type.

        Parameters:
            constraint_type (str): The type of constraint to create. Supported types are "equalDOF", "rigidLink", and "rigidDiaphragm".
            *args: Additional arguments required for creating the specific type of constraint.

        Returns:
            mpConstraint: An instance of the created constraint.

        Raises:
            ValueError: If an unknown constraint type is provided.
        """
        if constraint_type == "equalDOF":
            return self.create_equal_dof(*args)
        elif constraint_type == "rigidLink":
            return self.create_rigid_link(*args)
        elif constraint_type == "rigidDiaphragm":
            return self.create_rigid_diaphragm(*args)
        else:
            raise ValueError(f"Unknown constraint type: {constraint_type}")


    def get_constraint(self, tag: int) -> mpConstraint:
        """
        Retrieve a constraint by its tag.

        Args:
            tag (int): The tag identifier of the constraint.

        Returns:
            mpConstraint: The constraint object associated with the given tag.
        """
        """Get a constraint by its tag"""
        return mpConstraint.get_constraint(tag)


    def remove_constraint(self, tag: int) -> None:
        """
        Remove a constraint by its tag.

        Parameters:
        tag (int): The tag of the constraint to be removed.

        Returns:
        None
        """
        """Remove a constraint by its tag"""
        mpConstraint.remove_constraint(tag)

    
    def __iter__(self):
        """
        Iterate over all constraints.

        This method allows the mpConstraintManager to be iterable, yielding each
        constraint stored in the class variable `_constraints` of `mpConstraint`.

        Yields:
            mpConstraint: Each constraint object in the order of their tags.
        """
        return iter(mpConstraint._constraints.values())




    def to_tcl(self) -> str:
        """
        Convert all constraints to TCL commands.

        This method iterates over all constraints stored in the class variable
        `_constraints` of `mpConstraint` and converts each constraint to its
        corresponding TCL command string. The resulting TCL command strings are
        concatenated into a single string.

        Returns:
            str: A string containing all the TCL commands for the constraints.
        """
        """Convert all constraints to TCL commands"""
        tcl_str = ""
        for constraint in mpConstraint._constraints.values():
            tcl_str += constraint.to_tcl()
        return tcl_str