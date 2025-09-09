from femora.components.simcenter.eeuq.custom_building import custom_building
import os 
os.chdir(os.path.dirname(__file__))

# ============================================================================
# Input parameters
# =============================================================================
# structure information
structure_info = {
    "num_partitions": 1,
    "x_min": -13.716,
    "y_min": -13.716,
    "z_min": 0.,
    "x_max": 13.716,
    "y_max": 13.716,
    "z_max": 40.8432,
    "columns_base":[
        {"tag":101, "x":-13.71600, "y":-13.71600,  "z":0.00000 },
        {"tag":102, "x":-4.57200,  "y":-13.71600,  "z":0.00000 },
        {"tag":103, "x":4.57200,   "y":-13.71600,  "z":0.00000 },
        {"tag":104, "x":13.71600,  "y":-13.71600,  "z":0.00000 },
        {"tag":105, "x":-13.71600, "y":-4.57200,   "z":0.00000 },
        {"tag":106, "x":-4.57200,  "y":-4.57200,   "z":0.00000 },
        {"tag":107, "x":4.57200,   "y":-4.57200,   "z":0.00000 },
        {"tag":108, "x":13.71600,  "y":-4.57200,   "z":0.00000 },
        {"tag":109, "x":-13.71600, "y":4.57200,    "z":0.00000 },
        {"tag":110, "x":-4.57200,  "y":4.57200,    "z":0.00000 },
        {"tag":111, "x":4.57200,   "y":4.57200,    "z":0.00000 },
        {"tag":112, "x":13.71600,  "y":4.57200,    "z":0.00000 },
        {"tag":113, "x":-13.71600, "y":13.71600,   "z":0.00000 },
        {"tag":114, "x":-4.57200,  "y":13.71600,   "z":0.00000 },
        {"tag":115, "x":4.57200,   "y":13.71600,   "z":0.00000 },
        {"tag":116, "x":13.71600,  "y":13.71600,   "z":0.00000 },
    ],  
    "column_embedment_depth":0.3, # embedment depth of the columns in the foundation
    "model_file":r"C:\Users\aminp\OneDrive\Desktop\DRMGUI\examples\EEUQ\Example2\steel_frame.tcl", 
    "mesh_file" :r"C:\Users\aminp\OneDrive\Desktop\DRMGUI\examples\EEUQ\Example2\building.vtkhdf",
    "column_section_props":{
        "E": 30e6,    # Elastic Modulus
        "A": 0.282,     # Area
        "Iy": 0.0063585, # Moment of Inertia Iy
        "Iz": 0.0063585, # Moment of Inertia Iz
        "G": 12.5e6,   # Shear Modulus
        "J": 0.012717   # Moment of Inertia J
    }
}


# soil information from bottom to top
soil_info = {
    "x_min": -64,
    "x_max":  64,
    "y_min": -64,
    "y_max":  64,
    "nx": 32,
    "ny": 32,
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
    {"z_bot":-48, "z_top":-40, "nz":2, 
    "material":"Elastic", 
    "mat_props":[2031050.557968521, 0.306925827695258, 2.16275], 
    "damping":"Frequency-Rayleigh", "damping_props":[0.0211, 3, 15]
    },
    {"z_bot":-40,  "z_top":-32, "nz":2, 
    "material":"Elastic", 
    "mat_props":[1762809.8758694725, 0.30694522251297574, 2.1586],
    "damping":"Frequency-Rayleigh", "damping_props":[0.0221, 3, 15]
    },
    {"z_bot":-32,  "z_top":-24, "nz":2, 
    "material":"Elastic", 
    "mat_props":[1495388.2483252182, 0.306974948361342, 2.15445],
    "damping":"Frequency-Rayleigh", "damping_props":[0.0234, 3, 15]
    },
    {"z_bot":-24,  "z_top":-16,  "nz":2, 
    "material":"Elastic", 
    "mat_props":[1229028.6525414723, 0.30699478245814293, 2.15035],
    "damping":"Frequency-Rayleigh", "damping_props":[0.0249, 3, 15]
    },  
    {"z_bot":-16,  "z_top":-8,  "nz":2, 
    "material":"Elastic", 
    "mat_props":[963419.3475957835, 0.3070002901446228, 2.1462],
    "damping":"Frequency-Rayleigh", "damping_props":[0.0269, 3, 15]
    },
    {"z_bot":-8,  "z_top":0,  "nz":2, 
    "material":"Elastic",
    "mat_props":[698103.0346931004, 0.30696660596216024, 2.14205],
    "damping":"Frequency-Rayleigh", "damping_props":[0.0296, 3, 15]  
    }   
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
    "dz": 0.3,          # mesh size in z direction
    "gravity_x": 0.0,
    "gravity_y": 0.0,
    "gravity_z": -9.81,
    "num_partitions": 2,
    "foundation_profile" : [
        {"x_min":-20,  "x_max":20, 
         "y_min":-20,  "y_max":20,  
         "z_top":0,    "z_bot":-1.2, 
        "material":"Elastic", "mat_props":[30e6, 0.2, 2.4] 
        },
    ]
}


# pile information
pile_info = {
    "pile_profile" : [
        {
            "type": "grid",  # could be "grid" or "single"
            "x_start": -10 , "y_start": -10 ,
            "spacing_x": 5 , "spacing_y": 5 ,
            "nx": 5 , "ny": 5 ,
            "z_top": -0.5 , "z_bot": -10 ,
            "nz": 15 ,"r":0.3, "section": "No-Section", 
            "material":"Elastic", 
            "mat_props":[30e6, 0.282, 0.0063585, 0.0063585, 12.5e6, 0.012717], 
            "transformation": ["Linear", 0.0, 1.0, 0.0]
        },
    ],

    "pile_interface": {
        "num_points_on_perimeter": 8,   # number of points on the perimeter of the pile interface
        "num_points_along_length": 4,   # number of points along the length of the pile interface
        "penalty_parameter": 1.0e12
    },
}

custom_building(structure_info, soil_info, foundation_info, pile_info)