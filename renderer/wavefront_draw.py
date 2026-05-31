import numpy as np

class WavefrontDrawer:
    def __init__(self):
        self.waves = []  

    def update_radii(self, dt, speed, config):
        """Физика роста радиуса и точная генерация вторичных волн с компенсацией разности хода"""
        slits_on = getattr(config, 'slits_enabled', False)
        
        for wave in self.waves[:]: 
            wave['radius'] += speed * dt
            
            # 1. Удаляем волны, которые улетели за финальный экран наблюдения
            if wave['radius'] > config.z_screen + 0.2:
                self.waves.remove(wave)
                continue
                
            # 2. ПРИНЦИП ГЮЙГЕНСА (Вторичные волны)
            if slits_on and wave.get('is_primary', True):
                if hasattr(config, 'x_slit') and len(config.x_slit) > 0:
                    
                    for i, x_s in enumerate(config.x_slit):
                        if i in wave['slits_spawned']:
                            continue
                            
                        # Считаем точное диагональное расстояние от центра первичной волны до щели
                        dx = x_s - wave['center_x']
                        dz = config.z_trans - wave['center_z']
                        dist_to_slit = np.sqrt(dx**2 + dz**2)
                        
                        # Если волна дошла до щели (или перелетела её в этом кадре)
                        if wave['radius'] >= dist_to_slit:
                            wave['slits_spawned'].add(i)
                            
                            # СЧИТАЕМ РАЗНОСТЬ ХОДА (Идеальная компенсация перелета)
                            excess_radius = wave['radius'] - dist_to_slit
                            
                            # Спавним вторичную волну УЖЕ подросшей на величину перелета!
                            self.add_wave(
                                center_z=config.z_trans,
                                center_x=x_s,
                                color=wave['color'],
                                is_primary=False,
                                initial_radius=excess_radius # <--- ИСПРАВЛЕНИЕ ЗДЕСЬ
                            )

    def add_wave(self, center_z, center_x, color, is_primary=True, initial_radius=0.0):
        """Добавление новой волны (с поддержкой стартового радиуса)"""
        self.waves.append({
            'center_z': center_z,
            'center_x': center_x,
            'radius': initial_radius, # <--- ТЕПЕРЬ МОЖЕТ БЫТЬ НЕ НОЛЬ
            'color': color,
            'is_primary': is_primary,
            'slits_spawned': set() 
        })
        
    def clear(self):
        self.waves.clear()