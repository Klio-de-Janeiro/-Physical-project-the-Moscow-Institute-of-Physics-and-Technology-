import numpy as np
from utils.color_map import wavelength_to_rgb

class WavefrontDrawer:
    def __init__(self):  # ✅ Исправлено: __init__ вместо init
        self.waves = []  # [{'center_x': float, 'radius': float, 'last_emit': float, 'color': tuple}]

    def update_radii(self, dt, speed, config, current_time):
        expected_waves = sum(2 if w > 0 else 1 for w in config.src_widths)
        if len(self.waves) != expected_waves or len(config.x_src) == 0:
            self._rebuild_waves(config, current_time)

        for wave in self.waves:
            wave['radius'] += speed * dt
            if wave['radius'] > config.z_screen + 1.2:
                wave['radius'] = 0.0
                wave['last_emit'] = current_time
            if current_time - wave['last_emit'] >= config.dt_emit:
                wave['radius'] = 0.0
                wave['last_emit'] = current_time

    def _rebuild_waves(self, config, current_time):
        self.waves.clear()
        for i in range(len(config.x_src)):
            x_src = config.x_src[i]
            width = config.src_widths[i]
            lam = config.lambdas[i]
            rgb = wavelength_to_rgb(lam * 1e9)  # передаём в нм

            # Точечный → 1 центр, Протяжённый → 2 края
            centers = [x_src - width/2, x_src + width/2] if width > 0 else [x_src]
            for cx in centers:
                self.waves.append({
                    'center_x': cx,
                    'radius': 0.0,
                    'last_emit': current_time,
                    'color': rgb
                })