import numpy as np
def compute_field_from_source_to_point(source_x, source_z, target_x, target_z, wavelength, E0, phi0):
    dx = target_x - source_x
    dz = target_z - source_z
    r = np.sqrt(dx**2 + dz**2)
    r[r < 1e-12] = 1e-12
    k = 2 * np.pi / wavelength
    return (E0 / r) * np.exp(-1j * (k * r - phi0))

def propagate_from_slits_to_screen(slit_x, slit_amplitude, slit_phase, screen_x, z_screen, wavelength):
    dx = screen_x[np.newaxis, :] - slit_x[:, np.newaxis]
    r = np.sqrt(dx**2 + z_screen**2)
    k = 2 * np.pi / wavelength
    amp = slit_amplitude[:, np.newaxis] / r
    phase = slit_phase[:, np.newaxis]
    return amp * np.exp(-1j * (k * r - phase))