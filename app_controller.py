import numpy as np
import time
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMessageBox, QInputDialog

# Убедись, что эти импорты соответствуют твоей структуре проекта
from physics.coherence import compute_interference_pattern
from renderer.wavefront_draw import WavefrontDrawer
from ui.interaction import InteractionHandler
from utils.logger import PerformanceLogger
from utils.color_map import wavelength_to_rgb

class AppController:
    def __init__(self, main_window, config):
        """Контроллер теперь принимает уже созданное окно, решая проблему циклической зависимости"""
        self.main_window = main_window
        self.config = config
        
        self.wavefront_drawer = WavefrontDrawer()
        self.performance_logger = PerformanceLogger()
        
        # Подключаем обработчик мыши (перетаскивание и клики)
        self.interaction_handler = InteractionHandler(self.main_window, self)
        
        # Переменные состояния UI
        self.pending_source_params = None
        self.placement_mode = None
        
        # Параметры щелей (в метрах)
        self.slit_distance_m = 0.040 
        self.x_offset_m = 0.0
        self.slits_enabled = False

        # Флаг для оптимизации вычислений (считаем физику только при изменениях)
        self.needs_recalc = True

        # === ТАЙМЕРЫ ===
        # 1. Таймер анимации (расширение волн и перерисовка экрана) ~ 30 FPS
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_animation)
        
        # 2. Таймер генерации волн (испускание новых фронтов каждые 500 мс)
        self.gen_timer = QTimer()
        self.gen_timer.timeout.connect(self.add_waves_from_sources)

    def run(self):
        """Запуск цикла симуляции"""
        self.anim_timer.start(33)
        self.gen_timer.start(300)
        self.update_interference()

    # === ОБРАБОТКА ВЗАИМОДЕЙСТВИЙ (ИСТОЧНИКИ) ===

    def activate_placement(self, mode):
        """Диалог добавления нового источника"""
        wl_nm, ok = QInputDialog.getDouble(self.main_window, f"Источник ({mode})", "Длина волны (нм):", 550, 400, 700, 1)
        if not ok: return
        
        width = 0.0
        if mode == 'extended':
            w_mm, ok2 = QInputDialog.getDouble(self.main_window, "Протяжённый", "Ширина (мм):", 5, 0.1, 50, 1)
            if not ok2: return
            width = w_mm * 1e-3
            
        wl = wl_nm * 1e-9
        rgb = wavelength_to_rgb(wl_nm)
        color = (rgb[0], rgb[1], rgb[2])
        
        self.pending_source_params = (wl, color, width)
        self.placement_mode = mode
        
        self.main_window.start_preview(color, width)
        self.main_window.scene_view.setCursor(Qt.CursorShape.CrossCursor)

    def cancel_placement(self):
        self.pending_source_params = None
        self.placement_mode = None
        self.main_window.stop_preview()

    def update_preview_position(self, x): 
        self.main_window.update_preview(x)

    def place_source_at(self, x):
        if self.pending_source_params is None: return
        wl, color, width = self.pending_source_params
        self.add_source(x, wl, 1.0, 0.0, color, is_ext=(width > 0), width=width)
        self.cancel_placement()

    def add_source(self, x, wl, E0, phi0, color, is_ext=False, width=0.0):
        if hasattr(self.config, 'N_src') and self.config.N_src >= 10:
            QMessageBox.warning(self.main_window, "Limit", "Максимум 10 источников")
            return
            
        for k, v in zip(('x_src', 'lambdas', 'E0', 'phi0', 'source_colors', 'src_widths'), 
                        (x, wl, E0, phi0, color, width)):
            if not hasattr(self.config, k):
                setattr(self.config, k, [])
            getattr(self.config, k).append(v)
            
        self.config.N_src = len(self.config.x_src)
        self.config.x_src.append(x)
        self.config.lambdas.append(wl)
        self.config.E0.append(E0)
        self.config.phi0.append(phi0)  # Добавляем фазу
        self.config.source_colors.append(color)
        self.config.src_widths.append(width)
        
        self.config.N_src += 1
        self.on_params_changed()

    def remove_source(self, idx):
        for k in ('x_src', 'lambdas', 'E0', 'phi0', 'source_colors', 'src_widths'):
            if hasattr(self.config, k) and len(getattr(self.config, k)) > idx:
                getattr(self.config, k).pop(idx)
        self.config.N_src = len(self.config.x_src)
        self.wavefront_drawer.clear()
        self.on_params_changed()

    def reset_all(self):
        # Убрали 'x_slit' из очистки, чтобы математические координаты щелей не стирались!
        for k in ('x_src', 'lambdas', 'E0', 'phi0', 'source_colors', 'src_widths'):
            setattr(self.config, k, [])
        
        self.config.N_src = 0
        self.wavefront_drawer.clear()
        self.on_params_changed()
    # === ОБРАБОТКА ВЗАИМОДЕЙСТВИЙ (ЩЕЛИ) ===

    def add_two_slits(self):
        self._update_slits()

    def _update_slits(self):
        """Пересчет позиций щелей при сдвиге ползунка"""
        # Если чекбокс выключен или это не режим двух щелей — игнорируем
        d = self.slit_distance_m
        x1 = self.x_offset_m - (d / 2)
        x2 = self.x_offset_m + (d / 2)
        self.config.x_slit = [x1, x2]
        self.on_params_changed()

    def on_params_changed(self):
        """Вызывается при любом изменении сцены (перетаскивание, удаление, добавление)"""
        self.needs_recalc = True
        if self.main_window:
            self.main_window.update_scene_elements()

    def set_slits_enabled(self, enabled):
        self.slits_enabled = enabled
        self.config.slits_enabled = enabled  # Записываем флаг напрямую в конфиг для UI
        
        if not enabled:
            self.config.x_slit = []
        else:
            self._update_slits()
            
        # Очищаем волны, чтобы они сгенерировались заново с учетом новых преград
        self.wavefront_drawer.clear()
        self.on_params_changed()

    def update_config(self, **kwargs):
        """Универсальный метод для обновления конфига (напр. смещение экрана z_trans)"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
            # Если мы двигаем преграду (z_trans), нужно сбросить волны, 
            # чтобы отражение пересчиталось для новой координаты мгновенно
            if key == 'z_trans':
                self.wavefront_drawer.clear()
                
        self.on_params_changed()

    # === ГЕНЕРАЦИЯ ВОЛН И ФИЗИКА ===

    def add_waves_from_sources(self):
        """Испускает новые фронты строго от источников (z=0)"""
        if not hasattr(self.config, 'N_src'): return
        
        for idx in range(self.config.N_src):
            x_pos = self.config.x_src[idx]
            color = self.config.source_colors[idx]
            
            # Получаем ширину источника (с безопасной проверкой)
            width = 0.0
            if hasattr(self.config, 'src_widths') and len(self.config.src_widths) > idx:
                width = self.config.src_widths[idx]

            # Если источник протяженный (ширина > 0), генерируем две точки по краям.
            # Иначе - одну точку в центре.
            if width > 1e-6:
                centers_x = [x_pos - width / 2, x_pos + width / 2]
            else:
                centers_x = [x_pos]

            # Испускаем волны из вычисленных точек
            for cx in centers_x:
                self.wavefront_drawer.add_wave(
                    center_z=0.0, 
                    center_x=cx, 
                    color=color, 
                    is_primary=True
                )

    def update_animation(self):
        """Основной цикл обновления (30 раз в секунду)"""
        dt = self.config.dt_anim
        # Двигаем волны по физике Гюйгенса-Френеля
        self.wavefront_drawer.update_radii(dt, self.config.wave_speed, self.config)
        self.main_window.update_wave_visuals()
        
        # Считаем интерференцию только если что-то изменилось (перетащили щель/источник)
        if self.needs_recalc:
            self.update_interference()
            self.needs_recalc = False

    def update_interference(self):
        """Тяжелый математический расчет профиля интенсивности"""
        t0 = time.perf_counter()
        
        # Получаем координаты x от окна
        if hasattr(self.main_window, 'get_screen_coords'):
            x = self.main_window.get_screen_coords()
        else:
            x = np.linspace(-0.12, 0.12, 1000)

        # ВАЖНАЯ ЛОГИКА: Учитываем щели ТОЛЬКО если включен сплошной экран
        slits_on = getattr(self.config, 'slits_enabled', False)
        active_slits = self.config.x_slit if slits_on else []

        # Вызов твоего физического движка (physics/coherence.py)
        I = compute_interference_pattern(
            x_vals=x, 
            src_x=self.config.x_src, 
            lambdas=self.config.lambdas, 
            E0=self.config.E0, 
            phi0=self.config.phi0,
            src_widths=self.config.src_widths, 
            slit_x=active_slits, # <--- Передаем дырки только если стена стоит!
            slit_width=self.config.w_slit,
            z_trans=self.config.z_trans, 
            z_screen=self.config.z_screen, 
            delta_lambda=self.config.delta_lambda, 
            spatial_samples=self.config.spatial_samples
        )
        
        # Нормируем интенсивность, чтобы пик всегда был на 1.0 
        Imax = np.max(I) if np.any(I) else 1.0
        norm_I = I / Imax if Imax > 0 else I
        
        self.main_window.update_intensity_display(x, norm_I)
        self.performance_logger.log_frame_time(time.perf_counter() - t0)