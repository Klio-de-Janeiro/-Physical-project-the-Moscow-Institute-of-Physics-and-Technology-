import numpy as np
from utils.color_map import wavelength_to_rgb

class WavefrontDrawer:
    def __init__(self):
        self.waves = []  # [{'center_x': float, 'radius': float, 'color': tuple}]

    # Вызывать при добавлении/удалении источников (один раз)
    def rebuild_from_config(self, config, current_time=None):
        """Создаёт начальные волны от каждого источника (радиус = 0)"""
        self.waves.clear()
        for i in range(len(config.x_src)):
            x_src = config.x_src[i]
            width = config.src_widths[i]
            lam = config.lambdas[i]
            rgb = wavelength_to_rgb(lam * 1e9)
            # Для протяжённого источника — два края, для точечного — один центр
            centers = [x_src - width/2, x_src + width/2] if width > 0 else [x_src]
            for cx in centers:
                self.waves.append({
                    'center_x': cx,
                    'radius': 0.0,
                    'color': rgb
                })

    def update_radii(self, dt, speed, config):
        """Увеличивает радиус каждой волны, удаляет ушедшие далеко за экран"""
        for wave in self.waves[:]:  # проходим по копии, чтобы можно было удалять
            wave['radius'] += speed * dt
            # Удаляем волну, когда она прошла экран и ещё немного (на 0.2 м)
            if wave['radius'] > config.z_screen + 0.2:
                self.waves.remove(wave)

    def add_wave(self, center_x, color, initial_radius=0.0):
        """Добавляет новую волну от источника (вызывается по таймеру)"""
        self.waves.append({
            'center_x': center_x,
            'radius': initial_radius,
            'color': color
        })