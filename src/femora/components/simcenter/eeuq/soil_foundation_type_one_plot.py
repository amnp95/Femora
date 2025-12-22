"""
Browser-based plotting GUI for soil/foundation/piles using PyVista + trame.

This module provides the `SoilFoundationPlotter` class, which offers a web-based
interactive visualization tool for geotechnical models, including soil layers,
foundation blocks, and pile systems. It integrates PyVista for 3D rendering
and trame for creating the interactive web interface.

Install requirements if missing:
    pip install pyvista trame trame-vtk trame-vuetify
"""

from __future__ import annotations
from typing import Optional
import os
import json
import numpy as np


class SoilFoundationPlotter:
    """Browser-based GUI for visualizing soil layers, foundations, and piles.

    This class provides an interactive web interface using PyVista for 3D
    rendering and trame for the UI, allowing users to visualize and
    manipulate geotechnical models. It supports quick conceptual plots
    and detailed discretized meshes from a model builder.

    Attributes:
        pv (module): The imported PyVista module.
        title (str): The title displayed in the plotter's web interface.
        port (int): The port number the trame server will run on.
        structure_info (dict): Dictionary containing structural model information.
        soil_info (dict): Dictionary containing soil layer information.
        foundation_info (dict): Dictionary containing foundation block information.
        pile_info (dict): Dictionary containing pile system information.
        _mesh_file (Optional[str]): Path to an optional external mesh file for the building.
        plotter (pyvista.Plotter): The PyVista plotter instance used for 3D rendering.
        objects (dict): A dictionary storing references to added meshes and their actors.
        state_defaults (dict): Default values for the trame server's state variables.
        server (trame.app.Server): The trame server instance managing the UI and interactions.
        html_view (trame.widgets.vtk.VtkRemoteView): The trame widget for displaying the 3D scene.
        _actual_soil (pyvista.DataSet): Cached PyVista mesh for the discretized soil.
        _actual_pile (pyvista.DataSet): Cached PyVista mesh for the discretized piles.
        _actual_foundation (pyvista.DataSet): Cached PyVista mesh for the discretized foundation.
        _discretized_exists (bool): Flag indicating if actual meshes have been computed and cached.
        _scalars (list[str]): List of available scalar arrays for coloring.

    Example:
        >>> import os
        >>> from femora_plotting import SoilFoundationPlotter
        >>> # Assuming a 'config.json' file exists with structure, soil, foundation, pile info
        >>> # OR provide dictionaries directly
        >>> # plotter = SoilFoundationPlotter(info_file="config.json", port=8082)
        >>> plotter = SoilFoundationPlotter(
        ...     structure_info={"x_min":0, "x_max":10, "y_min":0, "y_max":10, "z_min":0, "z_max":5},
        ...     soil_info={"x_min":-10, "x_max":20, "y_min":-10, "y_max":20,
        ...                "soil_profile":[{"z_bot":-5, "z_top":0}, {"z_bot":-10, "z_top":-5}]},
        ...     foundation_info={"foundation_profile":[{"x_min":0, "x_max":5, "y_min":0, "y_max":5, "z_bot":-1, "z_top":0}]},
        ...     pile_info={"pile_profile":[{"type":"grid", "x_start":1, "y_start":1, "spacing_x":2, "spacing_y":2, "nx":2, "ny":2, "z_top":-0.5, "z_bot":-5, "r":0.2}]},
        ...     port=8081
        ... )
        >>> # plotter.start_server() # Access at http://localhost:8081
    """

    def __init__(
        self,
        structure_info: Optional[dict] = None,
        soil_info: Optional[dict] = None,
        foundation_info: Optional[dict] = None,
        pile_info: Optional[dict] = None,
        info_file: Optional[str] = None,
        server_name: str = "soil_foundation_plotter",
        port: int = 8080,
        title: str = "Soil/Foundation Plotter",
    ) -> None:
        """Initializes the SoilFoundationPlotter.

        Args:
            structure_info: Optional. A dictionary containing information about the
                structural model, such as global bounds and base column locations.
            soil_info: Optional. A dictionary describing the soil profile,
                including layer depths, dimensions, and material properties.
            foundation_info: Optional. A dictionary describing the foundation
                blocks, including their geometry and material.
            pile_info: Optional. A dictionary describing the pile systems,
                including single piles or pile grids.
            info_file: Optional. Path to a JSON file containing all configuration
                information (structure_info, soil_info, etc.). If provided, and
                individual info dicts are None, data will be loaded from this file.
            server_name: The name for the trame server instance.
            port: The port number on which the trame server will listen.
            title: The title to display in the plotter's web interface.

        Raises:
            RuntimeError: If `pyvista` or `trame` packages are not installed.
            FileNotFoundError: If `info_file` is provided but does not exist.
        """
        try:
            import pyvista as pv
        except Exception as exc:
            raise RuntimeError(
                "pyvista is required for SoilFoundationPlotter. Install with: "
                "pip install pyvista"
            ) from exc

        self.pv = pv
        self.title = title
        self.port = port

        # Load configuration data
        (
            self.structure_info,
            self.soil_info,
            self.foundation_info,
            self.pile_info,
        ) = self._load_infos(structure_info, soil_info, foundation_info, pile_info, info_file)

        # In-memory cached actual meshes (no disk persistence)
        self._actual_soil = None
        self._actual_pile = None
        self._actual_foundation = None
        self._scalars = ["Mesh", "Core", "Region", "ElementTag", "MaterialTag"]
        self._discretized_exists = False
        # Extra actors toggled from UI
        self._axes_actor = None
        self._grid_actor = None

        # Handle mesh file
        mesh_file = self.structure_info.get("mesh_file", None) if self.structure_info else None
        if mesh_file == "" or (mesh_file and not os.path.isfile(mesh_file)):
            mesh_file = None
            print("Warning: mesh file is not a valid file")
        self._mesh_file = mesh_file

        # Configure PyVista for web rendering
        pv.OFF_SCREEN = True
        pv.set_plot_theme("document")

        # Initialize PyVista plotter with proper settings for web
        self.plotter = pv.Plotter(
            off_screen=True,
            notebook=False,
            window_size=(1000, 700)
        )
        self.plotter.background_color = "white"

        # Store references to added objects
        self.objects = {}

        # State defaults
        self.state_defaults = {
            "show_soil": True,
            "soil_opacity": 0.35,
            "show_foundation": True,
            "foundation_opacity": 0.55,
            "show_piles": True,
            "piles_opacity": 1.0,
            "show_mesh": bool(mesh_file),
            "mesh_opacity": 1.0,
            "discretized": self._discretized_exists,
            "show_axes": False,
            "show_grid": False,
            "selected_scalar": "Mesh",
        }

        # Setup server
        self._setup_server(server_name)

        # Pre-populate scene
        self.quick_plot()

    def _setup_server(self, server_name: str):
        """Sets up the trame server and UI components.

        Args:
            server_name: The name for the trame server instance.

        Raises:
            RuntimeError: If `trame` stack packages (`trame`, `trame-vtk`,
                `trame-vuetify`) are not installed.
        """
        try:
            from trame.app import get_server
            import trame_vuetify as _tv

            # Get Vuetify version
            _tv_ver = getattr(_tv, "__version__", "2.0.0")
            _tv_major = int(str(_tv_ver).split(".")[0])

            self.server = get_server(server_name)

            # Configure client type based on Vuetify version
            if _tv_major >= 3:
                self.server.client_type = "vue3"
                from trame.ui.vuetify3 import SinglePageWithDrawerLayout
                from trame.widgets import vuetify3 as vuetify
            else:
                self.server.client_type = "vue2"
                from trame.ui.vuetify import SinglePageWithDrawerLayout
                from trame.widgets import vuetify

            from trame.widgets import html, vtk as vtk_widgets

        except Exception as exc:
            raise RuntimeError(
                "SoilFoundationPlotter requires 'trame' stack. Install with: "
                "pip install trame trame-vtk trame-vuetify"
            ) from exc

        state, ctrl = self.server.state, self.server.controller

        # Initialize state variables
        state.update(self.state_defaults)
        # Provide scalar items via state to avoid string-splitting in VSelect
        try:
            state.scalars = list(self._scalars)
        except Exception:
            state.scalars = ["None", "Core", "Region", "ElementTag", "MaterialTag"]
        # Visual styles for toggle buttons
        try:
            state.show_axes_variant = "text"
            state.show_axes_color = "grey"
            state.show_grid_variant = "text"
            state.show_grid_color = "grey"
        except Exception:
            pass

        # Define controller methods
        @ctrl.set("quick_plot")
        def quick_plot_handler():
            self.quick_plot()

        @ctrl.set("actual_plot")
        def actual_plot_handler():
            self.actual_plot()

        @ctrl.set("discretize")
        def discretize_handler():
            self.discretize_and_save()

        @ctrl.set("clear_all")
        def clear_all_handler():
            self.clear_all()

        @ctrl.set("reset_camera")
        def reset_camera_handler():
            self.reset_camera()

        # Camera view helpers
        @ctrl.set("view_iso")
        def view_iso_handler():
            try:
                self.plotter.camera_position = "iso"
            except Exception:
                try:
                    self.plotter.view_isometric()
                except Exception:
                    pass
            self.update_view()

        @ctrl.set("view_xy")
        def view_xy_handler():
            try:
                self.plotter.view_xy()
            except Exception:
                try:
                    self.plotter.camera_position = "xy"
                except Exception:
                    pass
            self.update_view()

        @ctrl.set("view_xz")
        def view_xz_handler():
            try:
                self.plotter.view_xz()
            except Exception:
                try:
                    self.plotter.camera_position = "xz"
                except Exception:
                    pass
            self.update_view()

        @ctrl.set("view_yz")
        def view_yz_handler():
            try:
                self.plotter.view_yz()
            except Exception:
                try:
                    self.plotter.camera_position = "yz"
                except Exception:
                    pass
            self.update_view()

        # Simple toggle helpers for small icon buttons
        @ctrl.set("toggle_axes")
        def toggle_axes_handler():
            try:
                self.server.state.show_axes = not bool(getattr(self.server.state, "show_axes", False))
                if hasattr(self.server.state, "flush"):
                    self.server.state.flush("show_axes")
            except Exception:
                pass

        @ctrl.set("toggle_grid")
        def toggle_grid_handler():
            try:
                self.server.state.show_grid = not bool(getattr(self.server.state, "show_grid", False))
                if hasattr(self.server.state, "flush"):
                    self.server.state.flush("show_grid")
            except Exception:
                pass

        # State change handlers
        @state.change("show_soil", "show_foundation", "show_piles", "show_mesh")
        def on_visibility_change(**kwargs):
            self._apply_visibility()

        @state.change("soil_opacity", "foundation_opacity", "piles_opacity", "mesh_opacity")
        def on_opacity_change(**kwargs):
            self._apply_opacity()

        @state.change("selected_scalar")
        def on_scalar_change(selected_scalar, **kwargs):
            if self._discretized_exists:
                try:
                    self.actual_plot(selected_scalar)
                except Exception as e:
                    print(f"Scalar change error: {e}")

        @state.change("show_axes")
        def on_show_axes_change(show_axes, **kwargs):
            try:
                if bool(show_axes):
                    try:
                        # Prefer explicit boolean toggle if supported
                        self.plotter.show_axes(True)
                    except TypeError:
                        # Older versions: calling without args enables
                        self.plotter.show_axes()
                    except Exception:
                        # Fallback to adding an axes actor in-scene
                        if self._axes_actor is None:
                            self._axes_actor = self.plotter.add_axes()
                    # update styles
                    if hasattr(self.server, 'state'):
                        self.server.state.show_axes_variant = "elevated"
                        self.server.state.show_axes_color = "primary"
                else:
                    hid_ok = False
                    try:
                        # Prefer explicit boolean toggle off
                        self.plotter.show_axes(False)
                        hid_ok = True
                    except Exception:
                        pass
                    if not hid_ok:
                        try:
                            # Some versions expose hide_axes()
                            self.plotter.hide_axes()
                            hid_ok = True
                        except Exception:
                            pass
                    if not hid_ok and self._axes_actor is not None:
                        # Last resort: try removing stored actor
                        try:
                            self.plotter.remove_actor(self._axes_actor)
                        except Exception:
                            pass
                        self._axes_actor = None
                    # update styles
                    if hasattr(self.server, 'state'):
                        self.server.state.show_axes_variant = "text"
                        self.server.state.show_axes_color = "grey"
            except Exception as e:
                print(f"Axes toggle error: {e}")
            self.update_view()

        @state.change("show_grid")
        def on_show_grid_change(show_grid, **kwargs):
            try:
                if bool(show_grid):
                    try:
                        # Most versions simply enable with no args
                        self.plotter.show_grid()
                    except TypeError:
                        # Some versions allow explicit boolean
                        self.plotter.show_grid(True)
                    except Exception:
                        # Fallback try returning actor
                        try:
                            self._grid_actor = self.plotter.show_grid(return_actor=True)
                        except Exception:
                            self._grid_actor = None
                    # update styles
                    if hasattr(self.server, 'state'):
                        self.server.state.show_grid_variant = "elevated"
                        self.server.state.show_grid_color = "primary"
                else:
                    removed = False
                    try:
                        # Proper API to remove bounds axes grid
                        self.plotter.remove_bounds_axes()
                        removed = True
                    except Exception:
                        pass
                    if not removed:
                        try:
                            # Some versions allow disabling grid this way
                            self.plotter.show_grid(False)
                            removed = True
                        except Exception:
                            pass
                    if not removed and self._grid_actor is not None:
                        try:
                            self.plotter.remove_actor(self._grid_actor)
                            removed = True
                        except Exception:
                            pass
                        self._grid_actor = None
                    # update styles
                    if hasattr(self.server, 'state'):
                        self.server.state.show_grid_variant = "text"
                        self.server.state.show_grid_color = "grey"
            except Exception as e:
                print(f"Grid toggle error: {e}")
            self.update_view()

        # Create the layout
        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.title.set_text(self.title)
            layout.icon.click = ctrl.reset_camera

            with layout.drawer:
                # Action buttons
                vuetify.VDivider()
                vuetify.VBtn(
                    "Quick Plot",
                    color="primary",
                    click=ctrl.quick_plot,
                    block=True,
                    prepend_icon="mdi-chart-scatter-plot" if _tv_major >= 3 else None
                )
                vuetify.VBtn(
                    "Discretize",
                    color="success",
                    click=ctrl.discretize,
                    block=True,
                    classes="mt-2",
                    disabled=("discretized", self._discretized_exists),
                    prepend_icon="mdi-cube-scan" if _tv_major >= 3 else None
                )
                vuetify.VBtn(
                    "Actual Plot",
                    color="success",
                    click=ctrl.actual_plot,
                    block=True,
                    classes="mt-2",
                    prepend_icon="mdi-cube-outline" if _tv_major >= 3 else None
                )
                vuetify.VBtn(
                    "Reset Camera",
                    color="secondary",
                    click=ctrl.reset_camera,
                    block=True,
                    classes="mt-2",
                    prepend_icon="mdi-camera-outline" if _tv_major >= 3 else None
                )
                vuetify.VBtn(
                    "Clear All",
                    color="error",
                    click=ctrl.clear_all,
                    block=True,
                    classes="mt-2",
                    prepend_icon="mdi-delete" if _tv_major >= 3 else None
                )

                # Visibility controls
                vuetify.VDivider(classes="my-3")
                html.Div("Visibility", classes="text-subtitle-2 mt-1 mb-1")
                vuetify.VSwitch(
                    v_model=("show_soil", self.state_defaults["show_soil"]),
                    label="Show Soil",
                    dense=True
                )
                vuetify.VSwitch(
                    v_model=("show_foundation", self.state_defaults["show_foundation"]),
                    label="Show Foundation",
                    dense=True
                )
                vuetify.VSwitch(
                    v_model=("show_piles", self.state_defaults["show_piles"]),
                    label="Show Piles",
                    dense=True
                )
                vuetify.VSwitch(
                    v_model=("show_mesh", self.state_defaults["show_mesh"]),
                    label="Show Building",
                    dense=True
                )

                # Opacity controls
                vuetify.VDivider(classes="my-3")
                html.Div("Opacity", classes="text-subtitle-2 mt-1 mb-1")
                vuetify.VSlider(
                    v_model=("soil_opacity", self.state_defaults["soil_opacity"]),
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    label="Soil",
                    hide_details=True
                )
                vuetify.VSlider(
                    v_model=("foundation_opacity", self.state_defaults["foundation_opacity"]),
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    label="Foundation",
                    hide_details=True
                )
                vuetify.VSlider(
                    v_model=("piles_opacity", self.state_defaults["piles_opacity"]),
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    label="Piles",
                    hide_details=True
                )
                vuetify.VSlider(
                    v_model=("mesh_opacity", self.state_defaults["mesh_opacity"]),
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    label="Building",
                    hide_details=True
                )

                # Scalar selection
                vuetify.VDivider(classes="my-3")
                html.Div("Scalar coloring", classes="text-subtitle-2 mt-1 mb-1")
                vuetify.VSelect(
                    v_model=("selected_scalar", self.state_defaults["selected_scalar"]),
                    label="Scalars",
                    items=("scalars", self._scalars),
                    dense=True,
                    clearable=True,
                )

                # Object count display
                vuetify.VDivider(classes="my-3")
                vuetify.VChip(
                    f"Objects: {len(self.objects)}",
                    color="info",
                    variant="elevated" if _tv_major >= 3 else "default",
                    classes="ma-1"
                )

                # Bottom-left compact tools (axes/grid toggles and camera views)
                from trame.widgets import html as _html  # local alias to avoid confusion
                with _html.Div(style="position: absolute; left: 12px; bottom: 12px; z-index: 10;"):
                    # Grid container for two rows, spaced buttons
                    with _html.Div(style="display: grid; grid-template-columns: repeat(3, max-content); gap: 10px 12px;"):
                        if _tv_major >= 3:
                            vuetify.VBtn(
                                icon="mdi-axis-arrow",
                                size="large",
                                variant=("show_axes_variant", "text"),
                                color=("show_axes_color", "grey"),
                                click=ctrl.toggle_axes,
                            )
                            vuetify.VBtn(
                                icon="mdi-grid",
                                size="large",
                                variant=("show_grid_variant", "text"),
                                color=("show_grid_color", "grey"),
                                click=ctrl.toggle_grid,
                            )
                            vuetify.VBtn(
                                icon="mdi-cube-scan",
                                size="large",
                                color="secondary",
                                click=ctrl.view_iso,
                            )
                            vuetify.VBtn(
                                icon="mdi-axis-z-arrow",
                                size="large",
                                color="secondary",
                                click=ctrl.view_xy,
                            )
                            vuetify.VBtn(
                                icon="mdi-axis-y-arrow",
                                size="large",
                                color="secondary",
                                click=ctrl.view_xz,
                            )
                            vuetify.VBtn(
                                icon="mdi-axis-x-arrow",
                                size="large",
                                color="secondary",
                                click=ctrl.view_yz,
                            )
                        else:
                            # Vuetify v2 buttons, larger and spaced
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                depressed=("show_axes", False),
                                color=("show_axes_color", "grey"),
                                click=ctrl.toggle_axes,
                                children=[vuetify.VIcon("mdi-axis-arrow")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                depressed=("show_grid", False),
                                color=("show_grid_color", "grey"),
                                click=ctrl.toggle_grid,
                                children=[vuetify.VIcon("mdi-grid")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                color="secondary",
                                click=ctrl.view_iso,
                                children=[vuetify.VIcon("mdi-cube-scan")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                color="secondary",
                                click=ctrl.view_xy,
                                children=[vuetify.VIcon("mdi-axis-z-arrow")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                color="secondary",
                                click=ctrl.view_xz,
                                children=[vuetify.VIcon("mdi-axis-y-arrow")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                large=True,
                                color="secondary",
                                click=ctrl.view_yz,
                                children=[vuetify.VIcon("mdi-axis-x-arrow")]
                            )

            with layout.content:
                with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
                    # Create the VTK view
                    self.html_view = vtk_widgets.VtkRemoteView(
                        self.plotter.ren_win,
                        ref="view",
                        interactive_ratio=1,
                        interactive_quality=60,
                        still_quality=98,
                        style="width: 100%; height: 100vh;",
                    )

                    # Set controller methods for view updates
                    ctrl.view_update = self.html_view.update
                    ctrl.view_reset_camera = self.html_view.reset_camera

    def quick_plot(self) -> None:
        """Builds a fast, conceptual scene with soil, foundation, and piles.

        This method generates simplified geometric representations (boxes for
        soil/foundation, cylinders for piles) for a quick overview of the
        geotechnical model. It clears any existing objects before plotting.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     soil_info={"x_min":-10, "x_max":10, "y_min":-10, "y_max":10,
            ...                "soil_profile":[{"z_bot":-5, "z_top":0}]},
            ...     foundation_info={"foundation_profile":[{"x_min":-2, "x_max":2, "y_min":-2, "y_max":2, "z_bot":-1, "z_top":0}]}
            ... )
            >>> plotter.quick_plot()
        """
        print("Building quick plot...")

        # Clear existing objects
        self.clear_all()

        # Soil layers as boxes with khaki color palette
        if self.soil_info is not None and "soil_profile" in self.soil_info:
            self._add_soil_layers()

        # Foundation blocks as boxes
        if self.foundation_info is not None and "foundation_profile" in self.foundation_info:
            self._add_foundation_blocks()

        # Piles as cylinders
        if self.pile_info is not None and "pile_profile" in self.pile_info:
            self._add_piles()

        # Optional mesh file
        if self._mesh_file:
            self._add_mesh_file()

        # Apply current visibility and opacity settings
        self._apply_visibility()
        self._apply_opacity()

        # Reset camera and update view
        self.reset_camera()
        self.update_view()
        print(f"Quick plot complete. Total objects: {len(self.objects)}")


    def _add_soil_layers(self):
        """Adds conceptual soil layers as colored boxes to the scene."""
        khaki_colors = [
            "#F0E68C", "#DEB887", "#D2B48C", "#BDB76B", "#F4A460", "#CD853F",
            "#A0522D", "#8B7355", "#6B8E23", "#556B2F", "#8FBC8F", "#9ACD32",
        ]

        x_min = self.soil_info.get("x_min", 0.0)
        x_max = self.soil_info.get("x_max", 0.0)
        y_min = self.soil_info.get("y_min", 0.0)
        y_max = self.soil_info.get("y_max", 0.0)

        for idx, layer in enumerate(self.soil_info["soil_profile"]):
            z_bot = layer.get("z_bot", 0.0)
            z_top = layer.get("z_top", 0.0)
            if z_top <= z_bot:
                continue

            center = ((x_min + x_max) * 0.5, (y_min + y_max) * 0.5, (z_bot + z_top) * 0.5)
            x_len = max(1e-6, x_max - x_min)
            y_len = max(1e-6, y_max - y_min)
            z_len = max(1e-6, z_top - z_bot)

            box = self.pv.Cube(center=center, x_length=x_len, y_length=y_len, z_length=z_len)
            soil_color = khaki_colors[idx % len(khaki_colors)]

            name = f"soil_{idx}"
            actor = self.plotter.add_mesh(
                box,
                name=name,
                color=soil_color,
                opacity=self.state_defaults["soil_opacity"],
                smooth_shading=False,
                show_edges=True,
            )
            self.objects[name] = {
                "mesh": box,
                "actor": actor,
                "type": "soil",
                "layer": idx
            }

    def _add_foundation_blocks(self):
        """Adds conceptual foundation blocks as colored boxes to the scene."""
        for fidx, f in enumerate(self.foundation_info["foundation_profile"]):
            try:
                x_min, x_max = f["x_min"], f["x_max"]
                y_min, y_max = f["y_min"], f["y_max"]
                z_bot, z_top = f["z_bot"], f["z_top"]
            except KeyError:
                continue

            if x_max <= x_min or y_max <= y_min or z_top <= z_bot:
                continue

            center = ((x_min + x_max) * 0.5, (y_min + y_max) * 0.5, (z_bot + z_top) * 0.5)
            box = self.pv.Cube(
                center=center,
                x_length=max(1e-6, x_max - x_min),
                y_length=max(1e-6, y_max - y_min),
                z_length=max(1e-6, z_top - z_bot),
            )

            name = f"foundation_{fidx}"
            actor = self.plotter.add_mesh(
                box,
                name=name,
                color="#A27EA8",
                opacity=self.state_defaults["foundation_opacity"],
                smooth_shading=False,
                show_edges=True,
            )
            self.objects[name] = {
                "mesh": box,
                "actor": actor,
                "type": "foundation",
                "index": fidx
            }

    def _add_piles(self):
        """Adds conceptual piles to the scene.

        Supports both individual pile definitions and grids of piles.
        """
        pidx = 0
        for pile in self.pile_info["pile_profile"]:
            ptype = str(pile.get("type", "single")).lower()

            if ptype == "grid":
                pidx = self._add_pile_grid(pile, pidx)
            else:
                pidx = self._add_single_pile(pile, pidx)

    def _add_pile_grid(self, pile: dict, pidx: int) -> int:
        """Adds a grid of conceptual piles to the scene.

        Args:
            pile: A dictionary containing parameters for the pile grid
                (e.g., x_start, y_start, spacing_x, ny, nx, z_top, z_bot, r).
            pidx: The starting index for naming the piles.

        Returns:
            The next available index for naming piles after adding the grid.
        """
        try:
            x_start = float(pile["x_start"])
            y_start = float(pile["y_start"])
            spacing_x = float(pile["spacing_x"])
            spacing_y = float(pile["spacing_y"])
            nx = int(pile["nx"])
            ny = int(pile["ny"])
            z_top = float(pile["z_top"])
            z_bot = float(pile["z_bot"])
            radius = float(pile.get("r", 0.2))
        except (KeyError, ValueError):
            return pidx

        if nx < 1 or ny < 1 or spacing_x <= 0 or spacing_y <= 0:
            return pidx

        height = abs(z_top - z_bot)
        direction = (0.0, 0.0, z_top - z_bot)

        for i in range(nx):
            for j in range(ny):
                x = x_start + i * spacing_x
                y = y_start + j * spacing_y
                center = (x, y, (z_top + z_bot) * 0.5)

                cyl = self.pv.Cylinder(
                    center=center,
                    direction=direction,
                    radius=max(1e-6, radius),
                    height=max(1e-6, height),
                    resolution=24
                )

                name = f"pile_{pidx}"
                actor = self.plotter.add_mesh(
                    cyl,
                    name=name,
                    color="#55AA66",
                    opacity=self.state_defaults["piles_opacity"],
                    smooth_shading=True,
                    show_edges=True,
                )
                self.objects[name] = {
                    "mesh": cyl,
                    "actor": actor,
                    "type": "pile",
                    "index": pidx,
                    "grid_pos": (i, j)
                }
                pidx += 1

        return pidx

    def _add_single_pile(self, pile: dict, pidx: int) -> int:
        """Adds a single conceptual pile to the scene.

        Args:
            pile: A dictionary containing parameters for a single pile
                (e.g., x_top, y_top, z_top, x_bot, y_bot, z_bot, r).
            pidx: The starting index for naming the pile.

        Returns:
            The next available index for naming piles after adding this pile.
        """
        try:
            x_top = float(pile["x_top"])
            y_top = float(pile["y_top"])
            z_top = float(pile["z_top"])
            x_bot = float(pile.get("x_bot", x_top))
            y_bot = float(pile.get("y_bot", y_top))
            z_bot = float(pile.get("z_bot", z_top - 1.0))
            radius = float(pile.get("r", 0.2))
        except (KeyError, ValueError):
            return pidx + 1

        direction = (x_top - x_bot, y_top - y_bot, z_top - z_bot)
        height = (direction[0]**2 + direction[1]**2 + direction[2]**2) ** 0.5
        center = ((x_top + x_bot) * 0.5, (y_top + y_bot) * 0.5, (z_top + z_bot) * 0.5)

        cyl = self.pv.Cylinder(
            center=center,
            direction=direction,
            radius=max(1e-6, radius),
            height=max(1e-6, height),
            resolution=24
        )

        name = f"pile_{pidx}"
        actor = self.plotter.add_mesh(
            cyl,
            name=name,
            color="#55AA66",
            opacity=self.state_defaults["piles_opacity"],
            smooth_shading=True,
            show_edges=True,
        )
        self.objects[name] = {
            "mesh": cyl,
            "actor": actor,
            "type": "pile",
            "index": pidx
        }

        return pidx + 1

    def _add_mesh_file(self):
        """Adds an external mesh file (e.g., building model) to the scene."""
        try:
            mesh = self.pv.read(self._mesh_file)
            name = "mesh_file"
            actor = self.plotter.add_mesh(
                mesh,
                name=name,
                color="#333333",
                opacity=self.state_defaults["mesh_opacity"],
                show_edges=True,
                render_lines_as_tubes=True,
                line_width=2.0,
            )
            self.objects[name] = {
                "mesh": mesh,
                "actor": actor,
                "type": "mesh"
            }
        except Exception as e:
            print(f"Failed to load mesh file {self._mesh_file}: {e}")

    def clear_all(self):
        """Clears all objects from the PyVista plotter and the internal object registry.

        This effectively resets the 3D scene.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter()
            >>> plotter.quick_plot()
            >>> plotter.clear_all()
        """
        self.plotter.clear()
        self.objects.clear()
        self.update_view()
        print("Cleared all objects")

    def reset_camera(self):
        """Resets the PyVista plotter's camera to an isometric default position.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter()
            >>> plotter.quick_plot()
            >>> plotter.reset_camera()
        """
        self.plotter.reset_camera()
        self.plotter.camera_position = "iso"
        self.update_view()

    def _apply_visibility(self):
        """Applies visibility settings to objects in the scene based on UI state."""
        if not hasattr(self.server, 'state'):
            return

        state = self.server.state
        vis_map = {
            "soil": getattr(state, "show_soil", True),
            "foundation": getattr(state, "show_foundation", True),
            "pile": getattr(state, "show_piles", True),
            "mesh": getattr(state, "show_mesh", True),
        }

        for name, obj_data in self.objects.items():
            obj_type = obj_data["type"]
            if obj_type in vis_map:
                try:
                    actor = obj_data["actor"]
                    actor.SetVisibility(1 if vis_map[obj_type] else 0)
                except Exception as e:
                    print(f"Error setting visibility for {name}: {e}")

        self.update_view()

    def _apply_opacity(self):
        """Applies opacity settings to objects in the scene based on UI state."""
        if not hasattr(self.server, 'state'):
            return

        state = self.server.state
        opa_map = {
            "soil": getattr(state, "soil_opacity", 0.35),
            "foundation": getattr(state, "foundation_opacity", 0.55),
            "pile": getattr(state, "piles_opacity", 1.0),
            "mesh": getattr(state, "mesh_opacity", 0.3),
        }

        for name, obj_data in self.objects.items():
            obj_type = obj_data["type"]
            if obj_type in opa_map:
                try:
                    actor = obj_data["actor"]
                    opacity = max(0.0, min(1.0, opa_map[obj_type]))
                    actor.GetProperty().SetOpacity(opacity)
                except Exception as e:
                    print(f"Error setting opacity for {name}: {e}")

        self.update_view()

    def update_view(self):
        """Updates the 3D view in the web interface.

        This method triggers a re-render of the PyVista scene within the trame
        web application, reflecting any changes made to actors or camera.
        """
        try:
            if hasattr(self, 'html_view'):
                self.html_view.update()
        except Exception as e:
            # This can happen during initial server setup before html_view is fully ready
            print(f"View update error (normal during initialization): {e}")

    def _load_infos(
        self,
        structure_info: Optional[dict],
        soil_info: Optional[dict],
        foundation_info: Optional[dict],
        pile_info: Optional[dict],
        info_file: Optional[str],
    ) -> tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]]:
        """Loads configuration information from a file or uses provided dictionaries.

        If `info_file` is provided and valid, it will attempt to load configuration
        from there, overwriting or supplementing any individual info dictionaries
        that were not explicitly provided.

        Args:
            structure_info: Optional. Initial structure information dictionary.
            soil_info: Optional. Initial soil information dictionary.
            foundation_info: Optional. Initial foundation information dictionary.
            pile_info: Optional. Initial pile information dictionary.
            info_file: Optional. Path to a JSON file containing all configuration data.

        Returns:
            A tuple containing the loaded (or provided) structure_info, soil_info,
            foundation_info, and pile_info dictionaries.

        Raises:
            FileNotFoundError: If `info_file` is specified but does not exist.
        """
        if info_file is not None and (not structure_info or not soil_info or not foundation_info or not pile_info):
            if not os.path.isfile(info_file):
                raise FileNotFoundError(f"info_file not found: {info_file}")
            with open(info_file, "r") as f:
                info = json.load(f)
            structure_info = structure_info or info.get("structure_info", None)
            soil_foundation_info = info.get("soil_foundation_info", {})
            soil_info = soil_info or soil_foundation_info.get("soil_info", None)
            foundation_info = foundation_info or soil_foundation_info.get("foundation_info", None)
            pile_info = pile_info or soil_foundation_info.get("pile_info", None)
        return structure_info, soil_info, foundation_info, pile_info

    def start_server(self, **kwargs):
        """Starts the trame server, making the GUI accessible via a web browser.

        This method blocks until the server is stopped (e.g., by Ctrl+C in the
        console or closing the browser tab if configured that way).

        Args:
            **kwargs: Additional keyword arguments to pass to `self.server.start()`.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     soil_info={"x_min":-10, "x_max":10, "y_min":-10, "y_max":10,
            ...                "soil_profile":[{"z_bot":-5, "z_top":0}]},
            ...     port=8085
            ... )
            >>> # This will start the server and block
            >>> # Open your browser to http://localhost:8085
            >>> # plotter.start_server(timeout=0) # timeout=0 for non-blocking in tests, remove for actual use
        """
        print(f"Starting Soil Foundation Plotter on port {self.port}")
        print(f"Open browser to: http://localhost:{self.port}")
        print("Press Ctrl+C to stop the server")

        self.server.start(port=self.port, **kwargs)

    def get_object_list(self) -> list[str]:
        """Gets a list of names of all currently plotted objects in the scene.

        Returns:
            A list of strings, where each string is the unique name of a
            plotted object.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     soil_info={"x_min":-1, "x_max":1, "y_min":-1, "y_max":1,
            ...                "soil_profile":[{"z_bot":-1, "z_top":0}]}
            ... )
            >>> plotter.quick_plot()
            >>> obj_names = plotter.get_object_list()
            >>> print(obj_names)
            ['soil_0']
        """
        return list(self.objects.keys())

    def get_object_info(self, name: str) -> Optional[dict]:
        """Gets detailed information about a specific plotted object.

        Args:
            name: The unique name of the object to retrieve information for.

        Returns:
            A dictionary containing the object's mesh, actor, type, and other
            associated data, or None if no object with the given name exists.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     soil_info={"x_min":-1, "x_max":1, "y_min":-1, "y_max":1,
            ...                "soil_profile":[{"z_bot":-1, "z_top":0}]}
            ... )
            >>> plotter.quick_plot()
            >>> info = plotter.get_object_info("soil_0")
            >>> if info:
            ...     print(info["type"])
            soil
        """
        return self.objects.get(name, None)

    def remove_object(self, name: str):
        """Removes a specific object from the plotter and its internal registry.

        Args:
            name: The unique name of the object to remove.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     soil_info={"x_min":-1, "x_max":1, "y_min":-1, "y_max":1,
            ...                "soil_profile":[{"z_bot":-1, "z_top":0}]}
            ... )
            >>> plotter.quick_plot()
            >>> plotter.remove_object("soil_0")
            Removed object: soil_0
        """
        if name in self.objects:
            self.plotter.remove_actor(name)
            del self.objects[name]
            self.update_view()
            print(f"Removed object: {name}")


    def actual_plot(self, scalar: Optional[str] = None):
        """Builds and renders the actual, discretized meshes from the model builder.

        This method triggers the computation of detailed meshes for soil,
        foundation, and piles using an external model builder. Once computed,
        these meshes are cached in memory for subsequent plots. It clears
        any existing scene before adding the new meshes.

        Args:
            scalar: Optional. The name of the scalar array to use for coloring
                the meshes (e.g., "Core", "Region", "ElementTag"). If "Mesh"
                or "None", no scalar coloring is applied.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     structure_info={"x_min":0, "x_max":1, "y_min":0, "y_max":1, "z_min":0, "z_max":1},
            ...     soil_info={"x_min":-2, "x_max":2, "y_min":-2, "y_max":2,
            ...                "soil_profile":[{"z_bot":-2, "z_top":0, "nz":1, "material":"Elastic", "mat_props":[1e6,0.3,2.0]}]}
            ... )
            >>> # This will call the external model builder to create detailed meshes
            >>> plotter.actual_plot()
            >>> # You can also specify a scalar for coloring if available in the meshes
            >>> # plotter.actual_plot(scalar="MaterialTag")
        """
        # Clear existing scene
        self.clear_all()
        if scalar == "Mesh" or scalar == "None":
            scalar = None

        # If already computed, reuse in-memory cached meshes; otherwise compute once
        pile_mesh, foundation_mesh, soil_mesh = None, None, None
        if self._discretized_exists and self._actual_soil is not None:
            pile_mesh = self._actual_pile
            foundation_mesh = self._actual_foundation
            soil_mesh = self._actual_soil
        else:
            pile_mesh, foundation_mesh, soil_mesh = self._compute_actual_meshes()
            if pile_mesh is None and foundation_mesh is None and soil_mesh is None:
                return
            # Cache in memory and mark as discretized
            self._actual_pile = pile_mesh
            self._actual_foundation = foundation_mesh
            self._actual_soil = soil_mesh
            self._discretized_exists = True
            try:
                if hasattr(self, 'server'):
                    self.server.state.discretized = True
                    if hasattr(self.server.state, 'flush'):
                        self.server.state.flush()
            except Exception:
                pass

        # Add meshes to the scene with appropriate types
        try:
            if soil_mesh is not None and soil_mesh.n_cells > 0:
                soil_actor = self.plotter.add_mesh(
                    soil_mesh,
                    name="soil_mesh",
                    color="#C2B280",  # khaki-like
                    opacity=self.state_defaults["soil_opacity"],
                    show_edges=True,
                    scalars=scalar,
                )
                self.objects["soil_mesh"] = {
                    "mesh": soil_mesh,
                    "actor": soil_actor,
                    "type": "soil",
                }

            if foundation_mesh is not None and foundation_mesh.n_cells > 0:
                foundation_actor = self.plotter.add_mesh(
                    foundation_mesh,
                    name="foundation_mesh",
                    color="grey",
                    opacity=self.state_defaults["foundation_opacity"],
                    show_edges=True,
                    scalars=scalar,
                )
                self.objects["foundation_mesh"] = {
                    "mesh": foundation_mesh,
                    "actor": foundation_actor,
                    "type": "foundation",
                }

            if pile_mesh is not None and pile_mesh.n_cells > 0:
                pile_actor = self.plotter.add_mesh(
                    pile_mesh,
                    name="pile_mesh",
                    color="#55AA66",
                    opacity=self.state_defaults["piles_opacity"],
                    show_edges=True,
                    scalars=scalar,
                    render_lines_as_tubes=True,
                    line_width=6.0,
                )
                self.objects["pile_mesh"] = {
                    "mesh": pile_mesh,
                    "actor": pile_actor,
                    "type": "pile",
                }
        except Exception as exc:
            print(f"Error adding actual meshes: {exc}")

        # Optional building mesh from file
        if self._mesh_file:
            self._add_mesh_file()

        # Apply current toggles and opacities
        self._apply_visibility()
        self._apply_opacity()

        # Reset camera and update
        self.reset_camera()
        self.update_view()


    def _compute_actual_meshes(self):
        """Computes the actual, discretized meshes using the model builder.

        This method attempts to import and use the `soil_foundation_type_one`
        function from `femora.components.simcenter.eeuq.soil_foundation_type_one`
        to generate detailed PyVista meshes based on the provided configuration.

        Returns:
            A tuple containing (pile_mesh, foundation_mesh, soil_mesh) as
            PyVista DataSet objects, or (None, None, None) if computation fails.
        """
        try:
            from femora.components.simcenter.eeuq.soil_foundation_type_one import soil_foundation_type_one
            return soil_foundation_type_one(
                structure_info=self.structure_info,
                soil_info=self.soil_info,
                foundation_info=self.foundation_info,
                pile_info=self.pile_info,
                plotting=True,
            )


        except Exception as exc:
            print(f"Discretization failed: {exc}")
            return None, None, None

    def _check_discretized_exists(self) -> bool:
        """Checks if the discretized meshes are currently cached in memory.

        Returns:
            True if all three main meshes (soil, pile, foundation) are cached,
            False otherwise.
        """
        return self._actual_soil is not None and self._actual_pile is not None and self._actual_foundation is not None

    def _save_discretized(self, pile_mesh, foundation_mesh, soil_mesh):
        """Caches the computed discretized meshes in memory.

        This is a no-operation function as meshes are kept in memory only
        based on user request or first computation, not saved to disk here.

        Args:
            pile_mesh (pyvista.DataSet): The computed pile mesh.
            foundation_mesh (pyvista.DataSet): The computed foundation mesh.
            soil_mesh (pyvista.DataSet): The computed soil mesh.
        """
        self._actual_pile = pile_mesh
        self._actual_foundation = foundation_mesh
        self._actual_soil = soil_mesh

    def _load_discretized(self):
        """Returns the already-cached discretized meshes from memory.

        Returns:
            A tuple containing (pile_mesh, foundation_mesh, soil_mesh) as
            PyVista DataSet objects.
        """
        return self._actual_pile, self._actual_foundation, self._actual_soil

    def discretize_and_save(self):
        """Computes and caches the actual discretized meshes in memory.

        This method performs the one-time discretization using the model builder
        and stores the resulting PyVista meshes in memory. Once executed, it
        marks the meshes as existing, preventing re-computation. The associated
        UI button will be disabled after successful execution.

        Example:
            >>> from femora_plotting import SoilFoundationPlotter
            >>> plotter = SoilFoundationPlotter(
            ...     structure_info={"x_min":0, "x_max":1, "y_min":0, "y_max":1, "z_min":0, "z_max":1},
            ...     soil_info={"x_min":-2, "x_max":2, "y_min":-2, "y_max":2,
            ...                "soil_profile":[{"z_bot":-2, "z_top":0, "nz":1, "material":"Elastic", "mat_props":[1e6,0.3,2.0]}]}
            ... )
            >>> plotter.discretize_and_save() # This will compute and cache meshes
            >>> # print(plotter._discretized_exists) # This would be True after successful computation
        """
        if self._discretized_exists:
            print("Discretized meshes already exist. Skipping.")
            return
        pile_mesh, foundation_mesh, soil_mesh = self._compute_actual_meshes()
        if pile_mesh is None and foundation_mesh is None and soil_mesh is None:
            return
        self._save_discretized(pile_mesh, foundation_mesh, soil_mesh)
        self._discretized_exists = True
        try:
            if hasattr(self, 'server'):
                self.server.state.discretized = True
                if hasattr(self.server.state, 'flush'):
                    self.server.state.flush()
        except Exception:
            pass
