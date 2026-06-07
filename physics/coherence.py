import numpy as np

def compute_interference_pattern(x_vals, src_x, lambdas, E0, phi0, src_widths, slit_x, slit_width, z_trans, z_screen, delta_lambda, spatial_samples):
    x = np.asarray(x_vals)
    N_src = len(src_x)
    N_slit = len(slit_x)
    slit_x_arr = np.asarray(slit_x)

    if N_src == 0:
        return np.zeros_like(x)

    intensity_total = np.zeros_like(x, dtype=np.float64)

    if delta_lambda > 1e-10:
        wl_offsets = np.linspace(-delta_lambda/2, delta_lambda/2, 7)
    else:
        wl_offsets = [0.0]
        
    s_samples = max(1, spatial_samples)

    for wl_off in wl_offsets:
        for s in range(s_samples):
            U_slice = np.zeros(x.shape, dtype=np.complex128)
            
            for i in range(N_src):
                wl = lambdas[i] + wl_off
                k = 2 * np.pi / wl
                
                width = src_widths[i]
                if width <= 1e-6:
                    pos = src_x[i]
                else:
                    offsets = np.linspace(-width/2, width/2, s_samples)
                    pos = src_x[i] + offsets[s]
                    
                E_current = E0[i] / np.sqrt(s_samples)
                
                if N_slit == 0:
                    r = np.sqrt((x - pos)**2 + z_screen**2)
                    U = (E_current / r) * np.exp(-1j * (k * r - phi0[i]))
                    U_slice += U
                else:
                    r_to_slits = np.sqrt((slit_x_arr - pos)**2 + z_trans**2)
                    U_slits = (E_current / r_to_slits) * np.exp(-1j * (k * r_to_slits - phi0[i]))
                    
                    dz = z_screen - z_trans
                    dist_x = x[np.newaxis, :] - slit_x_arr[:, np.newaxis]
                    r_from_slits = np.sqrt(dist_x**2 + dz**2)
                    
                    obliquity = dz / r_from_slits
                    
                    huygens_factor = slit_width / (1j * wl)
                    
                    U_individual_slits = U_slits[:, np.newaxis] * huygens_factor * obliquity * (1 / r_from_slits) * np.exp(-1j * k * r_from_slits)
                    
                    if slit_width > 1e-6:
                        sin_theta = dist_x / r_from_slits
                        beta = k * (slit_width / 2.0) * sin_theta
                        U_individual_slits *= np.sinc(beta / np.pi)
                    
                    U_slice += np.sum(U_individual_slits, axis=0)
            
            intensity_total += np.abs(U_slice)**2 / len(wl_offsets)

    return intensity_total