import numpy as np
from scipy.fft import rfft, irfft, rfftfreq
from scipy.special import j0, j1

# ----------------------------
# Medium from Vs, nu, rho
# ----------------------------
def medium_from_Vs_nu_rho(Vs, nu, rho):
    mu = rho * Vs**2
    Vp = Vs * np.sqrt(2.0*(1.0-nu)/(1.0-2.0*nu))
    lam = rho * Vp**2 - 2.0*mu
    return Vp, Vs, rho, lam, mu

# ----------------------------
# Ricker and FFT helpers
# ----------------------------
def ricker_pulse(t, A=100e3, f0=5.0, t0=0.5):
    tau = t - t0
    a = np.pi * f0
    g = np.exp(-(a*tau)**2)
    return A * (1.0 - 2.0*(a*tau)**2) * g

# ----------------------------
# FK kernels for a vertical point load at the free surface
# ----------------------------
def fk_kernels(k, z, w_c, Vp, Vs, rho):
    """
    Returns Gzz(k,z,ω), Grz(k,z,ω) for Lamb's half-space with vertical surface load.
    w_c is *complex* angular frequency (with small positive imaginary part).
    """
    # Avoid division by zero at k=0 by never calling with k=0 exactly.
    alpha, beta = Vp, Vs

    # Vertical slownesses (choose branches with Re(q)>=0)
    q_p = np.sqrt(k**2 - (w_c/alpha)**2)
    q_s = np.sqrt(k**2 - (w_c/beta )**2)
    q_p = np.where(np.real(q_p) < 0, -q_p, q_p)
    q_s = np.where(np.real(q_s) < 0, -q_s, q_s)

    # Rayleigh denominator (free-surface condition)
    Rden = (2.0*k**2 - q_s**2)**2 - 4.0*(k**2)*q_p*q_s

    # Vertical-vertical and radial-vertical Green's kernels in freq-k domain
    Gzz = (1.0/(rho*w_c**2)) * ( ((2.0*k**2 - q_s**2)*np.exp(-q_s*z))/(q_s*Rden)
                                - (2.0*k**2*np.exp(-q_p*z))/(q_p*Rden) )

    Grz = (1j*k/(rho*w_c**2)) * ( (2.0*k**2*np.exp(-q_s*z))/(q_s*Rden)
                                 - ((2.0*k**2 - q_s**2)*np.exp(-q_p*z))/(q_p*Rden) )
    return Gzz, Grz

