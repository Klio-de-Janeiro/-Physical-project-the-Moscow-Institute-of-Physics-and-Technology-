import numpy as np

def compute_interference_pattern(x_vals, src_x, lambdas, E0, phi0, src_widths, slit_x, slit_width, z_trans, z_screen, delta_lambda, spatial_samples):
    """
    Физически корректный расчет интерференции:
    Все источники складываются когерентно (сумма амплитуд),
    а уширение спектра (delta_lambda) усредняется по интенсивности.
    """
    x = np.asarray(x_vals)
    N_src = len(src_x)
    N_slit = len(slit_x)
    slit_x_arr = np.asarray(slit_x)

    if N_src == 0:
        return np.zeros_like(x)

    intensity_total = np.zeros_like(x, dtype=np.float64)

    # 1. Временная когерентность (усреднение по спектру)
    if delta_lambda > 1e-10:
        # Берем 7 точек спектра от -delta/2 до +delta/2
        wl_offsets = np.linspace(-delta_lambda/2, delta_lambda/2, 7)
    else:
        wl_offsets = [0.0]

    # 2. Для каждой компоненты спектра складываем поля от ВСЕХ источников
    for wl_off in wl_offsets:
        U_slice = np.zeros(x.shape, dtype=np.complex128)
        
        for i in range(N_src):
            wl = lambdas[i] + wl_off
            k = 2 * np.pi / wl
            
            # Пространственная протяженность источника
            width = src_widths[i]
            offsets = np.array([0.0]) if width <= 1e-6 else np.linspace(-width/2, width/2, spatial_samples)
            src_positions = src_x[i] + offsets
            
            for pos in src_positions:
                # Случай А: Без экрана со щелями
                if N_slit == 0:
                    r = np.sqrt((x - pos)**2 + z_screen**2)
                    U = (E0[i] / np.sqrt(r)) * np.exp(-1j * (k * r - phi0[i]))
                    U_slice += U / len(src_positions)
                    
                # Случай Б: С экраном и щелями
                else:
                    r_to_slits = np.sqrt((slit_x_arr - pos)**2 + z_trans**2)
                    U_slits = (E0[i] / np.sqrt(r_to_slits)) * np.exp(-1j * (k * r_to_slits - phi0[i]))
                    
                    dz = z_screen - z_trans
                    dist_x = x[np.newaxis, :] - slit_x_arr[:, np.newaxis]
                    r_from_slits = np.sqrt(dist_x**2 + dz**2)
                    
                    U_individual_slits = (U_slits[:, np.newaxis] / np.sqrt(r_from_slits)) * np.exp(-1j * k * r_from_slits)
                    
                    if slit_width > 1e-6:
                        sin_theta = dist_x / r_from_slits
                        beta = k * (slit_width / 2.0) * sin_theta
                        U_individual_slits *= np.sinc(beta / np.pi)
                    
                    # Плюсуем поле в ОБЩИЙ котел
                    U_slice += np.sum(U_individual_slits, axis=0) / len(src_positions)
        
        # 3. Возводим суммарное поле ВСЕХ источников в квадрат 
        # (получаем интенсивность для данной длины волны)
        intensity_total += np.abs(U_slice)**2 / len(wl_offsets)

    return intensity_total