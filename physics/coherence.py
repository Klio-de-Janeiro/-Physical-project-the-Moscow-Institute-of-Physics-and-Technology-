import numpy as np
from config.defaults import PHYSICAL_CONSTANTS

def compute_interference_pattern(x_vals, src_x, lambdas, E0, phi0, src_widths, slit_x, slit_width, z_trans, z_screen, delta_lambda, spatial_samples):
    lambda_mean = np.mean(lambdas) if len(lambdas) else 550e-9
    L_c = (lambda_mean**2) / (delta_lambda + 1e-12) if delta_lambda > 0 else 1e6

    x = np.asarray(x_vals)
    intensity_total = np.zeros_like(x, dtype=np.float64)
    N_src = len(src_x)
    N_slit = len(slit_x)
    slit_x_arr = np.asarray(slit_x)

    for i in range(N_src):
        width = src_widths[i]
        offsets = np.array([0.0]) if width <= 0 else np.linspace(-width/2, width/2, spatial_samples)
        wavelength_i = lambdas[i]
        k = 2 * np.pi / wavelength_i
        src_pos = src_x[i] + offsets[:, np.newaxis]  # (M, 1)

        if N_slit == 0:
            r = np.sqrt((x[np.newaxis, :] - src_pos)**2 + z_screen**2)
            r[r < 1e-12] = 1e-12
            U = (E0[i] / r) * np.exp(-1j * (k * r - phi0[i]))
            intensity_total += np.mean(np.abs(U)**2, axis=0)
            continue

        r_slit = np.sqrt((slit_x_arr[np.newaxis, :] - src_pos)**2 + z_trans**2)
        r_slit[r_slit < 1e-12] = 1e-12
        U_slit = (E0[i] / r_slit) * np.exp(-1j * (k * r_slit - phi0[i]))  # (M, N_slit)

        r_screen = np.sqrt((x[np.newaxis, np.newaxis, :] - slit_x_arr[np.newaxis, :, np.newaxis])**2 + z_screen**2)
        r_screen[r_screen < 1e-12] = 1e-12
        U_screen = U_slit[:, :, np.newaxis] * np.exp(-1j * k * r_screen) / r_screen  # (M, N_slit, N_x)

        if N_slit == 1:
            I = np.mean(np.abs(U_screen[:, 0, :])**2, axis=0)
        elif delta_lambda > 0:
            r1 = np.sqrt((slit_x_arr - src_x[i])**2 + z_trans**2)
            gamma_t = np.exp(-np.pi * ((r1[:, np.newaxis] - r1[np.newaxis, :]) / L_c)**2)
            I = np.zeros_like(x)
            for j1 in range(N_slit):
                I += np.mean(np.abs(U_screen[:, j1, :])**2, axis=0)
                for j2 in range(j1+1, N_slit):
                    I += 2 * np.real(np.mean(U_screen[:, j1, :] * np.conj(U_screen[:, j2, :]), axis=0)) * gamma_t[j1, j2]
        else:
            I = np.mean(np.abs(np.sum(U_screen, axis=1))**2, axis=0)

        intensity_total += I
    return intensity_total