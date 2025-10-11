import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
colors = [(0.050980392156862744, 0.16078431372549018, 0.4666666666666666, 1.0), (0.9784313725490196, 0.12137254901960784, 0.301960784313724, 1.0), (0.0, 0.2784313725490196, 0.10588235294117643, 1.0), (0.615686274509804, 0.27450980392156865, 0.0, 1.0), (0.5147058823529411, 0.141078431372549, 0.38431372549019527, 1.0), (0.025490196078431372, 0.2196078431372549, 0.28627450980392155, 1.0), (0.33333333333333337, 0.21764705882352942, 0.2333333333333333, 1.0), (0.4892156862745098, 0.19990196078431371, 0.2039215686274502, 1.0), (0.7970588235294118, 0.19794117647058823, 0.150980392156862, 1.0), (0.307843137254902, 0.27647058823529413, 0.052941176470588214, 1.0)]
mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)
import os 
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Set the working directory to the script's location

def ricker_pulse(t, A_ricker=100e3, f_ricker=5, t0=1.0):
    """
    Compute the Ricker pulse function.
    
    Parameters:
    t (float or array): Time variable (in seconds)
    A_ricker (float): Amplitude of the Ricker pulse (default 100 kN = 100e3 N)
    f_ricker (float): Frequency of the Ricker pulse (default 5 Hz)
    t0 (float): Time shift (default 1.0 s)
    
    Returns:
    float or array: The Ricker pulse value(s) at time(s) t
    """
    tau = t - t0
    return A_ricker * (1 - (2 * np.pi * f_ricker * tau)**2) * np.exp(-(np.pi * f_ricker * tau)**2)

# Generate time range and compute Ricker pulse
t = np.linspace(0, 2, 1000)
u = ricker_pulse(t,t0=.5)

# Create the figure
fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=300)  # 6x4 inches, 300 DPI for publication quality

# Plot the Ricker pulse
ax.plot(t, u, '-o', linewidth=0.5, label=r'Ricker Pulse', markersize=1)
timeFile = "LoadTime.txt"
forceFile = "LoadForce.txt"
np.savetxt(timeFile, t)
np.savetxt(forceFile, u)


# Customize labels, title, and grid
ax.set_xlabel(r'Time (s)', fontsize=12, fontweight='bold',fontname="Times New Roman")
ax.set_ylabel(r'Force (N)', fontsize=12, fontweight='bold',fontname="Times New Roman")
ax.grid(True, linestyle='--', alpha=0.7)


# Adjust tick labels for consistency
ax.tick_params(axis='both', which='major', labelsize=10)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Times New Roman")

# Add legend
ax.legend(fontsize=10, frameon=True, facecolor='white', edgecolor='black')

# Ensure tight layout
plt.tight_layout()



# # Save the figure in PGF format (for direct LaTeX import) and PNG
# plt.savefig('ricker_pulse_pgf.pgf', format='pgf', bbox_inches='tight', dpi=300)
# plt.savefig('ricker_pulse.png', format='png', bbox_inches='tight', dpi=300)

# Display the plot
# Save the figure in PGF format (for direct LaTeX import), PNG, and PDF
plt.savefig('ricker_pulse.pdf', format='pdf', bbox_inches='tight')
plt.show()


# %%