# ----------------------------
# Main FK solver
# ----------------------------
def halfspace_FK_xyz(
    x, y, z, t,
    Vs, nu, rho,
    A_ricker=100e3, f_ricker=5.0, t0=0.5,
    eta_rel=5e-3,           # small complex shift: ω -> ω (1+i*eta_rel)
    k_panels=600,           # number of k points in [0, kmax]
    kmax_scale=6.0,         # kmax ≈ kmax_scale * ω/β
    use_frequency_window=True  # optional gentle high-freq taper to reduce wrap
):
    """
    Exact semi-analytic FK solution for a vertical point load at the free surface (0,0,0).
    Returns displacement u(t) and acceleration a(t) at (x,y,z), in Cartesian components.
    """
    Vp, Vs, rho, lam, mu = medium_from_Vs_nu_rho(Vs, nu, rho)
    r = float(np.hypot(x, y))

    # Time/Frequency grids
    t = np.asarray(t, dtype=float)
    n = t.size
    dt = t[1] - t[0]
    freqs = rfftfreq(n, dt)
    w = 2.0*np.pi*freqs

    # Source in time & frequency
    F_t = ricker_pulse(t, A=A_ricker, f0=f_ricker, t0=t0)
    F_w = rfft(F_t)

    # Optional gentle high-freq window to suppress tiny FFT wrap
    if use_frequency_window:
        w_cut = w.max()
        roll = 0.15 * w_cut
        taper = 0.5*(1.0 + np.cos(np.clip((w - (w_cut-roll))/roll, 0, 1)*np.pi))
        F_w = F_w * taper

    # Allocate spectra for u_r and u_z (cylindrical components)
    U_r_w = np.zeros_like(F_w, dtype=complex)
    U_z_w = np.zeros_like(F_w, dtype=complex)

    # Precompute Bessel for each k after we build k-grid per frequency
    # Loop frequencies (skip DC; static handled separately if needed)
    for i, wi in enumerate(w):
        if wi == 0.0 or np.abs(F_w[i]) == 0.0:
            continue

        wi_c = wi * (1.0 + 1j*eta_rel)  # complex-shifted frequency

        # Practical k-range; beyond this, integrand is negligible
        kmax = max(kmax_scale * wi / max(Vs, 1e-12), 1e-6)
        ks = np.linspace(0.0, kmax, k_panels + 1)[1:]  # avoid k=0 exactly

        # Kernels
        Gzz, Grz = fk_kernels(ks, z, wi_c, Vp, Vs, rho)

        # Bessel factors (axisymmetric Hankel transform)
        if r == 0.0:
            # J1(0)=0 => ur=0; J0(0)=1 => uz integral has J0=1
            J0 = np.ones_like(ks)
            J1 = np.zeros_like(ks)
        else:
            J0 = j0(ks * r)
            J1 = j1(ks * r)

        # Assemble integrands (include measure k dk)
        integrand_z = J0 * Gzz * ks
        integrand_r = J1 * Grz * ks

        # Composite trapezoid (robust). For speed, you can panel by Bessel zeros.
        Uz_hat = np.trapz(integrand_z, ks) * F_w[i]
        Ur_hat = np.trapz(integrand_r, ks) * F_w[i]

        U_z_w[i] = Uz_hat
        U_r_w[i] = Ur_hat

    # Map cylindrical (u_r,u_z) -> Cartesian (u_x,u_y,u_z) in freq domain
    # Note: at r=0, u_r=0, so u_x=u_y=0 as expected.
    U_x_w = np.zeros_like(U_r_w, dtype=complex)
    U_y_w = np.zeros_like(U_r_w, dtype=complex)
    if r > 0.0:
        cos_theta = x / r
        sin_theta = y / r
        U_x_w = U_r_w * cos_theta
        U_y_w = U_r_w * sin_theta
    # U_z_w is already vertical component

    # Acceleration in frequency domain: \hat a = -ω^2 \hat u
    A_x_w = -(w**2) * U_x_w
    A_y_w = -(w**2) * U_y_w
    A_z_w = -(w**2) * U_z_w

    # Back to time domain
    u_x = irfft(U_x_w, n=n)
    u_y = irfft(U_y_w, n=n)
    u_z = irfft(U_z_w, n=n)
    a_x = irfft(A_x_w, n=n)
    a_y = irfft(A_y_w, n=n)
    a_z = irfft(A_z_w, n=n)

    return {
        "u": np.vstack([u_x, u_y, u_z]),
        "a": np.vstack([a_x, a_y, a_z]),
        "meta": dict(Vp=Vp, Vs=Vs, rho=rho, nu=nu, lam=lam, mu=mu,
                     eta_rel=eta_rel, k_panels=k_panels, kmax_scale=kmax_scale)
    }

# ----------------------------
# Minimal example
# ----------------------------
if __name__ == "__main__":
    # Medium & time grid
    Vs   = 300.0     # m/s
    nu   = 0.3
    rho  = 2000.0    # kg/m^3
    t    = np.linspace(0.0, 2.0, 4000)

    # Receiver (surface, 60 m away on x-axis)
    XY = np.array([[51.0, 0.0, 0.0],
                   [51.0*0.70710, 51.0*0.70710, 0.0],
                   [0.0, 51.0, 0.0]])
    

    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(4, 1, figsize=(10, 6), sharex=True)
    for rec in XY:
        x, y, z = rec
        out = halfspace_FK_xyz(
            x, y, z, t, Vs, nu, rho,
            A_ricker=100e3, f_ricker=5.0, t0=0.5,
            eta_rel=5e-3, k_panels=800, kmax_scale=6.0
        )

        ux, uy, uz = out["u"]
        ax, ay, az = out["a"]

        # calculate ur 
        i_r = np.array([x, y, 0.0])
        # normalize
        r = np.linalg.norm(i_r)
        if r > 0:
            i_r = i_r / r
            ur = ux * i_r[0] + uy * i_r[1]
            ar = ax * i_r[0] + ay * i_r[1]
        # Now plot or save traces as you like
        axs[0].plot(t, ax, label='rec (%.1f, %.1f, %.1f) m' % (x, y, z))
        axs[1].plot(t, ay, label='rec (%.1f, %.1f, %.1f) m' % (x, y, z))
        axs[2].plot(t, az, label='rec (%.1f, %.1f, %.1f) m' % (x, y, z))
        axs[3].plot(t, ar, label='rec (%.1f, %.1f, %.1f) m' % (x, y, z))
    axs[0].set_ylabel('Displacement x (m)')
    axs[1].set_ylabel('Displacement y (m)')
    axs[2].set_ylabel('Displacement z (m)')
    axs[2].set_xlabel('Time (s)')
    for ax in axs:
        ax.legend()
        ax.grid()
    plt.tight_layout()
    plt.show()


        



 