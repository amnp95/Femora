from typing import List, Optional, Dict, Any
import numpy as np
import pyvista as pv
import logging
import sys
from scipy.spatial import KDTree

from femora.components.Mesh.meshPartBase import MeshPart
from femora.core.element_base import Element
from femora.components.Material.materialBase import Material
from femora.components.event.event_bus import EventBus, FemoraEvent
from femora.utils.progress import Progress
from femora.constants import FEMORA_MAX_NDF


class Assembler:
    """Manages multiple `AssemblySection` instances and combines them into a unified mesh.

    This class implements the Singleton pattern, ensuring only one `Assembler` instance
    exists throughout the program. It provides methods for creating, managing, and
    assembling mesh sections into a complete structural model, handling unique tag
    management and mesh consolidation.

    Attributes:
        _instance (Assembler): The singleton instance of the Assembler.
        _assembly_sections (Dict[int, AssemblySection]): A dictionary mapping unique
            integer tags to `AssemblySection` instances.
        AssembeledMesh (pv.UnstructuredGrid): The final assembled PyVista
            UnstructuredGrid, or None if not yet assembled.
        AssembeledActor (pv.Actor): The PyVista actor for visualizing the assembled mesh,
            or None if not yet created.

    Example:
        >>> import femora as fm
        >>> from femora.components.Mesh.meshPartBase import MeshPart
        >>> from femora.core.element_base import Element
        >>> from femora.components.Material.materialBase import Material
        >>> from femora.components.Region.regionBase import Region
        >>> from femora.components.Section.sectionBase import Section
        >>> # Create dummy components for a simple example
        >>> class DummyElement(Element):
        ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
        ...         super().__init__(tag, nodes, material_tag, section_tag)
        ...         self._ndof = 3
        ...     def get_ndof(self): return self._ndof
        >>> class DummyMaterial(Material):
        ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
        >>> class DummySection(Section):
        ...     def __init__(self, tag, area): super().__init__(tag, area)
        >>> material = DummyMaterial(1, 200e9, 0.3)
        >>> section = DummySection(1, 1.0)
        >>> element = DummyElement(1, [1,2], material.tag, section.tag)
        >>> region = Region(1, "test_region")
        >>>
        >>> # Create dummy meshes using pyvista
        >>> mesh1 = pv.Cube().extract_all_edges()
        >>> mesh2 = pv.Sphere().extract_all_edges()
        >>>
        >>> # Register MeshParts (required by AssemblySection)
        >>> _ = MeshPart(mesh=mesh1, name="part1", element=element, material=material, region=region)
        >>> _ = MeshPart(mesh=mesh2, name="part2", element=element, material=material, region=region)
        >>>
        >>> assembler = fm.Assembler.get_instance()
        >>> section1 = assembler.create_section(meshparts=["part1"])
        >>> section2 = assembler.create_section(meshparts=["part2"])
        >>> assembler.Assemble(merge_points=True)
        >>> print(assembler.get_num_points()) # doctest: +SKIP
        106 # Example output varies based on internal mesh representation
        >>> print(assembler.get_num_cells()) # doctest: +SKIP
        192 # Example output varies
        >>> # assembler.plot() # doctest: +SKIP
    """
    _instance = None
    _assembly_sections: Dict[int, 'AssemblySection'] = {}
    AssembeledMesh = None
    AssembeledActor = None

    def __new__(cls):
        """Implements the singleton pattern for the `Assembler` class.

        Ensures that only a single instance of `Assembler` is created throughout
        the program's lifecycle. If an instance already exists, it returns the
        existing instance instead of creating a new one.

        Returns:
            Assembler: The singleton `Assembler` instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'Assembler':
        """Retrieves the single `Assembler` instance.

        This class method provides an alternative way to access the singleton
        instance, creating it if it doesn't already exist.

        Returns:
            Assembler: The singleton `Assembler` instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_section(
        self,
        meshparts: List[str],
        num_partitions: int = 1,
        partition_algorithm: str = "kd-tree",
        merging_points: bool = True,
        mass_merging: str = "sum",
        tolerance: float = 1e-5,
        **kwargs: Any
    ) -> 'AssemblySection':
        """Creates an `AssemblySection` and registers it with the `Assembler`.

        This method instantiates a new `AssemblySection` using the specified mesh parts
        and configuration. It automatically assigns a unique tag to the section and
        adds it to the Assembler's internal registry.

        Args:
            meshparts: A list of mesh part names to be assembled. These names
                must correspond to previously created `MeshPart` instances.
            num_partitions: The number of partitions for parallel processing.
                For the "kd-tree" algorithm, this value will be rounded up to the
                next power of 2 if not already one. Defaults to 1 (no partitioning).
            partition_algorithm: The algorithm to use for partitioning the mesh.
                Currently, only "kd-tree" is supported. Defaults to "kd-tree".
            merging_points: If True, points within a specified `tolerance` distance
                will be merged when combining mesh parts. Defaults to True.
            mass_merging: The method for merging mass properties of points if
                `merging_points` is True. Options are "sum" (masses are summed)
                or "average" (masses are averaged). Defaults to "sum".
            tolerance: The distance tolerance for merging points. Points closer
                than this value will be considered the same. Defaults to 1e-5.
            **kwargs: Additional keyword arguments to pass directly to the
                `AssemblySection` constructor.

        Returns:
            AssemblySection: The newly created and registered assembly section.

        Raises:
            ValueError: If any of the specified mesh parts do not exist, if the
                `partition_algorithm` is invalid, or if `mass_merging` is invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>>
            >>> # Create dummy PyVista meshes
            >>> mesh1 = pv.Cube()
            >>> mesh2 = pv.Sphere()
            >>>
            >>> # Register MeshParts
            >>> _ = MeshPart(mesh=mesh1, name="single_cube", element=element, material=material, region=region)
            >>> _ = MeshPart(mesh=mesh2, name="single_sphere", element=element, material=material, region=region)
            >>>
            >>> assembler = fm.Assembler.get_instance()
            >>> section = assembler.create_section(meshparts=["single_cube", "single_sphere"], num_partitions=2)
            >>> print(section.tag) # doctest: +SKIP
            1
            >>> print(section.num_partitions)
            2
        """
        # Create the AssemblySection
        assembly_section = AssemblySection(
            meshparts=meshparts,
            num_partitions=num_partitions,
            partition_algorithm=partition_algorithm,
            merging_points=merging_points,
            mass_merging=mass_merging,
            tolerance=tolerance,
            **kwargs
        )

        return assembly_section

    def delete_section(self, tag: int) -> None:
        """Deletes an `AssemblySection` by its tag.

        Removes the specified assembly section from the internal registry and
        updates the tags of remaining sections to maintain sequential numbering.

        Args:
            tag: The unique integer tag of the assembly section to delete.

        Raises:
            KeyError: If no assembly section with the given tag exists.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="part_to_delete", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> section = assembler.create_section(meshparts=["part_to_delete"])
            >>> initial_tag = section.tag
            >>> len(assembler.list_assembly_sections())
            1
            >>> assembler.delete_section(initial_tag)
            >>> len(assembler.list_assembly_sections())
            0
        """
        # Retrieve the section to ensure it exists
        section = self.get_assembly_section(tag)

        # Remove the section from the internal dictionary
        del self._assembly_sections[tag]

        # Retag remaining sections
        self._retag_sections()

    def _add_assembly_section(self, assembly_section: 'AssemblySection') -> int:
        """Internally adds an `AssemblySection` to the `Assembler`'s tracked sections.

        This method is primarily called by the `AssemblySection` constructor to
        register itself with the `Assembler`. It assigns a unique, sequential tag
        to the section and adds it to the internal registry.

        Args:
            assembly_section: The `AssemblySection` instance to add.

        Returns:
            int: The unique integer tag assigned to the added assembly section.
        """
        # Find the first available tag starting from 1
        tag = 1
        while tag in self._assembly_sections:
            tag += 1

        # Store the assembly section with its tag
        self._assembly_sections[tag] = assembly_section

        return tag

    def _remove_assembly_section(self, tag: int) -> None:
        """Removes an `AssemblySection` by its tag and retags remaining sections.

        This internal method is used to delete a section from the registry and
        updates the tags of remaining sections to maintain sequential numbering
        from 1.

        Args:
            tag: The unique integer tag of the assembly section to remove.

        Raises:
            KeyError: If no assembly section with the given tag exists.
        """
        if tag not in self._assembly_sections:
            raise KeyError(f"No assembly section with tag {tag} exists")

        # Remove the specified tag
        del self._assembly_sections[tag]

        # Retag all remaining sections to ensure continuous numbering
        self._retag_sections()

    def _retag_sections(self):
        """Retags all assembly sections to ensure continuous numbering from 1.

        This internal method is invoked after an `AssemblySection` is removed
        to ensure that the remaining sections have sequential tags starting
        from 1. It creates a new dictionary with updated tags and updates
        each section's internal tag.
        """
        # Sort sections by their current tags
        sorted_sections = sorted(self._assembly_sections.items(), key=lambda x: x[0])

        # Create a new dictionary with retagged sections
        new_assembly_sections = {}
        for new_tag, (_, section) in enumerate(sorted_sections, 1):
            new_assembly_sections[new_tag] = section
            section._tag = new_tag  # Update the section's tag

        # Replace the old dictionary with the new one
        self._assembly_sections = new_assembly_sections

    def get_assembly_section(self, tag: int) -> 'AssemblySection':
        """Retrieves an `AssemblySection` by its tag.

        Gets a specific assembly section from the internal registry using its unique
        integer tag.

        Args:
            tag: The unique integer tag of the assembly section to retrieve.

        Returns:
            AssemblySection: The requested assembly section.

        Raises:
            KeyError: If no assembly section with the given tag exists.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="part_a", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> section_a = assembler.create_section(meshparts=["part_a"])
            >>> retrieved_section = assembler.get_assembly_section(section_a.tag)
            >>> print(retrieved_section is section_a)
            True
        """
        return self._assembly_sections[tag]

    def list_assembly_sections(self) -> List[int]:
        """Lists all tags of registered `AssemblySection` instances.

        Returns a list of all integer tags that can be used to retrieve assembly
        sections from the `Assembler`. The tags are sorted in ascending order.

        Returns:
            List[int]: A list of tags for all added assembly sections.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> mesh2 = pv.Sphere()
            >>> _ = MeshPart(mesh=mesh1, name="list_part1", element=element, material=material, region=region)
            >>> _ = MeshPart(mesh=mesh2, name="list_part2", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections for consistent example
            >>> _ = assembler.create_section(meshparts=["list_part1"])
            >>> _ = assembler.create_section(meshparts=["list_part2"])
            >>> print(assembler.list_assembly_sections())
            [1, 2]
        """
        return sorted(list(self._assembly_sections.keys()))

    def clear_assembly_sections(self) -> None:
        """Clears all tracked `AssemblySection` instances.

        Removes all assembly sections from the internal registry, effectively
        resetting the `Assembler`'s state regarding tracked sections. This
        action does not affect the assembled mesh if one has already been
        created, nor does it delete the `MeshPart` instances themselves.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="clear_part1", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> _ = assembler.create_section(meshparts=["clear_part1"])
            >>> len(assembler.list_assembly_sections())
            1
            >>> assembler.clear_assembly_sections()
            >>> len(assembler.list_assembly_sections())
            0
        """
        self._assembly_sections.clear()

    def get_sections(self) -> Dict[int, 'AssemblySection']:
        """Retrieves all registered `AssemblySection` instances.

        Returns a shallow copy of the internal dictionary containing all assembly
        sections, keyed by their unique integer tags. This allows access to the
        sections without directly modifying the Assembler's internal state.

        Returns:
            Dict[int, AssemblySection]: A dictionary of all assembly sections,
                keyed by their tags.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="get_sections_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> section_obj = assembler.create_section(meshparts=["get_sections_part"])
            >>> all_sections = assembler.get_sections()
            >>> len(all_sections)
            1
            >>> print(all_sections[section_obj.tag] is section_obj)
            True
        """
        return self._assembly_sections.copy()

    def get_section(self, tag: int) -> 'AssemblySection':
        """Retrieves an `AssemblySection` by its tag.

        This method is an alias for `get_assembly_section` and is provided
        for backward compatibility.

        Args:
            tag: The unique integer tag of the assembly section to retrieve.

        Returns:
            AssemblySection: The requested assembly section.

        Raises:
            KeyError: If no assembly section with the given tag exists.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="get_section_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> section_obj = assembler.create_section(meshparts=["get_section_part"])
            >>> retrieved_section = assembler.get_section(section_obj.tag)
            >>> print(retrieved_section is section_obj)
            True
        """
        return self._assembly_sections[tag]

    @staticmethod
    def _snap_points(points: np.ndarray, tol: float = 1e-5) -> np.ndarray:
        """Snaps points within a given tolerance to a representative point using KDTree.

        This static method is used internally to clean up point clouds by
        identifying clusters of points that are very close to each other (within
        `tol` distance) and replacing them with a single representative point
        (the first point in the cluster).

        Args:
            points: A NumPy array of shape (N, D) representing N points in D dimensions.
            tol: The tolerance distance. Points within this distance from each
                other will be snapped to the same coordinate. Defaults to 1e-5.

        Returns:
            np.ndarray: A new NumPy array with the same shape as `points`, where
                clustered points have been snapped to their representative.
        """
        tree = KDTree(points)
        groups = tree.query_ball_tree(tree, tol)

        visited = np.zeros(len(points), dtype=bool)
        snapped = points.copy()

        for i in range(len(points)):
            if visited[i]:
                continue
            cluster = groups[i]
            rep = points[i]  # pick the first point
            for j in cluster:
                snapped[j] = rep
                visited[j] = True

        return snapped

    def get_num_cells(self) -> int:
        """Returns the total number of cells in the assembled mesh.

        Returns:
            int: The total number of cells if an assembled mesh exists,
                otherwise -1.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="num_cells_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> section_obj = assembler.create_section(meshparts=["num_cells_part"])
            >>> assembler.Assemble()
            >>> print(assembler.get_num_cells()) # doctest: +SKIP
            6
        """
        if self.AssembeledMesh is None:
            return -1
        return self.AssembeledMesh.n_cells

    def get_num_points(self) -> int:
        """Returns the total number of points in the assembled mesh.

        Returns:
            int: The total number of points if an assembled mesh exists,
                otherwise -1.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="num_points_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> section_obj = assembler.create_section(meshparts=["num_points_part"])
            >>> assembler.Assemble()
            >>> print(assembler.get_num_points()) # doctest: +SKIP
            8
        """
        if self.AssembeledMesh is None:
            return -1
        return self.AssembeledMesh.n_points

    def Assemble(self,
                 merge_points: bool = True,
                 mass_merging: str = "sum",
                 tolerance: float = 1e-5,
                 *,
                 progress_callback=None) -> None:
        """Assembles all registered `AssemblySection` instances into a single unified mesh.

        This method combines all `AssemblySection` objects tracked by the `Assembler`
        into a single PyVista UnstructuredGrid. It meticulously preserves and
        consolidates important mesh data such as element tags, material tags,
        region information, and partitioning details.

        Args:
            merge_points: If True, points within a small `tolerance` distance will
                be combined, creating a continuous mesh where connected. If False,
                all points from original meshes are preserved. Defaults to True.
            mass_merging: The method for merging mass properties of points if
                `merge_points` is True. Options are "sum" (masses are summed)
                or "average" (masses are averaged). Defaults to "sum".
            tolerance: The distance tolerance for merging points when `merge_points`
                is True. Points closer than this value will be snapped. Defaults to 1e-5.
            progress_callback: An optional callback function to report assembly progress.
                It should accept a float (0.0 to 100.0) for progress and an optional
                string for a message.

        Raises:
            ValueError: If no `AssemblySection` instances have been created or if
                the first `AssemblySection` does not contain a mesh.
            Exception: If any error occurs during the assembly process.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>>
            >>> # Create dummy meshes
            >>> mesh1 = pv.Cube()
            >>> mesh2 = pv.Sphere()
            >>>
            >>> # Register MeshParts
            >>> _ = MeshPart(mesh=mesh1, name="assemble_cube", element=element, material=material, region=region)
            >>> _ = MeshPart(mesh=mesh2, name="assemble_sphere", element=element, material=material, region=region)
            >>>
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> section_cube = assembler.create_section(meshparts=["assemble_cube"])
            >>> section_sphere = assembler.create_section(meshparts=["assemble_sphere"])
            >>>
            >>> assembler.Assemble(merge_points=True)
            >>> print(assembler.AssembeledMesh.n_points) # doctest: +SKIP
            338 # Example output will vary
            >>> print(assembler.AssembeledMesh.n_cells) # doctest: +SKIP
            242 # Example output will vary
        """

        if self.AssembeledMesh is not None:
            del self.AssembeledMesh
            self.AssembeledMesh = None

        if not self._assembly_sections:
            raise ValueError("No assembly sections have been created")

        # Progress setup
        if progress_callback is None:
            progress_callback = lambda v, msg="": Progress.callback(v, msg, desc="Assembling")

        progress_callback(0, "initialising")

        # Notify subscribers that assembly is starting
        EventBus.emit(FemoraEvent.PRE_ASSEMBLE)

        sorted_sections = sorted(self._assembly_sections.items(), key=lambda x: x[0])

        first_mesh = sorted_sections[0][1].mesh
        # assert first_mesh is not None, "AssemblySection mesh is None"
        if first_mesh is None:
            raise ValueError("There is no mesh to assemble. Please create an AssemblySection first.")

        self.AssembeledMesh = pv.MultiBlock()
        self.AssembeledMesh.append(first_mesh.copy())
        progress_callback(1 / len(sorted_sections) * 70, f"merged section 1/{len(sorted_sections)}")
        num_partitions = sorted_sections[0][1].num_partitions

        try:
            for idx, (tag, section) in enumerate(sorted_sections[1:], start=2):
                second_mesh = section.mesh.copy()  # type: ignore[attr-defined]
                second_mesh.cell_data["Core"] = second_mesh.cell_data["Core"] + num_partitions
                num_partitions = num_partitions + section.num_partitions
                self.AssembeledMesh.append(second_mesh)
                perc = idx / len(sorted_sections) * 70
                progress_callback(perc, f"merged section {idx}/{len(sorted_sections)}")
            self.AssembeledMesh = self.AssembeledMesh.combine(
                merge_points=False,
                tolerance=1e-5,
            )
            if merge_points:
                number_of_points_before_cleaning = self.AssembeledMesh.n_points

                # snap points within tolerance
                self.AssembeledMesh.points = self._snap_points(self.AssembeledMesh.points, tolerance)

                mass = self.AssembeledMesh.point_data["Mass"]
                self.AssembeledMesh = self.AssembeledMesh.clean(
                    tolerance=1e-5,
                    remove_unused_points=False,
                    produce_merge_map=True,
                    average_point_data=True,
                    merging_array_name="ndf",
                    progress_bar=False,
                )
                # make the ndf array uint16
                self.AssembeledMesh.point_data["ndf"] = self.AssembeledMesh.point_data["ndf"].astype(np.uint16)
                # make the MeshPartTag_pointdata array uint16
                self.AssembeledMesh.point_data["MeshPartTag_pointdata"] = self.AssembeledMesh.point_data["MeshPartTag_pointdata"].astype(np.uint16)

                if mass_merging == "sum":
                    if number_of_points_before_cleaning != number_of_points_after_cleaning:
                        Mass = np.zeros((number_of_points_after_cleaning, FEMORA_MAX_NDF), dtype=np.float32)
                        for i in range(self.AssembeledMesh.field_data["PointMergeMap"].shape[0]):
                            Mass[self.AssembeledMesh.field_data["PointMergeMap"][i], :] += mass[i, :]

                        self.AssembeledMesh.point_data["Mass"] = Mass

                del self.AssembeledMesh.field_data["PointMergeMap"]


        except Exception as e:
            raise e

        # Notify any subscribers that the mesh has been assembled and partitioned
        progress_callback(70, "post-assemble")
        EventBus.emit(FemoraEvent.POST_ASSEMBLE, assembled_mesh=self.AssembeledMesh)
        progress_callback(90, "resolving core conflicts")
        EventBus.emit(FemoraEvent.RESOLVE_CORE_CONFLICTS, assembled_mesh=self.AssembeledMesh)

        progress_callback(100, "done")
        # Announce the number of cores used for assembly
        self._announce_required_cores()

    def delete_assembled_mesh(self) -> None:
        """Deletes the assembled mesh.

        Releases memory by deleting the `AssembeledMesh` attribute, if it exists.
        This is useful for clearing resources or preparing for a new assembly
        operation without affecting the registered `AssemblySection` instances.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="delete_mesh_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> _ = assembler.create_section(meshparts=["delete_mesh_part"])
            >>> assembler.Assemble()
            >>> print(assembler.AssembeledMesh is not None)
            True
            >>> assembler.delete_assembled_mesh()
            >>> print(assembler.AssembeledMesh is None)
            True
        """
        if self.AssembeledMesh is not None:
            del self.AssembeledMesh
            self.AssembeledMesh = None

    def plot(
        self,
        color=None,
        style=None,
        scalars=None,
        clim=None,
        show_edges=None,
        edge_color=None,
        point_size=None,
        line_width=None,
        opacity=None,
        flip_scalars=False,
        lighting=None,
        n_colors=256,
        interpolate_before_map=None,
        cmap=None,
        label=None,
        reset_camera=None,
        scalar_bar_args=None,
        show_scalar_bar=None,
        multi_colors=False,
        name=None,
        texture=None,
        render_points_as_spheres=None,
        render_lines_as_tubes=None,
        smooth_shading=None,
        split_sharp_edges=None,
        ambient=None,
        diffuse=None,
        specular=None,
        specular_power=None,
        nan_color=None,
        nan_opacity=1.0,
        culling=None,
        rgb=None,
        categories=False,
        silhouette=None,
        use_transparency=False,
        below_color=None,
        above_color=None,
        annotations=None,
        pickable=True,
        preference='point',
        log_scale=False,
        pbr=None,
        metallic=None,
        roughness=None,
        render=True,
        user_matrix=None,
        component=None,
        emissive=None,
        copy_mesh=False,
        backface_params=None,
        show_vertices=None,
        edge_opacity=None,
        add_axes=True,
        add_bounding_box=False,
        show_grid=False,
        explode=False,
        explode_factor=0.1,
        sperate_beams_solid=False,
        opacity_beams=1.,
        opacity_solids=.5,
        tube_radius=0.05,
        show_cells_by_type=False,
        cells_to_show: Optional[List[int]] = None,
        **kwargs
    ) -> None:
        """Plots the assembled mesh using PyVista.

        This method visualizes the `AssembeledMesh` attribute of the `Assembler`
        instance. It leverages PyVista's extensive plotting capabilities,
        allowing for detailed customization through a wide range of keyword
        arguments directly passed to `pyvista.Plotter.add_mesh`.

        Args:
            color: The solid color for the mesh. Can be a string name, RGB list,
                or hex color string.
            style: The visualization style for the mesh: 'surface', 'wireframe',
                'points', or 'points_gaussian'.
            scalars: Data to use for coloring the mesh. Can be a string name of
                a point/cell data array or a NumPy array.
            clim: A two-item sequence specifying the color bar range for `scalars`.
                For example: `[-1, 2]`.
            show_edges: If True, mesh edges are displayed. This option is not
                applicable for 'wireframe' style.
            edge_color: The color for edges when `show_edges` is True.
            point_size: The size of points when `style` is 'points' or
                'points_gaussian'. Defaults to 5.0.
            line_width: The thickness of lines for 'wireframe' or 'surface' styles.
            opacity: The opacity of the mesh. Can be a float (0.0 to 1.0), a string
                specifying a transfer function, or an array-like object.
            flip_scalars: If True, the direction of the colormap will be flipped.
            lighting: If True, enables view-direction-dependent lighting.
            n_colors: The number of colors to use for scalar mapping. Defaults to 256.
            interpolate_before_map: If True, scalar data is interpolated before
                mapping to colors, resulting in a smoother display. Defaults to True.
            cmap: The colormap to use for `scalars`. Can be a string name, a list
                of colors, or a `pyvista.LookupTable` object.
            label: A string label for the mesh/actor, used in legends.
            reset_camera: If True, the camera position will be reset to fit the
                mesh after adding it to the plotter.
            scalar_bar_args: A dictionary of keyword arguments to customize the
                scalar bar appearance.
            show_scalar_bar: If True, displays a scalar bar for `scalars`.
            multi_colors: If True (or other accepted values), colors each block
                of a `MultiBlock` dataset with a solid color.
            name: A string name for the mesh/actor, useful for updating or retrieving
                it from the plotter later.
            texture: A `pyvista.Texture` object or a NumPy array representing an
                image to apply as a texture, provided the mesh has texture coordinates.
            render_points_as_spheres: If True, points are rendered as spheres.
            render_lines_as_tubes: If True, lines are rendered as tubes.
            smooth_shading: If True, enables smooth shading using the Phong
                lighting algorithm.
            split_sharp_edges: If True, sharp edges (angles > 30 degrees) are split
                before applying smooth shading, preventing artifacts.
            ambient: The ambient lighting coefficient (0.0 to 1.0).
            diffuse: The diffuse lighting coefficient. Defaults to 1.0.
            specular: The specular lighting coefficient. Defaults to 0.0.
            specular_power: The specular power (0.0 to 128.0).
            nan_color: The color to use for NaN values in scalars.
            nan_opacity: The opacity for NaN values (0.0 to 1.0). Defaults to 1.0.
            culling: Specifies face culling: 'front' (cull front faces) or
                'back' (cull back faces).
            rgb: If True, interprets `scalars` as RGB(A) color values.
            categories: If True, uses unique values in `scalars` as discrete
                categories for coloring.
            silhouette: A dictionary of properties or True to plot a silhouette
                highlight around the mesh.
            use_transparency: If True, inverts opacity mapping to transparency.
            below_color: The color for scalar values below the `clim` range.
            above_color: The color for scalar values above the `clim` range.
            annotations: A dictionary for custom annotations on the scalar bar.
            pickable: If True, the actor can be picked by mouse interactions.
            preference: Scalar mapping preference: 'point' or 'cell'.
            log_scale: If True, uses a logarithmic scale for color mapping.
            pbr: If True, enables physics-based rendering (PBR).
            metallic: The metallic value for PBR (0.0 to 1.0).
            roughness: The roughness value for PBR (0.0 to 1.0).
            render: If True, forces a render after adding the mesh. Defaults to True.
            user_matrix: A NumPy array or `vtkMatrix4x4` for transformation.
            component: An integer index to plot a specific component of
                vector-valued scalars.
            emissive: If True, treats points as emissive light sources (for
                'points_gaussian' style).
            copy_mesh: If True, a copy of the mesh is made before adding it to
                the plotter. Defaults to False.
            backface_params: A dictionary or `pyvista.Property` object for
                backface rendering parameters.
            show_vertices: If True, renders external surface vertices.
            edge_opacity: The opacity for edges (0.0 to 1.0).
            add_axes: If True, adds axes to the plot. Defaults to True.
            add_bounding_box: If True, adds a bounding box around the mesh. Defaults to False.
            show_grid: If True, displays a grid on the plot. Defaults to False.
            explode: If True, individual blocks of a `MultiBlock` mesh will be
                exploded apart for visualization.
            explode_factor: The factor by which to explode blocks if `explode` is True.
            sperate_beams_solid: If True, beams (lines/polylines) and solids
                (tets, hexes, quads, etc.) are rendered separately with distinct
                opacities.
            opacity_beams: Opacity for beam elements when `sperate_beams_solid` is True.
            opacity_solids: Opacity for solid elements when `sperate_beams_solid` is True.
            tube_radius: Radius for rendering beams as tubes when
                `sperate_beams_solid` is True.
            show_cells_by_type: If True, only cells of specified types in `cells_to_show`
                will be rendered.
            cells_to_show: A list of PyVista `CellType` integers indicating which
                cell types to display when `show_cells_by_type` is True.
            **kwargs: Additional keyword arguments that will be passed directly
                to `pyvista.Plotter.add_mesh`.

        Raises:
            ValueError: If no assembled mesh exists to plot or if `show_cells_by_type`
                is True but `cells_to_show` is None.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>>
            >>> # Create dummy mesh
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="plot_part", element=element, material=material, region=region)
            >>>
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> _ = assembler.create_section(meshparts=["plot_part"])
            >>> assembler.Assemble()
            >>> # assembler.plot(color='red', show_edges=True) # doctest: +SKIP
            >>> # Example of plotting with scalars (assuming 'Core' data exists after assembly)
            >>> # assembler.plot(scalars='Core', cmap='viridis', show_scalar_bar=True) # doctest: +SKIP
        """
        if self.AssembeledMesh is None:
            raise ValueError("No assembled mesh exists to plot")

        # remove the options that are not part of pyvista
        options = locals().copy()
        del options["self"]
        del options["show_cells_by_type"]
        del options["cells_to_show"]
        del options["tube_radius"]
        del options["kwargs"]
        del options["opacity_solids"]
        del options["opacity_beams"]
        del options["sperate_beams_solid"]
        del options["explode"]
        del options["explode_factor"]
        del options["add_axes"]
        del options["add_bounding_box"]
        del options["show_grid"]

        if show_cells_by_type:
            if cells_to_show is None:
                raise ValueError("cells_to_show must be provided when show_cells_by_type is True")
            mesh = self.AssembeledMesh.copy()
            mesh = pv.UnstructuredGrid(mesh)
            mesh = mesh.extract_cells_by_type(cells_to_show)
            pl = pv.Plotter()
            pl.add_mesh(mesh, **options)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            return

        # create a dict from all the inputs
        if sperate_beams_solid:
            mesh = self.AssembeledMesh.copy()
            mesh = pv.UnstructuredGrid(mesh)
            beams = mesh.extract_cells_by_type([pv.CellType.LINE, pv.CellType.POLY_LINE])
            mesh_solids = mesh.extract_cells_by_type([pv.CellType.TETRA,
                                                      pv.CellType.HEXAHEDRON,
                                                      pv.CellType.QUAD,
                                                      pv.CellType.WEDGE,
                                                      pv.CellType.TRIANGLE,
                                                      pv.CellType.VOXEL,
                                                      pv.CellType.PIXEL])

            pl = pv.Plotter()
            del options["opacity"]
            if beams.n_cells > 0:
                op = options.copy()
                op["show_edges"] = False
                op["line_width"] = tube_radius
                pl.add_mesh(beams, **op, opacity=opacity_beams,)
                del op
            if mesh_solids.n_cells > 0:
                options["render_lines_as_tubes"] = False
                pl.add_mesh(mesh_solids, **options, opacity=opacity_solids)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            return

        if scalars == "Core":
            scalars = None
            Mesh = self.AssembeledMesh.copy()

            if explode:
                Mesh = Mesh.explode(factor=explode_factor)

            cores = Mesh.cell_data["Core"]
            mesh = pv.MultiBlock()
            for core in np.unique(cores):
                core_mesh = Mesh.extract_cells(cores == core)
                mesh.append(core_mesh)

            pl = pv.Plotter()
            pl.add_mesh(mesh,
                color=color,
                style=style,
                scalars=scalars,
                clim=clim,
                show_edges=show_edges,
                edge_color=edge_color,
                point_size=point_size,
                line_width=line_width,
                opacity=opacity,
                flip_scalars=flip_scalars,
                lighting=lighting,
                n_colors=n_colors,
                interpolate_before_map=interpolate_before_map,
                cmap=cmap,
                label=label,
                reset_camera=reset_camera,
                scalar_bar_args=scalar_bar_args,
                show_scalar_bar=show_scalar_bar,
                multi_colors=True,
                name=name,
                texture=texture,
                render_points_as_spheres=render_points_as_spheres,
                render_lines_as_tubes=render_lines_as_tubes,
                smooth_shading=smooth_shading,
                split_sharp_edges=split_sharp_edges,
                ambient=ambient,
                diffuse=diffuse,
                specular=specular,
                specular_power=specular_power,
                nan_color=nan_color,
                nan_opacity=nan_opacity,
                culling=culling,
                rgb=rgb,
                categories=categories,
                silhouette=silhouette,
                use_transparency=use_transparency,
                below_color=below_color,
                above_color=above_color,
                annotations=annotations,
                pickable=pickable,
                preference=preference,
                log_scale=log_scale,
                pbr=pbr,
                metallic=metallic,
                roughness=roughness,
                render=render,
                user_matrix=user_matrix,
                component=component,
                emissive=emissive,
                copy_mesh=copy_mesh,
                backface_params=backface_params,
                show_vertices=show_vertices,
                edge_opacity=edge_opacity,
                **kwargs)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            pl.close()

        else:
            pl = pv.Plotter()
            mesh = self.AssembeledMesh.copy()
            if explode:
                mesh = mesh.explode(factor=explode_factor)

            pl.add_mesh(
                mesh,
                color=color,
                style=style,
                scalars=scalars,
                clim=clim,
                show_edges=show_edges,
                edge_color=edge_color,
                point_size=point_size,
                line_width=line_width,
                opacity=opacity,
                flip_scalars=flip_scalars,
                lighting=lighting,
                n_colors=n_colors,
                interpolate_before_map=interpolate_before_map,
                cmap=cmap,
                label=label,
                reset_camera=reset_camera,
                scalar_bar_args=scalar_bar_args,
                show_scalar_bar=show_scalar_bar,
                multi_colors=multi_colors,
                name=name,
                texture=texture,
                render_points_as_spheres=render_points_as_spheres,
                render_lines_as_tubes=render_lines_as_tubes,
                smooth_shading=smooth_shading,
                split_sharp_edges=split_sharp_edges,
                ambient=ambient,
                diffuse=diffuse,
                specular=specular,
                specular_power=specular_power,
                nan_color=nan_color,
                nan_opacity=nan_opacity,
                culling=culling,
                rgb=rgb,
                categories=categories,
                silhouette=silhouette,
                use_transparency=use_transparency,
                below_color=below_color,
                above_color=above_color,
                annotations=annotations,
                pickable=pickable,
                preference=preference,
                log_scale=log_scale,
                pbr=pbr,
                metallic=metallic,
                roughness=roughness,
                render=render,
                user_matrix=user_matrix,
                component=component,
                emissive=emissive,
                copy_mesh=copy_mesh,
                backface_params=backface_params,
                show_vertices=show_vertices,
                edge_opacity=edge_opacity,
                **kwargs
            )
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            pl.close()

    def get_mesh(self) -> Optional[pv.UnstructuredGrid]:
        """Retrieves a copy of the assembled mesh.

        Returns the currently assembled mesh as a PyVista UnstructuredGrid.
        If no mesh has been assembled yet, this method returns None.
        A copy is returned to prevent direct modification of the internal mesh state.

        Returns:
            Optional[pv.UnstructuredGrid]: A copy of the assembled mesh,
                or None if no mesh has been created yet.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="get_mesh_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> _ = assembler.create_section(meshparts=["get_mesh_part"])
            >>> assembler.Assemble()
            >>> mesh = assembler.get_mesh()
            >>> print(isinstance(mesh, pv.UnstructuredGrid))
            True
            >>> print(mesh.n_cells) # doctest: +SKIP
            6
        """
        return self.AssembeledMesh.copy()

    def _announce_required_cores(self):
        """Announces the number of CPU cores identified in the assembled mesh.

        This internal method configures logging and prints an important notice
        to `sys.stdout` indicating the number of unique "Core" partitions found
        in the `AssembeledMesh`. This informs the user about the computational
        resources potentially required to run simulations effectively on the model.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        # this part should be gou through the Assembled Mesh and see how many cores are used to print
        # the number of cores used in the assembly
        if self.AssembeledMesh is None:
            logging.warning("No assembled mesh found. Cannot announce required cores.")
            return
        cores = self.AssembeledMesh.cell_data["Core"]
        unique_cores = np.unique(cores)
        cores = len(unique_cores)
        RED = "\033[91m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        BLUE = "\033[94m"
        message = f"{BOLD}{BLUE}!!! IMPORTANT RESOURCE NOTICE !!!{RESET}\n" \
                f"{BOLD}This model requires {RED}{cores}{RESET}{BOLD} CPU cores to run effectively.{RESET}\n" \
                f"Please ensure your environment has sufficient resources.\n"

        border = "=" * 70
        full_message = f"\n{BLUE}{border}\n{message}{BLUE}{border}{RESET}\n"

        print(full_message)


class AssemblySection:
    """Represents a collection of mesh parts combined into a single mesh for analysis.

    The `AssemblySection` class takes a list of `MeshPart` names, validates them,
    and merges them into a single `pyvista.UnstructuredGrid`. It also handles
    the partitioning of this combined mesh, typically for parallel processing.
    Each instance of `AssemblySection` is automatically registered with the
    `Assembler` singleton and assigned a unique integer tag.

    This class manages:
    - Validation and merging of `MeshPart` objects.
    - Consistency of degrees of freedom (NDF) across merged parts.
    - Assignment of metadata (ElementTag, MaterialTag, Region, Core).
    - Optional partitioning of the assembled mesh.

    Attributes:
        meshparts_list (List[MeshPart]): A list of `MeshPart` objects included
            in this section.
        num_partitions (int): The number of partitions the assembled mesh is divided into.
        partition_algorithm (str): The algorithm used for partitioning (e.g., "kd-tree").
        merging_points (bool): True if points within `tolerance` are merged during assembly,
            False otherwise.
        mass_merging (str): The method used for merging mass properties ("sum" or "average").
        tolerance (float): The distance tolerance for merging points.
        mesh (Optional[pv.UnstructuredGrid]): The assembled and partitioned
            `pyvista.UnstructuredGrid`, or None if not yet assembled.
        elements (List[Element]): A list of `Element` objects referenced by the
            mesh parts in this section.
        materials (List[Material]): A list of `Material` objects referenced by
            the mesh parts in this section.
        actor (Any): A PyVista actor for visualization of this section's mesh.
        _tag (Optional[int]): The unique integer tag assigned by the `Assembler`,
            or None if not yet registered.

    Example:
        >>> import femora as fm
        >>> from femora.components.Mesh.meshPartBase import MeshPart
        >>> from femora.core.element_base import Element
        >>> from femora.components.Material.materialBase import Material
        >>> from femora.components.Region.regionBase import Region
        >>> from femora.components.Section.sectionBase import Section
        >>> # Setup dummy components
        >>> class DummyElement(Element):
        ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
        ...         super().__init__(tag, nodes, material_tag, section_tag)
        ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
        >>> class DummyMaterial(Material):
        ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
        >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
        >>> material = DummyMaterial(1, 200e9, 0.3)
        >>> section = DummySection(1, 1.0)
        >>> element = DummyElement(1, [1,2], material.tag, section.tag)
        >>> region = Region(1, "test_region")
        >>>
        >>> # Create dummy meshes
        >>> mesh1 = pv.Cube()
        >>> mesh2 = pv.Sphere()
        >>>
        >>> # Register MeshParts
        >>> _ = MeshPart(mesh=mesh1, name="partA", element=element, material=material, region=region)
        >>> _ = MeshPart(mesh=mesh2, name="partB", element=element, material=material, region=region)
        >>>
        >>> # Create an AssemblySection
        >>> section = fm.AssemblySection(meshparts=["partA", "partB"], num_partitions=2, merging_points=True)
        >>> print(section.tag) # doctest: +SKIP
        1
        >>> print(section.mesh.n_points) # doctest: +SKIP
        338 # Example output will vary
    """
    def __init__(
        self,
        meshparts: List[str],
        num_partitions: int = 1,
        partition_algorithm: str = "kd-tree",
        merging_points: bool = True,
        progress_callback=None,
        mass_merging: str = "sum",
        tolerance: float = 1e-5,
    ):
        """Initializes an `AssemblySection` by combining multiple mesh parts.

        This constructor takes a list of mesh part names, validates them,
        combines them into a single mesh, and optionally partitions the result.
        The assembled section is automatically registered with the `Assembler`
        singleton upon successful mesh assembly.

        If the `partition_algorithm` is "kd-tree" and `num_partitions` is not
        a power of 2, it will be automatically rounded up to the next power of 2
        to ensure compatibility with the algorithm's requirements.

        Args:
            meshparts: A list of mesh part names to be assembled. These names
                must correspond to previously created `MeshPart` instances
                registered in `MeshPart._mesh_parts`.
            num_partitions: The number of partitions for parallel processing.
                For the "kd-tree" algorithm, this will be rounded to the next
                power of 2 if not already one. Defaults to 1 (no partitioning).
            partition_algorithm: The algorithm used for partitioning the mesh.
                Currently, only "kd-tree" is supported. Defaults to "kd-tree".
            merging_points: If True, points that are within a `tolerance` distance
                of each other will be merged when assembling mesh parts.
                Defaults to True.
            progress_callback: An optional callback function to report assembly progress.
                It should accept a float (0.0 to 100.0) for progress and an optional
                string for a message.
            mass_merging: The method for merging mass properties of points if
                `merging_points` is True. Options are "sum" (masses are summed)
                or "average" (masses are averaged). Defaults to "sum".
            tolerance: The distance tolerance for merging points when
                `merging_points` is True. Defaults to 1e-5.

        Raises:
            ValueError: If no valid mesh parts are provided, if the `partition_algorithm`
                is invalid, if `mass_merging` is invalid, or if mesh assembly fails.
        """
        # Validate and collect mesh parts
        self.meshparts_list = self._validate_mesh_parts(meshparts)

        # Configuration parameters
        self.num_partitions = num_partitions
        self.partition_algorithm = partition_algorithm
        # check if the partition algorithm is valid
        if self.partition_algorithm not in ["kd-tree"]:
            raise ValueError(f"Invalid partition algorithm: {self.partition_algorithm}")

        if self.partition_algorithm == "kd-tree":
            # If a non-power of two value is specified for
            # n_partitions, then the load balancing simply
            # uses the power-of-two greater than the requested value
            if self.num_partitions & (self.num_partitions - 1) != 0:
                self.num_partitions = 2**self.num_partitions.bit_length()

        # Initialize tag to None
        self._tag = None
        self.merging_points = merging_points
        if mass_merging not in ["sum", "average"]:
            raise ValueError(f"Invalid mass merging method: {mass_merging}. Must be 'sum' or 'average'.")
        self.mass_merging = mass_merging

        # Assembled mesh attributes
        self.mesh: Optional[pv.UnstructuredGrid] = None
        self.elements: List[Element] = []
        self.materials: List[Material] = []
        self.tolerance = tolerance

        # Assemble the mesh first
        try:
            self._assemble_mesh(progress_callback=progress_callback)
            # Only add to Assembler if mesh assembly is successful
            self._tag = Assembler.get_instance()._add_assembly_section(self)
        except Exception as e:
            # If mesh assembly fails, raise the original exception
            raise

        self.actor = None

    @property
    def tag(self) -> int:
        """Retrieves the unique tag for this `AssemblySection`.

        The tag is an integer identifier assigned by the `Assembler` when
        the `AssemblySection` is successfully created and registered. It
        can be used to retrieve the section from the `Assembler` later.

        Returns:
            int: The unique integer tag assigned by the `Assembler`.

        Raises:
            ValueError: If the section has not been successfully added to the
                `Assembler` (i.e., `_tag` is None).

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="tag_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> assembly_section = assembler.create_section(meshparts=["tag_part"])
            >>> print(assembly_section.tag) # doctest: +SKIP
            1
        """
        if self._tag is None:
            raise ValueError("AssemblySection has not been successfully created")
        return self._tag

    def _validate_mesh_parts(self, meshpart_names: List[str]) -> List[MeshPart]:
        """Validates and retrieves `MeshPart` objects by their names.

        This internal method ensures that all specified mesh part names correspond
        to existing `MeshPart` instances registered in the global `MeshPart._mesh_parts`
        dictionary. It also verifies that at least one valid mesh part name is provided.

        Args:
            meshpart_names: A list of strings, where each string is the `user_name`
                of a `MeshPart` instance to be validated and retrieved.

        Returns:
            List[MeshPart]: A list of validated `MeshPart` objects corresponding
                to the input names.

        Raises:
            ValueError: If any specified mesh part name does not exist in the
                `MeshPart` registry or if the `meshpart_names` list is empty
                after validation.
        """
        validated_meshparts = []
        for name in meshpart_names:
            meshpart = MeshPart._mesh_parts.get(name)
            if meshpart is None:
                raise ValueError(f"Mesh with name '{name}' does not exist")
            validated_meshparts.append(meshpart)

        if not validated_meshparts:
            raise ValueError("No valid mesh parts were provided")

        return validated_meshparts

    @staticmethod
    def _snap_points(points: np.ndarray, tol: float = 1e-6) -> np.ndarray:
        """Snaps points within a given tolerance to a representative point using KDTree.

        This static method is used internally to clean up point clouds by
        identifying clusters of points that are very close to each other (within
        `tol` distance) and replacing them with a single representative point
        (the first point in the cluster).

        Args:
            points: A NumPy array of shape (N, D) representing N points in D dimensions.
            tol: The tolerance distance. Points within this distance from each
                other will be snapped to the same coordinate. Defaults to 1e-6.

        Returns:
            np.ndarray: A new NumPy array with the same shape as `points`, where
                clustered points have been snapped to their representative.
        """
        tree = KDTree(points)
        groups = tree.query_ball_tree(tree, tol)

        visited = np.zeros(len(points), dtype=bool)
        snapped = points.copy()

        for i in range(len(points)):
            if visited[i]:
                continue
            cluster = groups[i]
            rep = points[i]  # pick the first point
            for j in cluster:
                snapped[j] = rep
                visited[j] = True

        return snapped

    def _ensure_ndf_array(self, mesh: pv.UnstructuredGrid, default_ndf: int):
        """Ensures the mesh has an 'ndf' point data array.

        If the 'ndf' (Number of Degrees of Freedom) array is missing from the
        mesh's point data, this method creates it. It attempts to derive NDF
        values from the 'ElementTag' cell data to respect unique NDFs defined
        by different elements (e.g., for `GhostNodeElements`). If no 'ElementTag'
        is present, or if an element's NDF is not explicitly found, a
        `default_ndf` value is assigned to points.

        Args:
            mesh: The `pyvista.UnstructuredGrid` to check and modify.
            default_ndf: The default number of degrees of freedom to assign
                to points if no specific element NDF can be determined.
        """
        if "ndf" in mesh.point_data:
            return

        n_points = mesh.n_points

        # If no ElementTag, we must use the default for all points
        if "ElementTag" not in mesh.cell_data:
            if "ndf" not in mesh.point_data:
                mesh.point_data["ndf"] = np.full(n_points, default_ndf, dtype=np.uint16)
            return

        # Start with default
        ndf_values = np.full(n_points, default_ndf, dtype=np.uint16)
        element_tags = mesh.cell_data["ElementTag"]
        unique_tags = np.unique(element_tags)

        for tag in unique_tags:
            element = Element.get_element_by_tag(tag)
            if element:
                ele_ndof = element.get_ndof()
                if ele_ndof != default_ndf:
                    # Update points belonging to these cells
                    cell_indices = np.where(element_tags == tag)[0]
                    for cell_idx in cell_indices:
                        start = mesh.offset[cell_idx]
                        end = mesh.offset[cell_idx + 1]
                        pids = mesh.cell_connectivity[start:end]
                        ndf_values[pids] = ele_ndof

        mesh.point_data["ndf"] = ndf_values

    def _assemble_mesh(self, progress_callback=None):
        """Assembles mesh parts into a single `pyvista.UnstructuredGrid`.

        This internal method performs the actual combination of `MeshPart`
        objects into a unified `pyvista.UnstructuredGrid`. It manages:
        - Copying and preparing the first mesh part as the base.
        - Adding essential metadata (ElementTag, MaterialTag, Region, SectionTag,
          MeshPartTag_celldata, MeshPartTag_pointdata) to the mesh's cell and point data.
        - Ensuring the 'ndf' (Number of Degrees of Freedom) point data array exists.
        - Iteratively merging subsequent mesh parts with the base mesh.
        - Optionally performing point merging based on `self.merging_points` and
          `self.tolerance`, and handling `mass_merging`.
        - Partitioning the resulting mesh and assigning a "Core" (partition ID)
          to each cell if `self.num_partitions` is greater than 1.

        The final assembled mesh is stored in the `self.mesh` attribute.

        Args:
            progress_callback: An optional callback function to report assembly progress.
                It should accept a float (0.0 to 100.0) for progress and an optional
                string for a message.

        Raises:
            ValueError: If an error occurs during the mesh assembly process.
        """
        if progress_callback is None:
            def progress_callback(v, msg=""):
                Progress.callback(v, msg, desc=f"Assembly Section: {len(Assembler.get_instance()._assembly_sections) + 1}")

        # Start with the first mesh
        first_meshpart = self.meshparts_list[0]
        first_mesh = first_meshpart.mesh.copy()

        # Collect elements and materials
        ndf = 0
        if first_meshpart.element:
            ndf = first_meshpart.element._ndof
            matTag = first_meshpart.element.get_material_tag()
            EleTag = first_meshpart.element.tag
            sectionTag = first_meshpart.element.get_section_tag()
        elif hasattr(first_meshpart, 'ndof'):  # Handling CompositeMesh
            ndf = first_meshpart.ndof
            matTag = getattr(first_meshpart, 'material_tag', 0)
            EleTag = getattr(first_meshpart, 'element_tag', 0)
            sectionTag = getattr(first_meshpart, 'section_tag', 0)
        else:
            ndf = FEMORA_MAX_NDF  # Default fallback
            matTag = getattr(first_meshpart, 'material_tag', 0)
            EleTag = getattr(first_meshpart, 'element_tag', 0)
            sectionTag = getattr(first_meshpart, 'section_tag', 0)

        regionTag = first_meshpart.region.tag
        meshTag = first_meshpart.tag

        # Add initial metadata to the first mesh
        n_cells = first_mesh.n_cells
        n_points = first_mesh.n_points

        # ensure Mass array exists
        if "Mass" not in first_mesh.point_data:
            first_mesh.point_data["Mass"] = np.zeros((n_points, FEMORA_MAX_NDF), dtype=np.float32)

        # add cell and point data - ONLY IF NOT EXISTS
        if "ElementTag" not in first_mesh.cell_data:
            first_mesh.cell_data["ElementTag"] = np.full(n_cells, EleTag, dtype=np.uint16)
        if "MaterialTag" not in first_mesh.cell_data:
            first_mesh.cell_data["MaterialTag"] = np.full(n_cells, matTag, dtype=np.uint16)
        if "SectionTag" not in first_mesh.cell_data:
            first_mesh.cell_data["SectionTag"] = np.full(n_cells, sectionTag, dtype=np.uint16)

        self._ensure_ndf_array(first_mesh, ndf)

        first_mesh.cell_data["Region"] = np.full(n_cells, regionTag, dtype=np.uint16)
        first_mesh.cell_data["MeshPartTag_celldata"] = np.full(n_cells, meshTag, dtype=np.uint16)
        first_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points, meshTag, dtype=np.uint16)
        # Merge subsequent meshes
        n_sections = len(self.meshparts_list)
        perc = 1 / n_sections * 100
        progress_callback(perc, f"merged meshpart {1}/{n_sections}")
        self.mesh = pv.MultiBlock([first_mesh])  # Start with the first mesh as a MultiBlock
        for idx, meshpart in enumerate(self.meshparts_list[1:], start=2):
            second_mesh = meshpart.mesh.copy()

            ndf = 0
            if meshpart.element:
                ndf = meshpart.element._ndof
                matTag = meshpart.element.get_material_tag()
                EleTag = meshpart.element.tag
                sectionTag = meshpart.element.get_section_tag()
            elif hasattr(meshpart, 'ndof'):
                ndf = meshpart.ndof
                matTag = getattr(meshpart, 'material_tag', 0)
                EleTag = getattr(meshpart, 'element_tag', 0)
                sectionTag = getattr(meshpart, 'section_tag', 0)
            else:
                ndf = FEMORA_MAX_NDF
                matTag = getattr(meshpart, 'material_tag', 0)
                EleTag = getattr(meshpart, 'element_tag', 0)
                sectionTag = getattr(meshpart, 'section_tag', 0)

            regionTag = meshpart.region.tag
            meshTag = meshpart.tag
            n_cells_second = second_mesh.n_cells
            n_points_second = second_mesh.n_points
            if "Mass" not in second_mesh.point_data:
                second_mesh.point_data["Mass"] = np.zeros((n_points_second, FEMORA_MAX_NDF), dtype=np.float32)
            # add cell and point data to the second mesh
            if "ElementTag" not in second_mesh.cell_data:
                second_mesh.cell_data["ElementTag"] = np.full(n_cells_second, EleTag, dtype=np.uint16)
            if "MaterialTag" not in second_mesh.cell_data:
                second_mesh.cell_data["MaterialTag"] = np.full(n_cells_second, matTag, dtype=np.uint16)

            if "SectionTag" not in second_mesh.cell_data:
                second_mesh.cell_data["SectionTag"] = np.full(n_cells_second, sectionTag, dtype=np.uint16)

            self._ensure_ndf_array(second_mesh, ndf)

            second_mesh.cell_data["Region"] = np.full(n_cells_second, regionTag, dtype=np.uint16)

            second_mesh.cell_data["MeshPartTag_celldata"] = np.full(n_cells_second, meshTag, dtype=np.uint16)
            second_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points_second, meshTag, dtype=np.uint16)
            # Merge with tolerance and optional point merging
            self.mesh.append(second_mesh)
            perc = idx / n_sections * 100
            progress_callback(perc, f"merged meshpart {idx}/{n_sections}")

        self.mesh = self.mesh.combine(
            merge_points=False,
            tolerance=1e-5,
        )
        if self.merging_points:
            mass = self.mesh.point_data["Mass"]
            number_of_points_before_cleaning = self.mesh.number_of_points

            # fist we snap points within tolerance to the first representative point
            points = self._snap_points(self.mesh.points, tol=self.tolerance)
            self.mesh.points = points

            self.mesh = self.mesh.clean(
                tolerance=self.tolerance,
                remove_unused_points=False,
                produce_merge_map=True,
                average_point_data=True,
                merging_array_name="ndf",
                progress_bar=False,
            )

            number_of_points_after_cleaning = self.mesh.number_of_points
            # make the ndf array uint16
            self.mesh.point_data["ndf"] = self.mesh.point_data["ndf"].astype(np.uint16)
            # make the MeshPartTag_pointdata array uint16
            self.mesh.point_data["MeshPartTag_pointdata"] = self.mesh.point_data["MeshPartTag_pointdata"].astype(np.uint16)

            if self.mass_merging == "sum":
                if number_of_points_before_cleaning != number_of_points_after_cleaning:
                    Mass = np.zeros((self.mesh.number_of_points, FEMORA_MAX_NDF), dtype=np.float32)
                    for i in range(self.mesh.field_data["PointMergeMap"].shape[0]):
                        Mass[self.mesh.field_data["PointMergeMap"][i], :] += mass[i, :]

                    self.mesh.point_data["Mass"] = Mass

            del self.mesh.field_data["PointMergeMap"]

        # partition the mesh
        self.mesh.cell_data["Core"] = np.zeros(self.mesh.n_cells, dtype=int)
        if self.num_partitions > 1:
            partitiones = self.mesh.partition(self.num_partitions,
                                              generate_global_id=True,
                                              as_composite=True)
            for i, partition in enumerate(partitiones):
                ids = partition.cell_data["vtkGlobalCellIds"]
                self.mesh.cell_data["Core"][ids] = i

            del partitiones

    @property
    def meshparts(self) -> List[str]:
        """Retrieves the names of mesh parts included in this `AssemblySection`.

        This property returns a list of the user-friendly names (strings) of all
        `MeshPart` instances that were originally provided when creating this
        assembly section.

        Returns:
            List[str]: A list of names of mesh parts included in this
                assembly section.

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> mesh2 = pv.Sphere()
            >>> _ = MeshPart(mesh=mesh1, name="list_part_X", element=element, material=material, region=region)
            >>> _ = MeshPart(mesh=mesh2, name="list_part_Y", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> assembly_section = assembler.create_section(meshparts=["list_part_X", "list_part_Y"])
            >>> print(assembly_section.meshparts)
            ['list_part_X', 'list_part_Y']
        """
        return [meshpart.user_name for meshpart in self.meshparts_list]

    def assign_actor(self, actor) -> None:
        """Assigns a PyVista actor to the assembly section.

        This method associates a visualization actor (typically a `pyvista.Actor`)
        with this `AssemblySection` instance. This actor can then be used for
        rendering the assembled mesh within a visualization pipeline.

        Args:
            actor: The PyVista actor object to assign for visualization.
        """
        self.actor = actor

    def plot(self, **kwargs) -> None:
        """Plots the assembled mesh for this `AssemblySection` using PyVista.

        This method visualizes the `mesh` attribute of the `AssemblySection`
        instance. It utilizes PyVista's plotting capabilities, accepting a wide
        range of keyword arguments for customizing the rendering, which are
        passed directly to `pyvista.UnstructuredGrid.plot()`.

        Args:
            **kwargs: Additional keyword arguments to customize the plot (e.g.,
                `color`, `opacity`, `scalars`, `show_edges`).

        Raises:
            ValueError: If the mesh has not yet been assembled (i.e., `self.mesh` is None).

        Example:
            >>> import femora as fm
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.core.element_base import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import Region
            >>> from femora.components.Section.sectionBase import Section
            >>> # Setup dummy components
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, material_tag=0, section_tag=0):
            ...         super().__init__(tag, nodes, material_tag, section_tag)
            ...         self._ndof = 3
            ...     def get_ndof(self): return self._ndof
            >>> class DummyMaterial(Material):
            ...     def __init__(self, tag, E, nu): super().__init__(tag, E, nu)
            >>> class DummySection(Section):
            ...     def __init__(self, tag, area): super().__init__(tag, area)
            >>> material = DummyMaterial(1, 200e9, 0.3)
            >>> section = DummySection(1, 1.0)
            >>> element = DummyElement(1, [1,2], material.tag, section.tag)
            >>> region = Region(1, "test_region")
            >>> mesh1 = pv.Cube()
            >>> _ = MeshPart(mesh=mesh1, name="section_plot_part", element=element, material=material, region=region)
            >>> assembler = fm.Assembler.get_instance()
            >>> assembler.clear_assembly_sections() # Clear previous sections
            >>> assembly_section = assembler.create_section(meshparts=["section_plot_part"])
            >>> # assembly_section.plot(color='green', show_edges=True) # doctest: +SKIP
        """
        if self.mesh is None:
            raise ValueError("Mesh has not been assembled yet")
        else:
            self.mesh.plot(**kwargs)