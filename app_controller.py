import numpy as np, time
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from config.schema import SimulationConfig
from config.defaults import DEFAULT_CONFIG
from physics.coherence import compute_interference_pattern
from renderer.scene_manager import SceneManager
from renderer.wavefront_draw import WavefrontDrawer
from ui.main_window import MainWindow
from ui.interaction import InteractionHandler
from utils.logger import PerformanceLogger
from utils.color_map import wavelength_to_rgb

class AppController:
    def __init__(self):
        self.wave_time = 0.0
        # Фикс пробелов в ключах defaults.py
        clean_cfg = {k.strip(): v for k, v in DEFAULT_CONFIG.items()}
        self.config = SimulationConfig(**clean_cfg)
        
        self.scene_mgr = SceneManager()
        self.wavefront_drawer = WavefrontDrawer()
        self.performance_logger = PerformanceLogger()
        self.main_window = MainWindow(self)
        self.interaction = InteractionHandler(self.main_window, self)
        
        self.pending_source_params = None
        self.placement_mode = None
        self.slit_distance_mm = 40.0

        self.animation_timer = QTimer(); self.animation_timer.timeout.connect(self.update_animation)
        self.refresh_timer = QTimer(); self.refresh_timer.timeout.connect(self.update_interference)
        self.wave_gen_timer = QTimer()
        self.wave_gen_timer.timeout.connect(self.add_waves_from_sources)

        # В методе run (после self.main_window.show()):
        self.wave_gen_timer.start(200)   # каждые 200 мс добавляем новые волны

    def run(self):
        self.main_window.show()
        self.animation_timer.start(33)
        self.refresh_timer.start(50)
        self.update_interference()

    def activate_placement(self, mode):
        wl_nm, ok = QInputDialog.getDouble(self.main_window, f"Источник ({mode})", "Длина волны (нм):", 550, 400, 700, 1)
        if not ok: return
        width = 0.0
        if mode == 'extended':
            w_mm, ok2 = QInputDialog.getDouble(self.main_window, "Протяжённый", "Ширина (мм):", 5, 0.1, 50, 1)
            if not ok2: return
            width = w_mm * 1e-3
        wl = wl_nm * 1e-9
        rgb = wavelength_to_rgb(wl_nm)
        color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        self.pending_source_params = (wl, color, width)
        self.placement_mode = mode
        self.main_window.start_source_preview(color, width)
        self.main_window.scene_view.setCursor(Qt.CursorShape.CrossCursor)

    def on_params_changed(self):
        self.main_window.update_scene_elements()
        self.update_interference()

    def cancel_placement(self):
        self.pending_source_params = None; self.placement_mode = None
        self.main_window.stop_source_preview(); self.main_window.scene_view.setCursor(Qt.CursorShape.ArrowCursor)

    def update_animation(self):
        dt = self.config.dt_anim
        self.wave_time += dt
        # Исправленный вызов: удалён четвёртый аргумент self.wave_time
        self.wavefront_drawer.update_radii(dt, self.config.wave_speed, self.config)
        self.main_window.update_wave_visuals()
        
    def update_interference(self):
        t0 = time.perf_counter()
        x = np.linspace(-0.1, 0.1, self.config.screen_resolution)
        I = compute_interference_pattern(x, self.config.x_src, self.config.lambdas, self.config.E0, self.config.phi0,
                                         self.config.src_widths, self.config.x_slit, self.config.w_slit,
                                         self.config.z_trans, self.config.z_screen, self.config.delta_lambda, self.config.spatial_samples)
        Imax = np.max(I) if np.any(I) else 1.0
        self.main_window.update_intensity_display(I/Imax, x, self.config.lambdas[0] if self.config.lambdas else 550e-9)
        self.performance_logger.log_frame_time(time.perf_counter()-t0)

    def update_preview_position(self, x): self.main_window.update_source_preview(x)
    def place_source_at(self, x):
        if self.pending_source_params is None: return
        wl, color, width = self.pending_source_params
        self.add_source(x, wl, 1.0, 0.0, color, is_ext=(width>0), width=width)
        self.cancel_placement()
        
    def add_waves_from_sources(self):
        """Создаёт новую сферическую волну от каждого активного источника."""
        for idx in range(self.config.N_src):
            x_pos = self.config.x_src[idx]
            color = self.config.source_colors[idx]
            # предполагается, что у вас есть метод add_wave в wavefront_drawer
            self.wavefront_drawer.add_wave(x_pos, color=color)
            

    # В методе on_params_changed (или там, где меняются источники):
    def on_params_changed(self):
        self.wavefront_drawer.rebuild_from_config(self.config)  # ← перестроить базовые волны
        self.main_window.update_scene_elements()
        self.update_interference()

    # При сбросе/удалении источников тоже нужно перестраивать. У вас уже есть reset_all, remove_source — добавьте туда rebuild:
    def remove_source(self, idx):
        for k in ('x_src','lambdas','E0','phi0','source_colors','src_widths'):
            getattr(self.config, k).pop(idx)
        self.config.N_src = len(self.config.x_src)
        self.wavefront_drawer.rebuild_from_config(self.config)   # ← добавить
        self.on_params_changed()

    def reset_all(self):
        for k in ('x_src','lambdas','E0','phi0','source_colors','src_widths','x_slit'):
            setattr(self.config, k, [])
        self.config.N_src = 0
        self.wavefront_drawer.rebuild_from_config(self.config)   # ← добавить
        self.on_params_changed()

    def add_two_slits(self):
        d = self.slit_distance_mm / 1000.0
        self.config.x_slit = [-d/2, d/2]
        # Если вы хотите, чтобы волны шли от щелей, а не от источников — но у вас логика волн от источников.
        # Щели у вас используются только для интерференции, а волны рисуются от источников. Это нормально.
        self.on_params_changed()   # здесь уже есть rebuild? Нет, on_params_changed не вызывает rebuild. Исправим:
        # Лучше переписать on_params_changed так, как выше.

    # Также в методе add_source:
    def add_source(self, x, wl, E0, phi0, color, is_ext=False, width=0.0):
        if self.config.N_src >= 10:
            QMessageBox.warning(self.main_window, "Limit", "Максимум 10")
            return
        for k, v in zip(('x_src','lambdas','E0','phi0','source_colors','src_widths'), (x,wl,E0,phi0,color,width)):
            getattr(self.config, k).append(v)
        self.config.N_src = len(self.config.x_src)
        self.wavefront_drawer.rebuild_from_config(self.config)   # ← добавить
        self.on_params_changed()