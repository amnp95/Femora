
def soil_foundation_type_one(model_filename="model.tcl", 
                             structure_info=None, 
                             soil_info=None, 
                             foundation_info=None, 
                             pile_info=None,
                             info_file=None,
                             EEUQ=False,
                             plotting=False):
    # This model creates a soil profile and foundation for a custom building,
    # designed for use in the EE-UQ application.
    # Developed by Amin Pakzad, University of Washington.
    # Users can define their own building and soil parameters within this framework.

    # ==========================================================================
    # Assumptions and Simplifications :
    #   1 - all the materials for the soil profile are linear elastic
    #   2 - the soil profile is layerd horizontally
    #   3 - the custom building bays should be in x and y direction and the height should be in z direction
    # ========================================================================
    # input parameters
    if info_file is not None:
        import json
        with open(info_file, 'r') as f:
            info = json.load(f)
            structure_info = info.get("structure_info", None)
            soil_foundation_info = info.get("soil_foundation_info", None)
            if soil_foundation_info is None:
                print("Error: soil_foundation_info is not defined in the info file")
                sys.exit(1)
            if structure_info is None:
                print("Error: structure_info is not defined in the info file")
                sys.exit(1)
            soil_info = soil_foundation_info.get("soil_info", None)
            foundation_info = soil_foundation_info.get("foundation_info", None)
            pile_info = soil_foundation_info.get("pile_info", None)
            if soil_info is None:
                print("Error: soil_info is not defined in the info file")
                sys.exit(1)
            if foundation_info is None:
                print("Error: foundation_info is not defined in the info file")
                sys.exit(1)
            if pile_info is None:
                print("Error: pile_info is not defined in the info file")
                sys.exit(1)

    # ==========================================================================
    # Soil materials properties for this code
    # ==========================================================================
    # supported materials
    soil_supported_materials = ["Elastic"]

    # for Ealstic material the properties are :
    #   1 - Elastic Modulus (E)
    #   2 - Poisson Ratio (nu)  
    #   3 - Density (rho)

    # future work :
    #   1 - pressure dependent multi yield material
    #   2 - J2 cyclic bounding surface material
    #   3 - Drucker Prager material

    soil_supported_dampings = ["No-Damping","Frequency-Rayleigh"]
    # for frequency rayleigh damping the properties are :
    #   1 - damping factor (xi_s)
    #   2 - frequency 1 (f1)
    #   3 - frequency 2 (f2)

    # future work :
    #   1 - constant damping
    #   2 - modal damping
    #   3 - .................

    # =============================================================================
    # Foundation material properties for this code
    # =============================================================================

    # supported materials
    foundation_supported_materials = ["Elastic"]

    # for Ealstic material the properties are :
    #   1 - Elastic Modulus (E)
    #   2 - Poisson Ratio (nu)
    #   3 - Density (rho)

    # future work :
    #   1 - Concrete01 material
    #   2 - Concrete02 material

    foundation_supported_dampings = ["No-Damping","Frequency-Rayleigh"]
    # for frequency rayleigh damping the properties are :
    #   1 - damping factor (xi_s)
    #   2 - frequency 1 (f1)
    #   3 - frequency 2 (f2)
    # future work :
    #   1 - constant damping
    #   2 - modal damping
    #   3 - .................


    # =============================================================================
    # Pile material properties for this code
    # =============================================================================
    # supported materials
    pile_supported_materials = ["Elastic"]

    # for Ealstic Pile material the properties are :
    #   1 - Elastic Modulus (E)
    #   2 - Area (A)
    #   3 - Moment of Inertia Iy (Iy)
    #   4 - Moment of Inertia Iz (Iz)
    #   5 - Shear Modulus (G)
    #   6 - Moment of Inertia J (J)

    # future work :
    #  1 - steel material
    #  2 - concrete material

    # supported pile sections
    pile_supported_sections = ["No-Section"]

    # future work :
    #  1 - Circular section
    #  2 - Rectangular section
    #  3 - T section
    #  4 - I section
    #  5 - Wf section

    # ============================================================================
    # import libraries
    # ============================================================================
    import femora as fm 
    import os
    import sys
    import numpy as np
    import pyvista as pv
    import meshlib.mrmeshpy as mr
    
    fm.set_results_folder("Results")

    # ==========================================================================
    # change the grid piles to single piles
    # =========================================================================
    piles_to_add = []
    piles_to_remove = []
    for pile_index, pile in enumerate(pile_info["pile_profile"]):
        type = pile.get("type", "single")
        if type == "single":
            continue
        elif type == "grid":
            piles_to_remove.append(pile_index)
            nx = pile.get("nx")
            ny = pile.get("ny")
            spacing_x = pile.get("spacing_x")
            spacing_y = pile.get("spacing_y")
            if nx < 1 or ny < 1 or spacing_x <= 0 or spacing_y <= 0:
                print("Error: pile grid parameters are not valid. Check nx, ny, spacing_x, spacing_y")
                sys.exit(1)
            x_start = pile.get("x_start", None)
            y_start = pile.get("y_start", None)
            z_bot = pile.get("z_bot", None)
            z_top = pile.get("z_top", None)
            r = pile.get("r", None)
            section = pile.get("section", None)
            material = pile.get("material", None)
            mat_props = pile.get("mat_props", None)
            nz = pile.get("nz", None)
            transformation = pile.get("transformation", None)
            if x_start is None or y_start is None or z_bot is None or z_top is None or r is None \
            or section is None or material is None or mat_props is None or nz is None:
                print("Error: pile grid parameters are not valid. Check x_start, y_start, z_bot, z_top, r, section, material, mat_props, nz")
                sys.exit(1)
            for i in range(nx):
                for j in range(ny):
                    new_pile = {
                        "x_top": x_start + i * spacing_x,
                        "y_top": y_start + j * spacing_y,
                        "z_top": z_top,
                        "x_bot": x_start + i * spacing_x,
                        "y_bot": y_start + j * spacing_y,
                        "z_bot": z_bot,
                        "r": r,
                        "section": section,
                        "material": material,
                        "mat_props": mat_props,
                        "nz": nz,
                        "transformation": transformation
                    }
                    piles_to_add.append(new_pile)
        else:
            print("Error: pile type is not supported. Supported types are: single, grid")
            sys.exit(1)

    # remove the grid piles
    for index in sorted(piles_to_remove, reverse=True):
        del pile_info["pile_profile"][index]
    # add the new single piles
    pile_info["pile_profile"].extend(piles_to_add)
    # ============================================================================
    # Input parameters validation
    # =============================================================================

    # check the soil profile
    for layer_index, layer in enumerate(soil_info["soil_profile"]):
        if layer["z_top"] <= layer["z_bot"]:
            print("Error: soil layer z_top is less than or equal to z_bot for layer index : " + str(layer_index+1))
            sys.exit(1)
        if layer["nz"] < 1:
            print("Error: Number of elements in Z direction is less than 1 for layer index : " + str(layer_index+1))
            sys.exit(1)
        if layer["material"] not in soil_supported_materials:
            print("Error: material " + layer["material"] + " is not supported for soil layer index : " + str(layer_index+1))
            sys.exit(1)
        
        # check material properties
        if layer["material"] == "Elastic":
            length_mat_props = 3
            if len(layer["mat_props"]) != length_mat_props:
                print("Error: number of material properties is not correct for soil layer index : " + str(layer_index+1))
                sys.exit(1)
            E   = layer["mat_props"][0]
            nu  = layer["mat_props"][1]
            rho = layer["mat_props"][2]
            try: 
                assert E > 0 and nu >= 0 and nu < 0.5 and rho > 0
            except: 
                print("Error: material properties are not valid for soil layer index : " + str(layer_index+1))
                sys.exit(1)
        else:
            print("Error: material " + layer["material"] + " is not implemented yet for soil layer index : " + str(layer_index+1))
            sys.exit(1)

        # check damping
        if layer["damping"] not in soil_supported_dampings:
            print("Error: damping " + layer["damping"] + " is not supported for soil layer index : " + str(layer_index+1))
            print("Supported dampings are: ", soil_supported_dampings)
            sys.exit(1)
        if layer["damping"] == "Frequency-Rayleigh":
            length_damping_props = 3
            if len(layer["damping_props"]) != length_damping_props:
                print("Error: number of damping properties is not correct for soil layer index : " + str(layer_index+1))
                sys.exit(1)
            xi_s = layer["damping_props"][0]
            f1   = layer["damping_props"][1]
            f2   = layer["damping_props"][2]
            try: 
                assert xi_s >= 0 and xi_s < 1 and f1 > 0 and f2 > f1
            except:
                print("Error: damping properties are not valid for soil layer index : " + str(layer_index+1))
                sys.exit(1)
        elif layer["damping"] == "No-Damping":
            pass
        else:
            print("Error: damping " + layer["damping"] + " is not implemented yet for soil layer index : " + str(layer_index+1))
            sys.exit(1)
        


    # find the min and max z of the soil profile
    Z_MIN = min([layer["z_bot"] for layer in soil_info["soil_profile"]])
    Z_MAX = max([layer["z_top"] for layer in soil_info["soil_profile"]])
    # print("Z_MIN = ", Z_MIN)
    # print("Z_MAX = ", Z_MAX)

    if soil_info["nx"] < 1 or soil_info["ny"] < 1:
        print("Error: Number of cells in X or Y direction is less than 1")
        sys.exit(1)


    # check the piles
    for pile_index, pile in enumerate(pile_info["pile_profile"]):

        # check section and material
        if pile["section"] not in pile_supported_sections:
            print("Error: section " + pile["section"] + " is not supported for pile index : " + str(pile_index+1))
            sys.exit(1)
        if pile["material"] not in pile_supported_materials:
            print("Error: material " + pile["material"] + " is not supported for pile index : " + str(pile_index+1))
            sys.exit(1)

        # check pile elevation
        if pile["z_top"] <= pile["z_bot"]:
            print("Error: pile z_top is less than or equal to z_bot for pile index : " + str(pile_index+1))
            sys.exit(1)
        if pile["z_bot"] < Z_MIN:
            print("Error: pile z_bot is less than soil profile z_min for pile index : " + str(pile_index+1))
            sys.exit(1)
        if pile["z_bot"] > Z_MAX:
            print("Error: pile z_bot is greater than soil profile z_max for pile index : " + str(pile_index+1))
            sys.exit(1)
        
        # check pile location
        # check pile location within soil bounds for both top and bottom points
        x_min = soil_info["x_min"]
        x_max = soil_info["x_max"]
        y_min = soil_info["y_min"]
        y_max = soil_info["y_max"]

        if (pile["x_top"] < x_min or pile["x_top"] > x_max or
            pile["y_top"] < y_min or pile["y_top"] > y_max or
            pile["x_bot"] < x_min or pile["x_bot"] > x_max or
            pile["y_bot"] < y_min or pile["y_bot"] > y_max):
            print("Error: pile x or y location (top/bottom) is out of soil profile bounds for pile index : " + str(pile_index+1))
            sys.exit(1)

        # check pile radius
        if pile["r"] <= 0:
            print("Error: pile radius is less than or equal to 0 for pile index : " + str(pile_index+1))
            sys.exit(1)

        # check meshing in z direction
        if pile["nz"] < 1:
            print("Error: Number of elements in Z direction is less than 1 for pile index : " + str(pile_index+1))
            sys.exit(1)

        # check material properties
        if pile["material"] == "Elastic" and pile["section"] == "No-Section":
            length_mat_props = 6
            if len(pile["mat_props"]) != length_mat_props:
                print("Error: number of material properties is not correct for pile index : " + str(pile_index+1))
                sys.exit(1)
            E   = pile["mat_props"][0]
            A   = pile["mat_props"][1]
            Iy  = pile["mat_props"][2]
            Iz  = pile["mat_props"][3]
            G   = pile["mat_props"][4]
            J   = pile["mat_props"][5]
            try: 
                assert E > 0 and A > 0 and Iy > 0 and Iz > 0 and G > 0 and J > 0
            except: 
                print("Error: material properties are not valid for pile index : " + str(pile_index+1))
                sys.exit(1)
        else:
            print("Error: material " + pile["material"] + " is not implemented yet for pile index : " + str(pile_index+1))
            sys.exit(1)


        # check transformation
        pile_transformation = pile.get("transformation", ["Linear", 0.0, 1.0, 0.0])


        if len(pile_transformation) != 4:
            print("Error: transformation is not valid for pile index : " + str(pile_index+1))
            sys.exit(1)
        
        if pile_transformation[0] not in ["Linear", "linear", "PDelta", "pdelta", "LINEAR", "PDELTA"]:
            print("Error: transformation type is not supported for pile index : " + str(pile_index+1))
            print("Supported transformation types are: Linear, PDelta")
            sys.exit(1)
        
        if not isinstance(pile_transformation[1], (int, float)) \
        or not isinstance(pile_transformation[2], (int, float)) \
        or not isinstance(pile_transformation[3], (int, float)):
            print("Error: transformation direction is not valid for pile index : " + str(pile_index+1))
            sys.exit(1)
        
        transformation_vector = np.array([pile_transformation[1], pile_transformation[2], pile_transformation[3]])
        pile_direction = np.array([pile["x_top"] - pile["x_bot"], pile["y_top"] - pile["y_bot"], pile["z_top"] - pile["z_bot"]])

        # check if the transformation vector is not parallel to the pile direction
        transformation_vector_norm = np.linalg.norm(transformation_vector)
        pile_direction_norm = np.linalg.norm(pile_direction)
        mult = transformation_vector_norm * pile_direction_norm
        tol = 1e-6
        if transformation_vector_norm < tol or pile_direction_norm < tol:
            print("Error: transformation vector or pile direction is zero for pile index : " + str(pile_index+1))
            sys.exit(1)
        cos_theta = np.dot(transformation_vector, pile_direction) / mult
        if np.abs(np.abs(cos_theta) - 1.0) < tol:
            print("Error: transformation vector is parallel to the pile direction for pile index : " + str(pile_index+1))
            print(pile_transformation)
            print(transformation_vector)
            print(pile_direction)
            sys.exit(1)



    # check the structure_info
    if structure_info["x_min"] >= structure_info["x_max"] or \
    structure_info["y_min"] >= structure_info["y_max"] or \
    structure_info["z_min"] >= structure_info["z_max"]:
        print("Error: structure x_min is greater than or equal to x_max or y_min is greater than or equal to y_max or z_min is greater than or equal to z_max")
        sys.exit(1)
    if len(structure_info["columns_base"]) < 1:
        print("Error: No columns defined in the structure_info")
        sys.exit(1)
    for col_index, col in enumerate(structure_info["columns_base"]):
        if col["x"] < structure_info["x_min"] or col["x"] > structure_info["x_max"] or \
        col["y"] < structure_info["y_min"] or col["y"] > structure_info["y_max"] or \
        col["z"] < structure_info["z_min"] or col["z"] > structure_info["z_max"]:
            print("Error: column x, y, or z location is out of structure bounds for column index : " + str(col_index+1))
            sys.exit(1)
    if structure_info["num_partitions"] < 1:
        print("Error: Number of partitions is less than 1 in structure_info")
        sys.exit(1)
    if structure_info["num_partitions"] > 1:
        print("Right now only one partition is supported for the structure ")
        sys.exit(1)

    # check that the structure bounds are within the soil profile bounds
    if structure_info["x_min"] < soil_info["x_min"] or \
    structure_info["x_max"] > soil_info["x_max"] or \
    structure_info["y_min"] < soil_info["y_min"] or \
    structure_info["y_max"] > soil_info["y_max"] or \
    structure_info["z_min"] < Z_MIN :
        print("Error: structure bounds are out of soil profile bounds")
        sys.exit(1)

    for col_index, col in enumerate(structure_info["columns_base"]):
        z = col["z"] - foundation_info.get("column_embedment_depth")
        x = col["x"]
        y = col["y"]
        foundation_found = False

        for foundation in foundation_info["foundation_profile"]:
            if x > foundation["x_min"] and x < foundation["x_max"] and \
            y > foundation["y_min"] and y < foundation["y_max"] :
                if z < foundation["z_top"] and z > foundation["z_bot"]:
                    foundation_found = True
                    break

        if not foundation_found:
            print("Error: column base is not within any foundation for column index : " + str(col_index+1))
            sys.exit(1)


        

                
            



    # ============================================================================
    # Create the foundation mesh
    # =============================================================================
    foundation_mesh = pv.MultiBlock()
    tolerance = 1e-4

    # Using meshlib to create the foundation mesh with boolean operations
    # The reason is that pyvista boolean operations are not robust enough for this purpose sorry :))))

    if len(foundation_info["foundation_profile"]) == 0:
        print("Error: No foundation defined in the foundation_info")
        sys.exit(1)
    elif len(foundation_info["foundation_profile"]) == 1:
        x_min = foundation_info["foundation_profile"][0]["x_min"]
        x_max = foundation_info["foundation_profile"][0]["x_max"]
        y_min = foundation_info["foundation_profile"][0]["y_min"]   
        y_max = foundation_info["foundation_profile"][0]["y_max"]
        z_top = foundation_info["foundation_profile"][0]["z_top"]
        z_bot = foundation_info["foundation_profile"][0]["z_bot"]
        dx = foundation_info["dx"]
        dy = foundation_info["dy"]
        dz = foundation_info["dz"]
        if x_min >= x_max or y_min >= y_max or z_top <= z_bot:
            print("Error: foundation x_min is greater than or equal to x_max or y_min is greater than or equal to y_max or z_top is less than or equal to z_bot")
            sys.exit(1)
        nx = max(1, int((x_max - x_min) / dx))
        ny = max(1, int((y_max - y_min) / dy))
        nz = max(1, int((z_top - z_bot) / dz))
        if nx < 1 or ny < 1 or nz < 1:
            print("Error: Number of elements in X, Y, or Z direction is less than 1")
            sys.exit(1)
        x = np.linspace(x_min, x_max, nx+1)
        y = np.linspace(y_min, y_max, ny+1)
        z = np.linspace(z_bot, z_top, nz+1)
        xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
        mesh = pv.StructuredGrid(xx, yy, zz)
        mesh = mesh.cast_to_unstructured_grid()
    else:
        for foundation_index, foundation in enumerate(foundation_info["foundation_profile"]):
            ran_num = np.random.rand() * 4.0 + 1.0
            f_x_min = foundation["x_min"] - tolerance * ran_num
            f_x_max = foundation["x_max"] + tolerance * ran_num
            f_y_min = foundation["y_min"] - tolerance * ran_num
            f_y_max = foundation["y_max"] + tolerance * ran_num
            f_z_top = foundation["z_top"] + tolerance * ran_num
            f_z_bot = foundation["z_bot"] - tolerance * ran_num

            
            # check if the foundation dimensions are valid
            if f_x_min >= f_x_max or f_y_min >= f_y_max or f_z_top <= f_z_bot:
                print("Error: foundation x_min is greater than x_max or y_min is greater than y_max or z_top is less than z_bot for foundation index : " + str(foundation_index+1))
                sys.exit(1)

            if foundation["material"] not in foundation_supported_materials:
                print("Error: material " + foundation["material"] + " is not supported for foundation index : " + str(foundation_index+1))
                sys.exit(1)
            

            # check material properties
            if foundation["material"] == "Elastic":
                length_mat_props = 3
                if len(foundation["mat_props"]) != length_mat_props:
                    print("Error: number of material properties is not correct for foundation index : " + str(foundation_index+1))
                    sys.exit(1)
                E   = foundation["mat_props"][0]
                nu  = foundation["mat_props"][1]
                rho = foundation["mat_props"][2]
                try: 
                    assert E > 0 and nu >= 0 and nu < 0.5 and rho > 0
                except: 
                    print("Error: material properties are not valid for foundation index : " + str(foundation_index+1))
                    sys.exit(1)
            else:
                print("Error: material " + foundation["material"] + " is not implemented yet for foundation index : " + str(foundation_index+1))
                sys.exit(1)

            # check damping
            if foundation.get("damping", "No-Damping") not in foundation_supported_dampings:
                print("Error: damping " + foundation["damping"] + " is not supported for foundation index : " + str(foundation_index+1))
                print("Supported dampings are: ", foundation_supported_dampings)
                sys.exit(1)

            if foundation.get("damping", "No-Damping") == "Frequency-Rayleigh":
                length_damping_props = 3
                if len(foundation["damping_props"]) != length_damping_props:
                    print("Error: number of damping properties is not correct for foundation index : " + str(foundation_index+1))
                    sys.exit(1)
                xi_s = foundation["damping_props"][0]
                f1   = foundation["damping_props"][1]
                f2   = foundation["damping_props"][2]
                try: 
                    assert xi_s >= 0 and xi_s < 1 and f1 > 0 and f2 > f1
                except:
                    print("Error: damping properties are not valid for foundation index : " + str(foundation_index+1))
                    sys.exit(1)
            elif foundation.get("damping", "No-Damping") == "No-Damping":
                pass
            else:
                print("Error: damping " + foundation["damping"] + " is not implemented yet for foundation index : " + str(foundation_index+1))
                sys.exit(1)


            # check if the foundation is above the soil profile z_min
            if f_z_bot < Z_MIN:
                print("Error: foundation z_bot is less than soil profile z_min for foundation index : " + str(foundation_index+1))
                sys.exit(1)

            dx = f_x_max - f_x_min
            dy = f_y_max - f_y_min
            dz = f_z_top - f_z_bot
            if foundation_index == 0:
                foundation_mesh = mr.makeCube(size=mr.Vector3f(dx,dy,dz), base=mr.Vector3f(f_x_min,f_y_min,f_z_bot))
            else:
                cube = mr.makeCube(size=mr.Vector3f(dx,dy,dz), base=mr.Vector3f(f_x_min,f_y_min,f_z_bot))
                foundation_mesh = mr.boolean(foundation_mesh, cube, operation=mr.BooleanOperation.Union)
                if not foundation_mesh.valid():
                    print("Error: Boolean union operation failed for foundation index : " + str(foundation_index+1))
                    sys.exit(1)
                foundation_mesh = foundation_mesh.mesh    

        # now convert the meshlib mesh to pyvista mesh
        # vertices
        verts = np.array([
            list(foundation_mesh.points[mr.VertId(i)])
            for i in range(foundation_mesh.points.size())
        ])

        # faces (triangles)
        tris = []
        for f in foundation_mesh.topology.getValidFaces():
            v0, v1, v2 = foundation_mesh.topology.getTriVerts(f)
            tris.append([3, int(v0), int(v1), int(v2)])  # VTK format

        # --- Create PyVista PolyData ---
        faces = np.array(tris).flatten()
        mesh = pv.PolyData(verts, faces)


        # voxelize the mesh to 
        # mesh.voxelize() is deprecated in pyvista since version 0.46.0: The `voxelize` filter has been moved to `DataSetFilters`.
        if float(pv.__version__[0:4]) < 0.46:
            mesh = pv.voxelize(mesh, density=(foundation_info["dx"], 
                                            foundation_info["dy"], 
                                            foundation_info["dz"]))
        else:
            mesh = pv.DataSetFilters.voxelize(mesh, 
                                            spacing=(foundation_info["dx"], 
                                                    foundation_info["dy"], 
                                                    foundation_info["dz"]))
            # mesh = pv.DataSetFilters.voxelize_rectilinear(mesh, 
            #                                   spacing=(foundation_info["dx"], 
            #                                            foundation_info["dy"], 
            #                                            foundation_info["dz"]))
            # mesh = mesh.cast_to_unstructured_grid()


        # TODO: Verify the voxelization is correct
        # Convert voxel cells -> hexahedron cells
        # starting conversion ......

        ugrid_voxel = mesh.cast_to_unstructured_grid()
        points = ugrid_voxel.points

        cells = []
        for i in range(ugrid_voxel.n_cells):
            ids = ugrid_voxel.get_cell(i).point_ids
            # Remap voxel node ordering to hexahedron ordering
            voxel_to_hex = [0, 1, 3, 2, 4, 5, 7, 6]
            hex_ids = [ids[j] for j in voxel_to_hex]
            cells.append([8] + hex_ids)

        cells = np.hstack(cells)
        celltypes = np.full(ugrid_voxel.n_cells, pv.CellType.HEXAHEDRON, dtype=np.uint8)

        # Build new unstructured grid with HEXAHEDRON cells
        mesh = pv.UnstructuredGrid(cells, celltypes, points)

    # ... conversion done

    mesh.clear_data()
    mesh.cell_data["mesh_ind"] = np.arange(mesh.n_cells, dtype=int)
    # mesh.plot(show_edges=True, opacity=1.0, scalars="mesh_ind")
    # exit()




    # extract largest connected region
    foundation_mesh = pv.MultiBlock()
    while mesh.n_cells > 0:
        largest = mesh.extract_largest()
        foundation_mesh.append(largest)
        mesh = mesh.extract_values(largest.cell_data["mesh_ind"] , invert=True, scalars="mesh_ind")


    # foundation_mesh.plot(show_edges=True, opacity=1.0, multi_colors=True)
    foundation_mesh.clear_all_data()

    # iterate through each foundation and assign material properties
    tolerance = 1e-3
    for block_index, block in enumerate(foundation_mesh):
        block.cell_data["foundation_index"] = np.full(block.n_cells, -1, dtype=int)
        for foundation_index, foundation in enumerate(foundation_info["foundation_profile"]):
            f_x_min = foundation["x_min"]
            f_x_max = foundation["x_max"] 
            f_y_min = foundation["y_min"] 
            f_y_max = foundation["y_max"] 
            f_z_top = foundation["z_top"]  
            f_z_bot = foundation["z_bot"]

            # find the cells that are within the foundation bounds
            # cell_centers = block.cell_centers().points
            # in_x = np.logical_and(cell_centers[:,0] >= f_x_min, cell_centers[:,0] <= f_x_max)
            # in_y = np.logical_and(cell_centers[:,1] >= f_y_min, cell_centers[:,1] <= f_y_max)
            # in_z = np.logical_and(cell_centers[:,2] >= f_z_bot, cell_centers[:,2] <= f_z_top)
            # in_foundation = np.logical_and(np.logical_and(in_x, in_y), in_z)

            block_points = block.points
            in_x = np.logical_and(block_points[:,0] >= f_x_min, block_points[:,0] <= f_x_max)
            in_y = np.logical_and(block_points[:,1] >= f_y_min, block_points[:,1] <= f_y_max)
            in_z = np.logical_and(block_points[:,2] >= f_z_bot, block_points[:,2] <= f_z_top)
            in_foundation = np.logical_and(np.logical_and(in_x, in_y), in_z)
            in_foundation = block.extract_points(in_foundation, 
                                                adjacent_cells=True, 
                                                include_cells=True)
            if in_foundation.n_cells < 1:
                continue
            in_foundation = in_foundation.cell_data["vtkOriginalCellIds"]
            
            # assign the foundation index to the cells that are within the foundation bounds
            block.cell_data["foundation_index"][in_foundation] = foundation_index

            # remove all the cells that are not assigned to any foundation
        mask = block.cell_data["foundation_index"] != -1
        foundation_mesh[block_index] = block.extract_cells(mask)



    # check that if each foundation has at least one pile
    for foundation_index, foundation in enumerate(foundation_mesh):
        foundation_has_pile = False
        for pile in pile_info["pile_profile"]:
            # foundation.find_cells_along_line(pointa)
            # ind = foundation.find_cells_intersecting_line(
            #     pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
            #     pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
            #     tolerance=1e-3
            # )
            ind = foundation.find_cells_along_line(
                pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
                pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
                tolerance=pile["r"]
            )
            if len(ind) > 0:
                # debug ploting 
                # pl = pv.Plotter()
                # line = pv.Line(pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
                #                pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
                #                resolution=1)
                # pl.add_mesh(line, color="red", line_width=5)
                # pl.add_mesh(foundation, style='wireframe', color="blue", line_width=1)
                # pl.add_mesh(foundation.extract_cells(ind), color="green", opacity=0.5)
                # pl.show()
                foundation_has_pile = True
                break
        
        if not foundation_has_pile:
            print("Error: foundation index " + str(foundation_index+1) + " does not have any pile to support it.")
            print("Please add at least one pile that intersects with the foundation.")
            print("Foundation bounds: x_min = " + str(foundation.bounds[0]) + ", x_max = " + str(foundation.bounds[1]) +
                ", y_min = " + str(foundation.bounds[2]) + ", y_max = " + str(foundation.bounds[3]) +
                ", z_min = " + str(foundation.bounds[4]) + ", z_max = " + str(foundation.bounds[5]))
            # debug ploting
            # pl = pv.Plotter()
            # pl.add_mesh(foundation, style='wireframe', color="blue", line_width=1)
            # lines = pv.MultiBlock()
            # for pile in pile_info["pile_profile"]:
            #     line = pv.Line(pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
            #                    pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
            #                    resolution=1)
            #     lines.append(line)
            # pl.add_mesh(lines, color="red", line_width=5)
            # pl.add_axes()
            # pl.add_bounding_box()
            # pl.show_grid()
            # pl.show()
            sys.exit(1)



    foundation_mesh = foundation_mesh.combine(merge_points=True,
                                            tolerance=1e-3,)

    # debugging info
    # foundation_mesh.plot(show_edges=True, opacity=1.0, scalars="foundation_index")
    # print("Number of foundation cells: ", foundation_mesh.n_cells)
    # print("Number of foundation points: ", foundation_mesh.n_points)
    # print("cell_data: ", foundation_mesh.cell_data.keys())
    # print("point_data: ", foundation_mesh.point_data.keys())

    # adding bounds to the foundation info
    foundation_info["x_min"] = foundation_mesh.bounds[0]
    foundation_info["x_max"] = foundation_mesh.bounds[1]
    foundation_info["y_min"] = foundation_mesh.bounds[2]
    foundation_info["y_max"] = foundation_mesh.bounds[3]
    foundation_info["z_min"] = foundation_mesh.bounds[4]
    foundation_info["z_max"] = foundation_mesh.bounds[5]



    # ============================================================================
    # Creating the soil mesh
    # ============================================================================
    soil_mesh = pv.MultiBlock()

    for layer_index, layer in enumerate(soil_info["soil_profile"]):
        x_min = soil_info["x_min"]
        x_max = soil_info["x_max"]
        y_min = soil_info["y_min"]
        y_max = soil_info["y_max"]

        z_bot = layer["z_bot"]
        z_top = layer["z_top"]

        nx = soil_info["nx"]
        ny = soil_info["ny"]    
        nz = layer["nz"]

        # Check if the layer dimensions are valid
        if x_min >= x_max or y_min >= y_max or z_top <= z_bot:
            print("Error: soil layer x_min is greater than x_max or y_min is greater than y_max or z_top is less than z_bot for layer index : " + str(layer_index+1))
            sys.exit(1)

        x = np.linspace(x_min, x_max, nx+1)
        y = np.linspace(y_min, y_max, ny+1)
        z = np.linspace(z_bot, z_top, nz+1)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        grid = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        grid.cell_data["layer_index"] = np.full(grid.n_cells, layer_index, dtype=int)
        soil_mesh.append(grid)
        

    soil_mesh = soil_mesh.combine(merge_points=True, tolerance=1e-3,)



    soil_mesh = pv.UnstructuredGrid(soil_mesh)

    # find the points that are inside the foundation and remove them from the soil mesh
    tolerance = 1e-4
    if foundation_info["embedded"]:
        x_max = foundation_info["x_max"] - tolerance
        x_min = foundation_info["x_min"] + tolerance
        y_max = foundation_info["y_max"] - tolerance
        y_min = foundation_info["y_min"] + tolerance 
        z_max = foundation_info["z_max"] + tolerance
        z_min = foundation_info["z_min"] - tolerance
        points = soil_mesh.points

        # mask inside the foundation bounds
        mask = np.logical_and.reduce((
            points[:,0] >= x_min, points[:,0] <= x_max,
            points[:,1] >= y_min, points[:,1] <= y_max, 
            points[:,2] >= z_min, points[:,2] <= z_max
        ))
        cells = soil_mesh.extract_points(mask, 
                                            adjacent_cells=True,
                                            include_cells=True  
                                            ).cell_data["vtkOriginalCellIds"]
        soil_mesh = soil_mesh.extract_cells(cells, invert=True)
    else:
        # raise error of not implemented yet
        print("Error: foundation is not embedded in the soil. This option is not implemented yet.")
        sys.exit(1)



    # check that if each pile intersects with the soil mesh
    for pile_index, pile in enumerate(pile_info["pile_profile"]):
        ind = soil_mesh.find_cells_intersecting_line(
            pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
            pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
            tolerance=1e-3
        )
        # debug ploting
        # if len(ind) > 0:
        #     pl = pv.Plotter()
        #     line = pv.Line(pointa=[pile["x_top"], pile["y_top"], pile["z_top"]],
        #                    pointb=[pile["x_bot"], pile["y_bot"], pile["z_bot"]],
        #                    resolution=1)
        #     pl.add_mesh(line, color="red", line_width=5)
        #     pl.add_mesh(soil_mesh, style='wireframe', color="blue", line_width=1)
        #     pl.add_mesh(soil_mesh.extract_cells(ind), color="green", opacity=0.5)
        #     pl.add_axes()
        #     pl.show_grid()
        #     pl.show()


        if len(ind) < 1:
            print("Error: pile index " + str(pile_index+1) + " does not intersect with the soil mesh.")
            print("Please check the pile coordinates and soil profile bounds.")
            sys.exit(1)
        


    # ============================================================================
    # building the femora model
    # ============================================================================
    # building the femora model

    # building the soil sections
    soil_sections = []
    for layer_index, layer in enumerate(soil_info["soil_profile"]):
        layer_mesh = soil_mesh.extract_cells(soil_mesh.cell_data["layer_index"] == layer_index)

        if layer_mesh.n_cells < 1:
            # warning message
            print("Warning: soil layer index " + str(layer_index+1) + " does not have any cells.")
            continue


        # create material
        material = layer["material"]
        mat_props = layer["mat_props"]


        if material == "Elastic":
            E   = mat_props[0]
            nu  = mat_props[1]
            rho = mat_props[2]
            mat = fm.material.nd.elastic_isotropic(user_name="Soil_Layer_" + str(layer_index+1),
                                            E=E, nu=nu, rho=rho)
        else:
            print("Error: material " + material + " is not implemented yet for soil layer index : " + str(layer_index+1))
            sys.exit(1)
        

        # create the element
        elem = fm.element.brick.std(ndof=3, 
                                    material=mat,
                                    b1=soil_info["gravity_x"]*rho,
                                    b2=soil_info["gravity_y"]*rho,
                                    b3=soil_info["gravity_z"]*rho)
        
        damping = layer["damping"]
        damping_props = layer["damping_props"]
        if damping == "No-Damping":
            damp = None
        elif damping == "Frequency-Rayleigh":
            xi_s = damping_props[0]
            f1   = damping_props[1]
            f2   = damping_props[2]
            damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=f1, f2=f2)
        reg = fm.region.create_region("elementRegion", damping=damp)

        fm.meshPart.create_mesh_part("General mesh", "External mesh",
                            user_name=f"SoilLayer_{layer_index+1}",
                            element=elem,
                            region=reg,
                            mesh=layer_mesh)
        soil_sections.append(f"SoilLayer_{layer_index+1}")



    # building the foundation sections
    foundation_sections = []
    for foundation_index, foundation_block in enumerate(foundation_info["foundation_profile"]):
        layer_mesh = foundation_mesh.extract_cells(foundation_mesh.cell_data["foundation_index"] == foundation_index)
        if layer_mesh.n_cells < 1:
            # warning message
            print("Warning: foundation index " + str(foundation_index+1) + " does not have any cells.")
            continue
        # create material
        material = foundation_block["material"]
        mat_props = foundation_block["mat_props"]
        if material == "Elastic":
            E   = mat_props[0]
            nu  = mat_props[1]
            rho = mat_props[2]
            mat = fm.material.nd.elastic_isotropic(user_name="Foundation_" + str(foundation_index+1),
                                            E=E, nu=nu, rho=rho)
        else:
            print("Error: material " + material + " is not implemented yet for foundation index : " + str(foundation_index+1))
            sys.exit(1)
        
        # create the element
        elem = fm.element.brick.std(ndof=3, 
                                    material=mat,
                                    b1=foundation_info["gravity_x"]*rho,
                                    b2=foundation_info["gravity_y"]*rho,
                                    b3=foundation_info["gravity_z"]*rho)
        damping = foundation_block.get("damping", "No-Damping")
        if damping == "No-Damping":
            damp = None
        elif damping == "Frequency-Rayleigh":
            damping_props = foundation_block.get("damping_props", [])
            xi_s = damping_props[0]
            f1   = damping_props[1]
            f2   = damping_props[2]
            damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=f1, f2=f2)
        else:
            print("Error: damping " + damping + " is not implemented yet for foundation index : " + str(foundation_index+1))
            sys.exit(1)
        reg = fm.region.create_region("elementRegion", damping=damp)
        fm.meshPart.create_mesh_part("General mesh", "External mesh",
                            user_name=f"Foundation_{foundation_index+1}",
                            element=elem,
                            region=reg,
                            mesh=layer_mesh)
        foundation_sections.append(f"Foundation_{foundation_index+1}")


    # building the pile sections
    pile_sections = []
    for pile_index, pile in enumerate(pile_info["pile_profile"]):
        # create the pile mesh
        x_top = pile["x_top"]
        y_top = pile["y_top"]
        z_top = pile["z_top"]
        x_bot = pile["x_bot"]
        y_bot = pile["y_bot"]
        z_bot = pile["z_bot"]
        nz    = pile["nz"]
        r     = pile["r"]

        if nz >=1 and nz < 3:
            print("Warning: Number of elements in Z direction is less than 3 for pile index : " + str(pile_index+1))
        

        # create the section
        section_type = pile["section"]
        material = pile["material"]
        mat_props = pile["mat_props"]

        transformation = pile.get("transformation", ["Linear", 0.0, 1.0, 0.0])
        transf = fm.transformation.transformation3d(
            transf_type=transformation[0],
            vecxz_x=transformation[1],
            vecxz_y=transformation[2],
            vecxz_z=transformation[3],
            description="PileTransformation_" + str(pile_index+1)
        )


        if material == "Elastic" and section_type == "No-Section":
            length_mat_props = 6
            if len(mat_props) != length_mat_props:
                print("Error: number of material properties is not correct for pile index : " + str(pile_index+1))
                sys.exit(1)
            E   = mat_props[0]
            A   = mat_props[1]
            Iy  = mat_props[2]
            Iz  = mat_props[3]
            G   = mat_props[4]
            J   = mat_props[5]
            try: 
                assert E > 0 and A > 0 and Iy > 0 and Iz > 0 and G > 0 and J > 0
            except: 
                print("Error: material properties are not valid for pile index : " + str(pile_index+1))
                sys.exit(1)
            pile_section = fm.section.elastic(
                user_name="PileSection_" + str(pile_index+1),
                E=E, A=A, Iy=Iy, Iz=Iz, G=G, J=J
            )
        else:
            print("Error: material " + material + " or section " + section_type + " is not implemented yet for pile index : " + str(pile_index+1))
            sys.exit(1)

        pile_ele = fm.element.beam.disp(
        ndof=6,
        section=pile_section,
        transformation=transf,
        numIntgrPts=5,
        )
        pile_mesh_part = fm.mesh_part.line.single_line(
        user_name="Pile_" + str(pile_index+1),
        element=pile_ele,
        region=None,
        x0=x_bot, y0=y_bot, z0=z_bot,
        x1=x_top, y1=y_top, z1=z_top,
        number_of_lines = nz,
        merge_points = True,
        )
        pile_sections.append("Pile_" + str(pile_index+1))  


    # interface elements between piles and soil
    for pile_index, pile in enumerate(pile_info["pile_profile"]):
        radius = pile["r"]
        n_p = pile_info["pile_interface"]["num_points_on_perimeter"]
        n_l = pile_info["pile_interface"]["num_points_along_length"]
        pp = pile_info["pile_interface"]["penalty_parameter"]
        fm.interface.beam_solid_interface(
            name = "Pile-Solid_Interface_" + str(pile_index+1),
            beam_part = "Pile_" + str(pile_index+1),
            solid_parts = None,  # No solid part specified
            radius = radius,  # Interface radius
            n_peri = n_p,
            n_long = n_l,
            penalty_param = pp,  # Penalty parameter
            g_penalty = True,  # Use geometric penalty
            write_connectivity = True,
            write_interface = True,  # Write interface file
        )



    # create the columns base sections
    base_column_sections = []
    column_sections = []
    for col_index, col in enumerate(structure_info["columns_base"]):
        x = col["x"]
        y = col["y"]
        z = col["z"]
        z_top = z
        z_bot = z - foundation_info.get("column_embedment_depth")
        transformation = ["Linear", 0.0, 1.0, 0.0]
        transf = fm.transformation.transformation3d(
                    transf_type=transformation[0],
                    vecxz_x=transformation[1],
                    vecxz_y=transformation[2],
                    vecxz_z=transformation[3],
                    description="ColumnBaseTransformation_" + str(col_index+1)  
                )
        E  = foundation_info["column_section_props"]["E"]
        A  = foundation_info["column_section_props"]["A"]
        Iy = foundation_info["column_section_props"]["Iy"]
        Iz = foundation_info["column_section_props"]["Iz"]
        G  = foundation_info["column_section_props"]["G"]
        J  = foundation_info["column_section_props"]["J"]
        try:
            assert E > 0 and A > 0 and Iy > 0 and Iz > 0 and G > 0 and J > 0
        except:
            print("Error: column section properties are not valid")
            sys.exit(1)
        column_section = fm.section.elastic(
                user_name="columnSection_" + str(col_index+1),
                E=E, A=A, Iy=Iy, Iz=Iz, G=G, J=J
            )
        column_sections.append(column_section)
        column_ele = fm.element.beam.disp(
            ndof=6,
            section=column_section,
            transformation=transf,
            numIntgrPts=3,
        )
        column_mesh_part = fm.mesh_part.line.single_line(
            user_name="BaseColumn_" + str(col_index+1),
            element=column_ele,
            region=None,
            x0=x, y0=y, z0=z_bot,
            x1=x, y1=y, z1=z_top,
            number_of_lines = 1,
            merge_points = True,
        )
        base_column_sections.append("BaseColumn_" + str(col_index+1))


    # interface elements between base columns and soil
    for col_index, col in enumerate(structure_info["columns_base"]):
        n_p = 8
        n_l = 6
        pp = pile_info["pile_interface"]["penalty_parameter"]
        radius = 0.1
        fm.interface.beam_solid_interface(
            name = "BaseColumn-Solid_Interface_" + str(col_index+1),
            beam_part = "BaseColumn_" + str(col_index+1),
            solid_parts = None,  # No solid part specified  
            radius = radius,  # Interface radius
            n_peri = n_p,
            n_long = n_l,
            penalty_param = pp,  # Penalty parameter
            g_penalty = True,  # Use geometric penalty
            write_connectivity = True,
            write_interface = True,  # Write interface file
        )

    # ============================================================================    
    # Assembling the model
    # ============================================================================
    foundation_pile_sections = pile_sections + foundation_sections + base_column_sections
    fm.assembler.create_section(foundation_pile_sections, 
                                num_partitions=foundation_info["num_partitions"],
                                partition_algorithm="kd-tree",
                                merging_points=True,
                                tolerance=1e-3,
                                mass_merging="sum")

    fm.assembler.create_section(soil_sections, 
                                num_partitions=soil_info["num_partitions"],
                                partition_algorithm="kd-tree",
                                merging_points=True,
                                tolerance=1e-3,
                                mass_merging="sum")


    fm.assembler.Assemble(merge_points=False)


    # %%
    # ============================================================================
    # set the start tags to push the numberings
    fm.material.set_material_tag_start(20000)
    fm.transformation.set_start_tag(30000)
    fm.section.set_start_tag(40000)
    fm.damping.set_start_tag(45000)


    # node tag start and element tag start
    fm.MeshMaker().set_nodetag_start(500000)
    fm.MeshMaker().set_eletag_start( 600000)
    fm.MeshMaker().set_start_core_tag(structure_info.get("num_partitions"))
    # ============================================================================
    # boundary conditions
    # ============================================================================
    # find Z_min and Z_max from the soil profile by comparing all the layers
    if soil_info["boundary_conditions"] == "periodic": 
        z_min = np.inf
        z_max = -np.inf
        for layer in soil_info["soil_profile"]:
            if layer["z_bot"] < z_min:
                z_min = layer["z_bot"]
            if layer["z_top"] > z_max:
                z_max = layer["z_top"]

        z_min = z_min + 5e-2  # adding a small tolerance
        fm.constraint.mp.create_laminar_boundary(bounds=(z_min, z_max),
                                                dofs=[1,2,3], 
                                                direction=3)
        fm.constraint.sp.fixMacroZmin(dofs=[1,1,1],
                                    tol=1e-3)
    elif soil_info["boundary_conditions"] == "DRM":

        fm.drm.addAbsorbingLayer(numLayers=soil_info["DRM_options"].get("number_of_layers"),
                            numPartitions=soil_info["DRM_options"].get("num_partitions"),
                            partitionAlgo="kd-tree",
                            geometry="Rectangular",
                            rayleighDamping=soil_info["DRM_options"].get("Rayleigh_damping"),
                            matchDamping=soil_info["DRM_options"].get("match_damping", False),
                            type=soil_info["DRM_options"].get("absorbing_layer_type", "Rayleigh")
                            )
        dofsVals = [1,1,1,1,1,1,1,1,1]
        fm.constraint.sp.fixMacroXmax(dofs=dofsVals)
        fm.constraint.sp.fixMacroXmin(dofs=dofsVals)
        fm.constraint.sp.fixMacroYmax(dofs=dofsVals)
        fm.constraint.sp.fixMacroYmin(dofs=dofsVals)
        fm.constraint.sp.fixMacroZmin(dofs=dofsVals)


    # ============================================================================
    # plotting
    # ============================================================================
    # if plotting true retun the soil, foundation and pile mesh
    if plotting:
        mesh =fm.assembler.get_mesh()
        pile_mesh_tags = [fm.meshPart.get_mesh_part(name).tag for name in pile_sections]
        foundation_mesh_tags = [fm.meshPart.get_mesh_part(name).tag for name in foundation_sections]
        soil_mesh_tags = [fm.meshPart.get_mesh_part(name).tag for name in soil_sections]
        MeshTag = fm.assembler.AssembeledMesh.cell_data["MeshPartTag_celldata"]
        pile_mesh = mesh.extract_cells(np.isin(MeshTag, pile_mesh_tags))
        foundation_mesh = mesh.extract_cells(np.isin(MeshTag, foundation_mesh_tags))
        soil_mesh = mesh.extract_cells(np.isin(MeshTag, soil_mesh_tags))
        return pile_mesh, foundation_mesh, soil_mesh
        # return pile_mesh, foundation_mesh, soil_mesh

    # ============================================================================
    # actions and analysis
    # ============================================================================
    # gravity analysis
    newmark_gamma = 0.6
    newnark_beta = (newmark_gamma + 0.5)**2 / 4
    elastic_update = fm.actions.updateMaterialStageToElastic()
    dampNewmark = fm.analysis.integrator.newmark(gamma=newmark_gamma, beta=newnark_beta)
    gravity_elastic = fm.actions.tcl("""
if {$pid == 0} {puts [string repeat "=" 120] }
if {$pid == 0} {puts "Starting analysis : defualtTransient_gravity_elastic"}
if {$pid == 0} {puts [string repeat "=" 120] }
constraints  Penalty 1.e12 1.e12
numberer ParallelRCM
system Mumps -ICNTL14 400 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test EnergyIncr 0.001 20 2
integrator Newmark 0.6 0.30250000000000005
analysis Transient
set AnalysisStep 0
while { $AnalysisStep < 30} {
	if {$pid==0} {puts "$AnalysisStep/30"}
	set Ok [analyze 1 1.0]
	incr AnalysisStep 1
}
wipeAnalysis"""
)

    plastic_update = fm.actions.updateMaterialStageToPlastic()
    gravity_plastic = fm.actions.tcl("""
if {$pid == 0} {puts [string repeat "=" 120] }
if {$pid == 0} {puts "Starting analysis : defualtTransient_gravity_plastic"}
if {$pid == 0} {puts [string repeat "=" 120] }
constraints Penalty 1.e12 1.e12
numberer ParallelRCM
system Mumps -ICNTL14 400 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test EnergyIncr 0.001 20 2
integrator Newmark 0.6 0.30250000000000005
analysis Transient
set AnalysisStep 0
while { $AnalysisStep < 100} {
	if {$pid==0} {puts "$AnalysisStep/100"}
	set Ok [analyze 1 0.01]
	incr AnalysisStep 1
}
wipeAnalysis
setTime 0.0
""")


    # defind a tcl action that will be used to create the conncetions between the piles 
    # and the foundation after the gravity analysis

    # TODO: implement the tcl action to create the connections between the piles and the foundation
    tcl_command = """
proc Femora_getNodeCoordFrom {structureCores embeddedCore nTag secTag eleTag enTag} {
    if {$::pid == $embeddedCore || $::pid < $structureCores} {
		if {$::pid == $embeddedCore} {
			set tmpTags [getNodeTags]
			if {[lsearch -exact $tmpTags $nTag] >= 0} {
				#eval "element zeroLengthSection $eleTag $nTag $enTag $secTag -orient 0 0 1 1 0 0"
                eval "equalDOF $nTag $enTag 1 2 3 4 5 6"
				puts "Created element $eleTag $enTag $nTag $secTag in pid $::pid"
				return
			} 
		}


        if {$::pid <  $structureCores} {
            set tmpTags [getNodeTags]
            if {[lsearch -exact $tmpTags $nTag] >= 0} {
                set coords [nodeCoord $nTag]
                puts "Found node $nTag at $coords from pid $::pid"
                send -pid 1 "$coords"
            } else {
                send -pid 1 "None"
            }
        } else {
            for {set i 0} {$i < $structureCores} {incr i} {
                recv -pid $i ANY tmpcoord
                if {$tmpcoord != "None"} {set coord $tmpcoord}
            }
        }

        if {$::pid == $embeddedCore} {
            puts "received coord $coord for node $nTag in pid $::pid"
			eval "node $nTag $coord -ndf 6"
			#eval "element zeroLengthSection $eleTag $nTag $enTag $secTag -orient 0 0 1 1 0 0"
            equalDOF $nTag $enTag 1 2 3 4 5 6
			puts "Created node $nTag and connected to $enTag in pid $::pid"
        }
        if {$::pid < $structureCores} {
            set tmpTags [getNodeTags]
            if {[lsearch -exact $tmpTags $nTag] >= 0} {
                set coords [nodeCoord $nTag]
                eval "node $enTag $coords -ndf 6"
                equalDOF $nTag $enTag 1 2 3 4 5 6
                puts "Created node $enTag and connected to $nTag in pid $::pid"
            }
        }
	}
}
"""
    # loop over the base columns
    for col_index, col in enumerate(structure_info["columns_base"]):
        col_coord = np.array([col["x"], col["y"], col["z"]])
        col_tag = col["tag"]
        name = "BaseColumn_" + str(col_index+1)
        mesh_part = fm.meshPart.get_mesh_part(name)
        if mesh_part is None:
            print("Error: mesh part " + name + " not found.")
            sys.exit(1)
        mesh_part_tag = mesh_part.tag
        mesh_part_cells = fm.assembler.AssembeledMesh.cell_data["MeshPartTag_celldata"] == mesh_part_tag
        mesh_part_cell  = np.where(mesh_part_cells)[0]
        mesh_part_points = []
        for cell_id in mesh_part_cell:
            mesh_part_points.append(fm.assembler.AssembeledMesh.get_cell(cell_id).point_ids)
        mesh_part_points = np.unique(np.hstack(mesh_part_points))
        # find the point with the minimum z value and maximum z value
        points = fm.assembler.AssembeledMesh.points[mesh_part_points]
        z_min_index = np.argmin(points[:,2])
        z_max_index = np.argmax(points[:,2])
        z_min_point = points[z_min_index]
        z_max_point = points[z_max_index]

        # find the z_min_index and z_max_index in the original mesh
        z_min_index = mesh_part_points[z_min_index]
        z_max_index = mesh_part_points[z_max_index]

        z_min_index = z_min_index + fm._instance._start_nodetag
        z_max_index = z_max_index + fm._instance._start_nodetag

        # print(f"Column {col_index+1}: z_min_point = {z_min_point}, z_max_point = {z_max_point}")
        # print(f"Column {col_index+1}: column = {col}")

        # verify that the z_max_point is close to the column coordinates by np allclose
        if not np.allclose(z_max_point, col_coord, atol=1e-2):
            print("Error: column " + str(col_index+1) + " top point is not close to the column coordinates.")
            print("Column top point: ", z_max_point)
            print("Column coordinates: ", col_coord)
            sys.exit(1)


        connection_core = fm.assembler.AssembeledMesh.cell_data["Core"][mesh_part_cell]
        connection_core = np.unique(connection_core)
        if len(connection_core) > 1:
            print("Error: column " + str(col_index+1) + " is spanning multiple cores. This is not supported yet.")
            sys.exit(1)

        connection_core = np.unique(connection_core)[0]
        connection_core += fm._instance._start_core_tag
        tcl_command += f"set tmpTag [expr [getFemoraMax eleTag] + 1]\n"
        tcl_command += f"Femora_getNodeCoordFrom {structure_info.get('num_partitions')} {connection_core} {col_tag} {column_sections[col_index].tag} $tmpTag {z_max_index}\n\n"

        # tcl_command += f"""if {{$pid <= {connection_core}}} """ + "{\n"
        # tcl_command += f"\tif {{$pid <  {connection_core}}} """ + "{\n"

        # tcl_command += f"\tnode {col_tag} {" ".join([str(coord) for coord in col_coord])} -ndf 6\n"
        # tcl_command += f"\telement zeroLengthSection $tmpTag {z_max_index} {col_tag} {column_sections[col_index].tag} -orient 0 0 1 1 0 0\n"
        # tcl_command += f"\tputs \"Created connection between column base node {col_tag} and embedded node {z_max_index}\"\n"
        # tcl_command += "}\n"
        # tcl_command += "barrier\n\n"

        
    connection = fm.actions.tcl(tcl_command)



    # ============================================================================
    # strucutre tcl 
    # ============================================================================
    structure_file = structure_info.get("model_file", None)
    if EEUQ:
        print(os.getcwd())
        structure_file = os.path.basename(structure_file) 
    structure_numpartitions = structure_info.get("num_partitions")
    if structure_file is not None:
        try:
            with open(structure_file, 'r') as sf:
                structure_data = sf.read()
            structure_data = "\n".join(["\t" + line for line in structure_data.splitlines()])
            structure_tcl = "if {$pid < %d} {\n" % structure_numpartitions
            structure_tcl += structure_data
            structure_tcl += "\n}\n"
            structure_tcl_action = fm.actions.tcl(structure_tcl)
            del structure_data 
            del structure_tcl
        except Exception as e:
            print(f"Error reading structure file {structure_file}: {e}")
            sys.exit(1)
    else:
        print("Error: structure model file is not provided.")
        sys.exit(1)
    

    # ============================================================================
    # recorder
    recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="result.vtkhdf",
                                            resp_types=["stress3D6", "disp"], 
                                            delta_t=0.001)

    # ============================================================================
    # 
    tmptcl = fm.actions.tcl("""
# =======================================================================================
# Uniform Excitation (Northridge record) ======================================
# Time Series ======================================
timeSeries Path 10 -dt 0.0127 -filePath Northridge.acc -factor -9.81
pattern UniformExcitation 10 1 -accel 10


# Recorder ======================================

recorder vtkhdf Results/result$pid.vtkhdf -dT 0.02 stress3D6 disp




# Reset pseudo time ======================================
setTime 0.0


# Dynamic Analysis Step ======================================

if {$pid == 0} {puts [string repeat "=" 120] }
if {$pid == 0} {puts "Starting analysis : dyn"}
if {$pid == 0} {puts [string repeat "=" 120] }
constraints Penalty 1.e12 1.e12
numberer ParallelRCM
system Mumps -ICNTL14 400 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test NormDispIncr 0.001 5 2 2
integrator Newmark 0.5 0.25
analysis Transient
set dt 0.0127


set endTime 50.0
set baseDt $dt

while {[getTime] < $endTime} {
    if {$pid == 0} {puts "Time : [getTime]"}
    set ok [analyze 1 $dt]
}
""")
    
    # =============================================================================
    # process
    # =============================================================================
    fm.process.add_step(structure_tcl_action, description="Import structure model from tcl file")
    fm.process.add_step(connection,      description="Create connections between base columns and foundation")
    fm.process.add_step(elastic_update,  description="Update material to elastic")
    fm.process.add_step(gravity_elastic, description="Gravity analysis in elastic regime")
    fm.process.add_step(plastic_update,  description="Update material to plastic")
    fm.process.add_step(gravity_plastic, description="Gravity analysis in plastic regime")
    # fm.process.add_step(recorder,        description="Recorder")
    # fm.process.add_step(tmptcl,          description="Dynamic analysis with ground motion")
    # fm.process.add_step(fm.actions.tcl("exit"), description="Exit")





    # =============================================================================
    # exporting the model to tcl
    # =============================================================================
    # model_filename = "tmpmodel.tcl"
    import tqdm
    bar = tqdm.tqdm(total=100, 
                    desc="Exporting model to tcl", 
                    bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [" "{elapsed}<{remaining}] {postfix}",)

    def progress_callback(progress, message):
        value = int(progress)
        bar.set_postfix_str(message)
        bar.n = value
        bar.refresh()
        if value >= 100:
            bar.close()
            print("Model exported to " + model_filename)


        


    if fm.assembler.AssembeledMesh is None:
        print("Error: Assembled mesh is None. Cannot export the model.")
        sys.exit(1)
    from femora.components.event.event_bus import EventBus, FemoraEvent
    from femora.components.Element.elementBase import Element

    self = fm._instance
    with open(model_filename, 'w') as f:
        # Inform interfaces that we are about to export
        EventBus.emit(FemoraEvent.PRE_EXPORT, 
                    file_handle=f, 
                    assembled_mesh=fm.assembler.AssembeledMesh)

        # f.write("wipe\n")
        f.write("model BasicBuilder -ndm 3\n")
        f.write("set pid [getPID]\n")
        f.write("set np [getNP]\n")

        if self._results_folder != "":
            f.write("if {$pid == 0} {" + f"file mkdir {self._results_folder}" + "} \n")

        f.write("barrier\n")
        f.write("\n# Helper functions ======================================\n")
        f.write(self._get_tcl_helper_functions())

        # Write the meshBounds
        f.write("\n# Mesh Bounds ======================================\n")
        bounds = self.assembler.AssembeledMesh.bounds
        f.write(f"set X_MIN {bounds[0]}\n")
        f.write(f"set X_MAX {bounds[1]}\n")
        f.write(f"set Y_MIN {bounds[2]}\n")
        f.write(f"set Y_MAX {bounds[3]}\n")
        f.write(f"set Z_MIN {bounds[4]}\n")
        f.write(f"set Z_MAX {bounds[5]}\n")

        if progress_callback:
            progress_callback(0, "writing materials")


        # Write the materials
        f.write("\n# Materials ======================================\n")
        for tag,mat in self.material.get_all_materials().items():
            f.write(f"{mat.to_tcl()}\n")


        # write the transformations
        f.write("\n# Transformations ======================================\n")
        for transf in self.transformation.get_all_transformations():
            f.write(f"{transf.to_tcl()}\n")


        # Write the sections
        f.write("\n# Sections ======================================\n")
        for tag,section in self.section.get_all_sections().items():
            f.write(f"{section.to_tcl()}\n")



        # Write the nodes
        f.write("\n# Nodes & Elements ======================================\n")
        cores = self.assembler.AssembeledMesh.cell_data["Core"]
        num_cores = np.unique(cores)
        nodes     = self.assembler.AssembeledMesh.points
        ndfs      = self.assembler.AssembeledMesh.point_data["ndf"]
        mass      = self.assembler.AssembeledMesh.point_data["Mass"]
        num_nodes = self.assembler.AssembeledMesh.n_points
        wroted    = np.zeros((num_nodes, len(num_cores)), dtype=bool) # to keep track of the nodes that have been written
        nodeTags  = np.arange(self._start_nodetag,
                            self._start_nodetag + num_nodes,
                            dtype=int)
        eleTags   = np.arange(self._start_ele_tag,
                            self._start_ele_tag + self.assembler.AssembeledMesh.n_cells,
                            dtype=int)


        elementClassTag = self.assembler.AssembeledMesh.cell_data["ElementTag"]


        for i in range(self.assembler.AssembeledMesh.n_cells):
            cell = self.assembler.AssembeledMesh.get_cell(i)
            pids = cell.point_ids
            core = cores[i]
            f.write("if {$pid ==" + str(core + self._start_core_tag) + "} {\n")
            # writing nodes
            for pid in pids:
                if not wroted[pid][core]:
                    f.write(f"\tnode {nodeTags[pid]} {nodes[pid][0]} {nodes[pid][1]} {nodes[pid][2]} -ndf {ndfs[pid]}\n")
                    mass_vec = mass[pid]
                    mass_vec = mass_vec[:ndfs[pid]] 
                    # if any of the mass vector is not zero then write it
                    if abs(mass_vec).sum() > 1e-6:
                        f.write(f"\tmass {nodeTags[pid]} {' '.join(map(str, mass_vec))}\n")
                    # write them mass for that node
                    wroted[pid][core] = True
            
            eleclass = Element._elements[elementClassTag[i]]
            nodeTag = [nodeTags[pid] for pid in pids]
            eleTag = eleTags[i]
            f.write("\t"+eleclass.to_tcl(eleTag, nodeTag) + "\n")
            f.write("}\n")     
            if progress_callback:
                progress_callback((i / self.assembler.AssembeledMesh.n_cells) * 45 + 5, "writing nodes and elements")
        
        # notify EmbbededBeamSolidInterface event
        EventBus.emit(FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, 
                    file_handle=f, 
                    ele_start_tag=self._start_ele_tag) 
        
        if progress_callback:
            progress_callback(50, "writing dampings")
        # write the dampings 
        f.write("\n# Dampings ======================================\n")
        if self.damping.get_all_dampings() is not None:
            for tag,damp in self.damping.get_all_dampings().items():
                f.write(f"{damp.to_tcl()}\n")
        else:
            f.write("# No dampings found\n")

        # write regions
        f.write("\n# Regions ======================================\n")
        Regions = np.unique(self.assembler.AssembeledMesh.cell_data["Region"])
        for i,regionTag in enumerate(Regions):
            region = self.region.get_region(regionTag)
            if region.get_type().lower() == "noderegion":
                raise ValueError(f"""Region {regionTag} is of type NodeTRegion which is not supported in yet""")
            
            region.setComponent("element", eleTags[self.assembler.AssembeledMesh.cell_data["Region"] == regionTag])
            f.write(f"{region.to_tcl()} \n")
            del region
            if progress_callback:
                progress_callback((i / Regions.shape[0]) * 10 + 55, "writing regions")


        # Write mp constraints
        f.write("\n# mpConstraints ======================================\n")

        # Precompute mappings
        core_to_idx = {core: idx for idx, core in enumerate(num_cores)}
        master_nodes = np.zeros(num_nodes, dtype=bool)
        slave_nodes = np.zeros(num_nodes, dtype=bool)
        
        # Modified data structures to handle multiple constraints per node
        constraint_map = {}  # map master node to list of constraints
        constraint_map_rev = {}  # map slave node to list of (master_id, constraint) tuples
        
        for constraint in self.constraint.mp:
            master_id = constraint.master_node - self._start_nodetag
            master_nodes[master_id] = True
            
            # Add constraint to master's list
            if master_id not in constraint_map:
                constraint_map[master_id] = []
            constraint_map[master_id].append(constraint)
            
            # For each slave, record the master and constraint
            for slave_id in constraint.slave_nodes:
                slave_id = slave_id - self._start_nodetag
                slave_nodes[slave_id] = True
                
                if slave_id not in constraint_map_rev:
                    constraint_map_rev[slave_id] = []
                constraint_map_rev[slave_id].append((master_id, constraint))

        # Get mesh data
        cells = self.assembler.AssembeledMesh.cell_connectivity
        offsets = self.assembler.AssembeledMesh.offset

        for core_idx, core in enumerate(num_cores):
            # Get elements in current core
            eleids = np.where(cores == core)[0]
            if eleids.size == 0:
                continue
            
            # Get all nodes in this core's elements
            starts = offsets[eleids]
            ends = offsets[eleids + 1]
            core_node_indices = np.concatenate([cells[s:e] for s, e in zip(starts, ends)])
            in_core = np.isin(np.arange(num_nodes), core_node_indices)
            
            # Find active masters and slaves in this core
            active_masters = np.where(master_nodes & in_core)[0]
            active_slaves = np.where(slave_nodes & in_core)[0]

            # Add the master nodes that are not in the core but needed for constraints
            masters_to_add = []
            for slave_id in active_slaves:
                if slave_id in constraint_map_rev:
                    for master_id, _ in constraint_map_rev[slave_id]:
                        masters_to_add.append(master_id)
            
            # Add unique masters
            if masters_to_add:
                active_masters = np.concatenate([active_masters, np.array(masters_to_add)])
                active_masters = np.unique(active_masters)

            if not active_masters.size:
                continue

            f.write(f"if {{$pid == {core + self._start_core_tag}}} {{\n")
            
            # Process all master nodes that are not in the current core
            valid_mask = ~in_core[active_masters]
            valid_masters = active_masters[valid_mask]
            if valid_masters.size > 0:
                f.write("\t# Master nodes not defined in this core\n")
                for master_id in valid_masters:
                    node = nodes[master_id]
                    f.write(f"\tnode {master_id+self._start_nodetag} {node[0]} {node[1]} {node[2]} -ndf {ndfs[master_id]}\n")

            # Process all slave nodes that are not in the current core
            # Collect all unique slave nodes from active master nodes' constraints
            all_slaves = []
            for master_id in active_masters:
                for constraint in constraint_map[master_id]:
                    all_slaves.extend([sid - self._start_nodetag for sid in constraint.slave_nodes])
            
            # Filter out slave nodes that are not in the current core
            valid_slaves = np.array([sid for sid in all_slaves if 0 <= sid < num_nodes and not in_core[sid]])
            
            if valid_slaves.size > 0:
                f.write("\t# Slave nodes not defined in this core\n")
                for slave_id in np.unique(valid_slaves):
                    node = nodes[slave_id]
                    f.write(f"\tnode {slave_id+self._start_nodetag} {node[0]} {node[1]} {node[2]} -ndf {ndfs[slave_id]}\n")

            # Write constraints after nodes
            f.write("\t# Constraints\n")
            
            # Process constraints where master is in this core
            for master_id in active_masters:
                for constraint in constraint_map[master_id]:
                    f.write(f"\t{constraint.to_tcl()}\n")
            
            f.write("}\n")

            if progress_callback:
                progress = 65 + (core_idx + 1) / len(num_cores) * 15
                progress_callback(min(progress, 80), "writing constraints")


        # write sp constraints
        f.write("\n# spConstraints ======================================\n")
        size = len(self.constraint.sp)
        indx = 1
        for constraint in self.constraint.sp:
            f.write(f"{constraint.to_tcl()}\n")
            if progress_callback:
                progress_callback(80 + indx / size * 5, "writing sp constraints")
            indx += 1


        # write time series
        f.write("\n# Time Series ======================================\n")
        size = len(self.timeSeries)
        indx = 1
        for timeSeries in self.timeSeries:
            f.write(f"{timeSeries.to_tcl()}\n")
            if progress_callback:
                progress_callback(85 + indx / size * 5, "writing time series")
            indx += 1
        
        # write process
        f.write("\n# Process ======================================\n")
        indx = 1
        size = len(self.process)
        f.write(f"{self.process.to_tcl()}\n")
        

        if progress_callback:
            progress_callback(100, "finished exporting model")


    # return the number of cores the mode needs
    num_cores = max(self.assembler.AssembeledMesh.cell_data["Core"])
    num_cores += structure_info.get("num_partitions", 1)
    num_cores += 1  # to account for zero indexing
    print(f"Model requires at least {num_cores} cores to run.")
    return num_cores







    # # ============================================================================
    # # ploting each core separately
    # # ============================================================================
    # mesh = fm.assembler.get_mesh()
    # cores = np.unique(mesh.cell_data["Core"])
    # print("Number of cores: ", len(cores))
    # print("Number of cells: ", mesh.n_cells)
    # print("Number of points: ", mesh.n_points)
    # # for core in cores:
    # #     pl = pv.Plotter()
    # #     part = mesh.extract_cells(mesh.cell_data["Core"] == core)
    # #     pl.add_mesh(part, show_edges=True, opacity=1.0, scalars="Core", multi_colors=True)
    # #     pl.add_mesh(mesh, style='wireframe', color="black", line_width=1, opacity=0.1)
    # #     pl.show(title="Core " + str(core))

    # center = np.array(mesh.center)
    # assmesh = fm.assembler.get_mesh()
    # mesh = pv.MultiBlock()
    # for core in cores:
    #     part = assmesh.extract_cells(assmesh.cell_data["Core"] == core)
    #     # Move points away from the part center to create an exploded view (previous repeat caused shape mismatch)
    #     vec = (part.center - center) * 2
    #     vec = vec / np.linalg.norm(vec) * 10  # Normalize and scale
    #     # vec[:2] = 0  # Only move in the Z direction
    #     part.points += vec
    #     mesh.append(part)

    # mesh.plot(show_edges=True, 
    #         opacity=1.0, 
    #         scalars="Core",
    #         multi_colors=True, 
    #         style="surface", 
    # )


    # strucure_mesh   = structure_info.get("mesh_file", None)
    # if strucure_mesh is not None:
    #     structure_part = pv.read(strucure_mesh)
    #     pl = pv.Plotter()
    #     pl.add_mesh(structure_part, style='wireframe', color="black", line_width=3, opacity=1.0)
    #     pl.add_mesh(fm.assembler.AssembeledMesh, show_edges=True, opacity=1.0, scalars="Core", multi_colors=True)
    #     pl.show(title="Structure and Soil")
    





    # fm.assembler.plot(show_edges=True, 
    #                 opacity=1.0, 
    #                 scalars="Core",
    #                 multi_colors=True, 
    #                 style="surface", 
    #                 explode=False, 
    #                 explode_factor=0.3,
    #                 render_lines_as_tubes=False,
    #                 sperate_beams_solid=True,
    #                 opacity_beams=1.0, 
    #                 opacity_solids=0.7,
    #                 tube_radius=5.0,
    #                 show_cells_by_type=False,
    #                 cells_to_show=[pv.CellType.LINE],
    #                 show_grid=True
    #                 )


if __name__ == "__main__":
    # ============================================================================
    # Input parameters
    # =============================================================================
    # structure information
    structure_info = {
        "num_partitions": 1,
        "x_min": 0.,
        "y_min": 0.,
        "z_min": 0.,
        "x_max": 45.72,
        "y_max": 45.72,
        "z_max": 40.8432,
        "columns_base":[
            {"tag":101, "x":0.00000, "y":0.00000,   "z":0.0 },
            {"tag":102, "x":9.14400, "y":0.00000,   "z":0.0 },
            {"tag":103, "x":18.28800, "y":0.00000,  "z":0.0 },
            {"tag":104, "x":27.43200, "y":0.00000,  "z":0.0 },
            {"tag":105, "x":36.57600, "y":0.00000,  "z":0.0 },
            {"tag":106, "x":45.72000, "y":0.00000,  "z":0.0 },
            {"tag":107, "x":0.00000, "y":9.14400,   "z":0.0 },
            {"tag":108, "x":9.14400, "y":9.14400,   "z":0.0 },
            {"tag":109, "x":18.28800, "y":9.14400,  "z":0.0 },
            {"tag":110, "x":27.43200, "y":9.14400,  "z":0.0 },
            {"tag":111, "x":36.57600, "y":9.14400,  "z":0.0 },
            {"tag":112, "x":45.72000, "y":9.14400,  "z":0.0 },
            {"tag":113, "x":0.00000, "y":18.28800,  "z":0.0 },
            {"tag":114, "x":9.14400, "y":18.28800,  "z":0.0 },
            {"tag":115, "x":18.28800, "y":18.28800, "z":0.0 },
            {"tag":116, "x":27.43200, "y":18.28800, "z":0.0 },
            {"tag":117, "x":36.57600, "y":18.28800, "z":0.0 },
            {"tag":118, "x":45.72000, "y":18.28800, "z":0.0 },
            {"tag":119, "x":0.00000, "y":27.43200,  "z":0.0 },
            {"tag":120, "x":9.14400, "y":27.43200,  "z":0.0 },
            {"tag":121, "x":18.28800, "y":27.43200, "z":0.0 },
            {"tag":122, "x":27.43200, "y":27.43200, "z":0.0 },
            {"tag":123, "x":36.57600, "y":27.43200, "z":0.0 },
            {"tag":124, "x":45.72000, "y":27.43200, "z":0.0 },
            {"tag":125, "x":0.00000, "y":36.57600,  "z":0.0 },
            {"tag":126, "x":9.14400, "y":36.57600,  "z":0.0 },
            {"tag":127, "x":18.28800, "y":36.57600, "z":0.0 },
            {"tag":128, "x":27.43200, "y":36.57600, "z":0.0 },
            {"tag":129, "x":36.57600, "y":36.57600, "z":0.0 },
            {"tag":130, "x":45.72000, "y":36.57600, "z":0.0 },
            {"tag":131, "x":0.00000, "y":45.72000,  "z":0.0 },
            {"tag":132, "x":9.14400, "y":45.72000,  "z":0.0 },
            {"tag":133, "x":18.28800, "y":45.72000, "z":0.0 },
            {"tag":134, "x":27.43200, "y":45.72000, "z":0.0 },
            {"tag":135, "x":36.57600, "y":45.72000, "z":0.0 },
            {"tag":136, "x":45.72000, "y":45.72000, "z":0.0 },
        ],  
        "column_embedment_depth":0.3, # embedment depth of the columns in the foundation
        "model_file":r"C:\Users\aminp\OneDrive\Desktop\DRMGUI\src\femora\components\simcenter\eeuq\steel_frame.tcl",  
        "column_section_props":{
            "E": 200e9,    # Elastic Modulus
            "A": 1.0,     # Area
            "Iy": 8.333e-6, # Moment of Inertia Iy
            "Iz": 8.333e-6, # Moment of Inertia Iz
            "G": 79.3e9,   # Shear Modulus
            "J": 1.666e-5   # Moment of Inertia J
        }
    }


    # soil information from bottom to top
    soil_info = {
        "x_min": -25.,
        "x_max":  65.,
        "y_min": -25.,
        "y_max":  65.,
        "nx": 45,
        "ny": 45,
        "gravity_x": 0.0,
        "gravity_y": 0.0,
        "gravity_z": -9.81,
        "num_partitions": 8,
        "boundary_conditions": "periodic", # could be "DRM" 
        "DRM_options": {
            "absorbing_layer_type": "PML",  # could be "PML" or "Rayleigh" 
            "num_partitions": 8,
            "number_of_layers": 5,
            "Rayleigh_damping": 0.95,
            "match_damping": False, # if true the Rayleigh damping will be matched to the soil damping
        },
        "soil_profile" : [
        {"z_bot":-10, "z_top":-7, "nz":2, 
        "material":"Elastic", "mat_props":[30e6, 0.3, 18], "damping":"Frequency-Rayleigh", "damping_props":[0.05, 3, 15]
        },
        {"z_bot":-7,  "z_top":-4, "nz":4, 
        "material":"Elastic", "mat_props":[50e6, 0.3, 19], "damping":"Frequency-Rayleigh", "damping_props":[0.05, 3, 15]
        },
        {"z_bot":-4,  "z_top":-1, "nz":6, 
        "material":"Elastic", "mat_props":[70e6, 0.3, 20], "damping":"Frequency-Rayleigh", "damping_props":[0.05, 3, 15]
        },
        {"z_bot":-1,  "z_top":0,  "nz":3, 
        "material":"Elastic", "mat_props":[90e6, 0.3, 21], "damping":"Frequency-Rayleigh", "damping_props":[0.05, 3, 15]
        },       
        ]
    }


    # foundation information
    foundation_info = {
        "gravity_x": 0.0,
        "gravity_y": 0.0,
        "gravity_z": -9.81, 
        "embedded" : True,  # if the foundation is embedded in the soil or not True/False.
        "dx": 2.0,          # mesh size in x direction
        "dy": 2.0,          # mesh size in y direction
        "dz": 2.0,          # mesh size in z direction
        "gravity_x": 0.0,
        "gravity_y": 0.0,
        "gravity_z": -9.81,
        "num_partitions": 4,
        "foundation_profile" : [
            {"x_min":-5, "x_max":50, "y_min":-5, 
            "y_max":50,  "z_top":0,    "z_bot":-1.2, 
            "material":"Elastic", "mat_props":[30e6, 0.3, 18] 
            },
        ]
    }


    # pile information
    pile_info = {
        "pile_profile" : [
            {
                "x_top": -2.5 , "y_top": -2.5 , "z_top":0,
                "x_bot": -2.5 , "y_bot": -2.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 22.5 , "y_top": -2.5 , "z_top":0,
                "x_bot": 22.5 , "y_bot": -2.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 47.5 , "y_top": -2.5 , "z_top":0,
                "x_bot": 47.5 , "y_bot": -2.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": -2.5 , "y_top": 22.5 , "z_top":0,
                "x_bot": -2.5 , "y_bot": 22.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 22.5 , "y_top": 22.5 , "z_top":0,
                "x_bot": 22.5 , "y_bot": 22.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6],
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 47.5 , "y_top": 22.5 , "z_top":0,
                "x_bot": 47.5 , "y_bot": 22.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": -2.5 , "y_top": 47.5 , "z_top":0,
                "x_bot": -2.5 , "y_bot": 47.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 22.5 , "y_top": 47.5 , "z_top":0,
                "x_bot": 22.5 , "y_bot": 47.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6], 
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
            {
                "x_top": 47.5 , "y_top": 47.5 , "z_top":0,
                "x_bot": 47.5 , "y_bot": 47.5 , "z_bot":-7,
                "nz": 50 ,"r":0.2, "section": "No-Section", 
                "material":"Elastic", 
                "mat_props":[30e6, 2, 3,3, 3e6, 6],
                "transformation": ["Linear", 0.0, 1.0, 0.0]
            },
        ],

        "pile_interface": {
            "num_points_on_perimeter": 8,   # number of points on the perimeter of the pile interface
            "num_points_along_length": 3,   # number of points along the length of the pile interface
            "penalty_parameter": 1.0e12
        },
    }



