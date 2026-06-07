import numpy as np

class WavefrontDrawer:
    def __init__(self):
        self.waves = []  

    def update_radii(self, dt, speed, config):
        slits_on = getattr(config, 'slits_enabled', False)
        
        for wave in self.waves[:]: 
            wave['radius'] += speed * dt
            
            if wave['radius'] > config.z_screen + 0.2:
                self.waves.remove(wave)
                continue
                
            if slits_on and wave.get('is_primary', True):
                if hasattr(config, 'x_slit') and len(config.x_slit) > 0:
                    
                    for i, x_s in enumerate(config.x_slit):
                        if i in wave['slits_spawned']:
                            continue
                            
                        dx = x_s - wave['center_x']
                        dz = config.z_trans - wave['center_z']
                        dist_to_slit = np.sqrt(dx**2 + dz**2)
                        
                        if wave['radius'] >= dist_to_slit:
                            wave['slits_spawned'].add(i)
                            
                            excess_radius = wave['radius'] - dist_to_slit
                            
                            self.add_wave(
                                center_z=config.z_trans,
                                center_x=x_s,
                                color=wave['color'],
                                is_primary=False,
                                initial_radius=excess_radius 
                            )

    def add_wave(self, center_z, center_x, color, is_primary=True, initial_radius=0.0):
        """Добавление новой волны (с поддержкой стартового радиуса)"""
        self.waves.append({
            'center_z': center_z,
            'center_x': center_x,
            'radius': initial_radius, 
            'color': color,
            'is_primary': is_primary,
            'slits_spawned': set() 
        })
        
    def clear(self):
        self.waves.clear()