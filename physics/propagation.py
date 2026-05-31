import numpy as np

def calculate_field(x_sources, z_sources, wavelengths, amplitudes, x_screen, z_screen):
    """
    Вычисляет суммарное комплексное поле в точках экрана от набора источников.
    
    :param x_sources: np.array координат x источников
    :param z_sources: np.array координат z источников
    :param wavelengths: np.array длин волн (в метрах)
    :param amplitudes: np.array начальных амплитуд E0
    :param x_screen: np.array координат x точек на экране
    :param z_screen: координата z экрана (константа 0.5)
    :return: np.array комплексных амплитуд поля на экране
    """
    # Создаем сетку: строки - источники, столбцы - точки экрана
    # x_screen shape: (N_points,), x_sources shape: (M_sources, 1)
    dx = x_screen[np.newaxis, :] - x_sources[:, np.newaxis]
    dz = z_screen - z_sources[:, np.newaxis]
    
    # Расстояние r от каждого источника до каждой точки экрана 
    r = np.sqrt(dx**2 + dz**2)
    
    # Волновое число k [cite: 27]
    k = 2 * np.pi / wavelengths[:, np.newaxis]
    
    # Комплексное поле U = (E0 / r) * exp(-j * k * r) 
    # Затухание поля как 1/r [cite: 91]
    fields = (amplitudes[:, np.newaxis] / r) * np.exp(-1j * k * r)
    
    # Суммируем вклады всех источников в каждой точке экрана
    return np.sum(fields, axis=0)