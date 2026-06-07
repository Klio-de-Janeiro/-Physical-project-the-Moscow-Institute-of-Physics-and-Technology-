import numpy as np

def calculate_field(x_sources, z_sources, wavelengths, amplitudes, x_screen, z_screen):
   
    dx = x_screen[np.newaxis, :] - x_sources[:, np.newaxis]
    dz = z_screen - z_sources[:, np.newaxis]
    
    r = np.sqrt(dx**2 + dz**2)
    
    k = 2 * np.pi / wavelengths[:, np.newaxis]
    
    fields = (amplitudes[:, np.newaxis] / r) * np.exp(-1j * k * r)
    
    return np.sum(fields, axis=0)