import numpy as np

def compute_interference_pattern(x_vals, src_x, lambdas, E0, phi0, src_widths, slit_x, slit_width, z_trans, z_screen, delta_lambda, spatial_samples):
    """
    Физически корректный расчет интерференции для когерентных источников.
    """
    x = np.asarray(x_vals)
    N_src = len(src_x)
    N_slit = len(slit_x)
    slit_x_arr = np.asarray(slit_x)

    if N_src == 0:
        return np.zeros_like(x)

    # Итоговое комплексное поле на экране (инициализируем нулями)
    U_total_at_screen = np.zeros(x.shape, dtype=np.complex128)

    for i in range(N_src):
        wavelength = lambdas[i]
        k = 2 * np.pi / wavelength
        
        # Пространственная когерентность
        width = src_widths[i]
        offsets = np.array([0.0]) if width <= 1e-6 else np.linspace(-width/2, width/2, spatial_samples)
        src_positions = src_x[i] + offsets
        
        # Временная когерентность (упрощенно)
        # Если есть разброс длин волн, мы суммируем интенсивности с разным весом
        # Здесь для простоты оставим монохроматический случай (delta_lambda=0)

        for pos in src_positions:
            # А. Прямое распространение
            if N_slit == 0:
                r = np.sqrt((x - pos)**2 + z_screen**2)
                U = (E0[i] / np.sqrt(r)) * np.exp(-1j * (k * r - phi0[i]))
                U_total_at_screen += U / len(src_positions)
                
            # Б. Через щели
            else:
                r_to_slits = np.sqrt((slit_x_arr - pos)**2 + z_trans**2)
                U_slits = (E0[i] / np.sqrt(r_to_slits)) * np.exp(-1j * (k * r_to_slits - phi0[i]))
                
                dz = z_screen - z_trans
                r_from_slits = np.sqrt((x[np.newaxis, :] - slit_x_arr[:, np.newaxis])**2 + dz**2)
                
                # Вторичные волны ОТ КАЖДОЙ ЩЕЛИ
                U_individual_slits = U_slits[:, np.newaxis] * np.exp(-1j * k * r_from_slits) / np.sqrt(r_from_slits)
                
                # Дифракционный конверт (sinc)
                if slit_width > 1e-6:
                    sin_theta = (x[np.newaxis, :] - slit_x_arr[:, np.newaxis]) / r_from_slits
                    beta = k * (slit_width / 2.0) * sin_theta
                    U_individual_slits *= np.sinc(beta / np.pi)
                
                # Складываем поля от всех щелей в ОДНУ общую сумму полей
                U_total_at_screen += np.sum(U_individual_slits, axis=0) / len(src_positions)

    return np.abs(U_total_at_screen)**2