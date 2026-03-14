
# %%
import numpy as np
import matplotlib.pyplot as plt
import os
from femora.tools.transferFunction import TransferFunction, TimeHistory
from femora.utils.paths import motions_dir

os.chdir(os.path.dirname(__file__))

_MOTIONS = motions_dir()
record = TimeHistory.load(acc_file=str(_MOTIONS / "ricker_surface.acc"),
                            time_file=str(_MOTIONS / "ricker_surface.time"),
                            unit_in_g=True,
                            gravity=9.81)

soil = [
    {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
]
rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}

# Create transfer function instance
tf = TransferFunction(soil, rock, f_max=50.0)
bedrock = tf._deconvolve(time_history=record)
# save to a txt file ricker_base.acc and ricker_base.time
#  
np.savetxt("ricker_base.acc", bedrock.acceleration, fmt='%.6f')
np.savetxt("ricker_base.time", bedrock.time, fmt='%.6f')
fig = tf.plot_deconvolved_motion(time_history=record)

plt.show()
