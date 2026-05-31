from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QGroupBox, QGraphicsRectItem, QLabel, QCheckBox)
from PyQt6.QtCore import Qt, QRectF
import pyqtgraph as pg
import numpy as np
from typing import List

from ui.controls import CustomSlider 
from utils.color_map import wavelength_to_rgb
from PyQt6.QtWidgets import QDoubleSpinBox

class MainWindow(QMainWindow):
    MAX_WAVE_ITEMS = 120  # Пул переиспользуемых кривых для высокого FPS

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Интерференция и когерентность (МФТИ)")
        self.setGeometry(100, 100, 1200, 800)

        # Списки для статических элементов
        self.source_items = []
        self.slit_items = []
        
        # Состояние предпросмотра
        self.preview_item = None
        self.preview_color = None
        self.preview_width = 0.0

        # Собираем интерфейс
        self.setup_ui()
        self._init_wave_pool()

    def _init_wave_pool(self):
        """Оптимизация: создаем невидимые кривые один раз"""
        self.wave_curves: List[pg.PlotCurveItem] = []
        for _ in range(self.MAX_WAVE_ITEMS):
            curve = pg.PlotCurveItem()
            curve.hide()
            self.scene_plot.addItem(curve)
            self.wave_curves.append(curve)

    def finalize_init(self, controller):
        """Подключение логики контроллера после сборки UI"""
        self.controller = controller
        
        self.scene_plot.setXRange(-0.05, self.controller.config.z_screen + 0.15)

        self.btn_point.clicked.connect(lambda: self.controller.activate_placement('point'))
        self.btn_extended.clicked.connect(lambda: self.controller.activate_placement('extended'))
        self.btn_add_slits.clicked.connect(self.controller.add_two_slits)
        self.reset_btn.clicked.connect(self.controller.reset_all)
        self.slit_slider.valueChanged.connect(self._on_slit_distance_changed)

        # Подключаем нижнюю панель к контроллеру
        self.screen_cb.toggled.connect(self.controller.set_slits_enabled)
        self.z_trans_slider.valueChanged.connect(lambda v: self.controller.update_config(z_trans=v))

        self.update_scene_elements()

    def _on_slit_distance_changed(self, value):
        if self.controller:
            self.controller.slit_distance_m = value / 1000.0
            if hasattr(self.controller, '_update_slits'):
                self.controller._update_slits()

    # === РЕНДЕРИНГ И ОБНОВЛЕНИЯ ===

    def update_wave_visuals(self):
            """Отрисовка волн: обрезка об экран со щелями и об финальный экран"""
            if not self.controller or not hasattr(self.controller, 'wavefront_drawer'):
                return
                
            drawer = self.controller.wavefront_drawer
            cfg = self.controller.config
            slits_on = getattr(cfg, 'slits_enabled', False)
            
            # Генерируем только правую полусферу
            theta = np.linspace(-np.pi/2, np.pi/2, 150)

            active_count = 0
            for wave in drawer.waves:
                r = wave['radius']
                if r <= 1e-9: continue
                if active_count >= self.MAX_WAVE_ITEMS: break
                    
                z_center = wave.get('center_z', 0.0)
                z = z_center + r * np.cos(theta)
                x = wave['center_x'] + r * np.sin(theta)
                
                # 1. ОБРЕЗКА ОБ ПРЕГРАДУ СО ЩЕЛЯМИ
                if slits_on and wave.get('is_primary', True):
                    mask_cut = z > cfg.z_trans
                    z[mask_cut] = np.nan
                    x[mask_cut] = np.nan
                    
                # 2. ОБРЕЗКА ОБ ФИНАЛЬНЫЙ ЭКРАН НАБЛЮДЕНИЯ (Все волны исчезают здесь)
                mask_final = z > cfg.z_screen
                z[mask_final] = np.nan
                x[mask_final] = np.nan
                
                curve = self.wave_curves[active_count]
                curve.setData(z, x, pen=pg.mkPen(color=wave['color'], width=2), connect='finite')
                curve.show()
                active_count += 1

            for i in range(active_count, self.MAX_WAVE_ITEMS):
                self.wave_curves[i].hide()

  
    def _make_source_item(self, x, color, width):
        if width > 0:
            rect = QGraphicsRectItem(QRectF(-0.005, x - width / 2, 0.01, width))
            rect.setPen(pg.mkPen(color=color, width=2))
            rect.setBrush(pg.mkBrush(color=color))
            return rect
        else:
            return pg.ScatterPlotItem([0], [x], symbol='o', size=10, pen=color, brush=color)


    def update_intensity_display(self, x_vals, I_norm):
        self.intensity_curve.setData(x_vals, I_norm)

    # === ИНТЕРАКТИВ И ПРЕДПРОСМОТР ===
    def start_preview(self, color, width):
        self.preview_color = color
        self.preview_width = width

    def stop_preview(self):
        if self.preview_item:
            self.scene_plot.removeItem(self.preview_item)
        self.preview_item = None
        self.scene_view.setCursor(Qt.CursorShape.ArrowCursor)

    def update_preview(self, x):
        self.stop_preview()
        item = self._make_source_item(x, self.preview_color, self.preview_width)
        self.scene_plot.addItem(item)
        self.preview_item = item
        self.scene_view.setCursor(Qt.CursorShape.CrossCursor)

    def closeEvent(self, event):
        if self.controller:
            if hasattr(self.controller, 'anim_timer'):
                self.controller.anim_timer.stop()
            if hasattr(self.controller, 'phys_timer'):
                self.controller.phys_timer.stop()
        event.accept()
        
    def setup_ui(self):
        """Создание всех виджетов"""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # === ВЕРХНЯЯ ЧАСТЬ ===
        top_layout = QHBoxLayout()

        self.scene_view = pg.GraphicsLayoutWidget()
        self.scene_plot = self.scene_view.addPlot(title="Распространение волн (x-z)")
        self.scene_plot.setAspectLocked(False)
        
        # --- НОВЫЙ МАСШТАБ СЦЕНЫ (-15 мм ... +15 мм) ---
        self.scene_plot.setYRange(-0.015, 0.015) 
        
        # Включаем умные приставки (PyQtGraph сам подставит 'm' -> 'mm')
        self.scene_plot.setLabel('bottom', 'z', units='m')
        self.scene_plot.setLabel('left', 'x', units='m')
        self.scene_plot.setMouseEnabled(x=False, y=False)
        self.scene_plot.vb.setMouseEnabled(x=False, y=False)
        
        top_layout.addWidget(self.scene_view, stretch=3)

        # ПРАВАЯ ПАНЕЛЬ
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        src_group = QGroupBox("Добавление источников")
        src_layout = QVBoxLayout()
        self.btn_point = QPushButton("Точечный источник")
        self.btn_extended = QPushButton("Протяжённый источник")
        src_layout.addWidget(self.btn_point)
        src_layout.addWidget(self.btn_extended)
        src_group.setLayout(src_layout)
        right_layout.addWidget(src_group)

        slit_group = QGroupBox("Две щели")
        slit_layout = QVBoxLayout()
        # НОВЫЙ ПОЛЗУНОК: от 0 до 20 мм, по умолчанию 2 мм
        self.slit_slider = CustomSlider("Расстояние между щелями (мм)", 0, 20, 2)
        self.btn_add_slits = QPushButton("Добавить две щели")
        slit_layout.addWidget(self.slit_slider)
        slit_layout.addWidget(self.btn_add_slits)
        slit_group.setLayout(slit_layout)
        right_layout.addWidget(slit_group)

        self.intensity_view = pg.GraphicsLayoutWidget()
        self.intensity_plot = self.intensity_view.addPlot(title="Интерференция I_norm(x)")
        self.intensity_plot.setLabel('bottom', 'x', units='m') # Тоже умная ось
        self.intensity_plot.setLabel('left', 'Интенсивность (норм.)')
        self.intensity_plot.setMouseEnabled(x=False, y=False) 
        self.intensity_plot.hideButtons()                     
        self.intensity_plot.setMenuEnabled(False)             
        self.intensity_plot.setYRange(0, 1.05)                
        self.intensity_plot.setXRange(-0.015, 0.015) # Синхронизируем со сценой
        
        self.intensity_curve = self.intensity_plot.plot(pen=pg.mkPen('y', width=2))
        right_layout.addWidget(self.intensity_view, 1)

        self.reset_btn = QPushButton("Очистить всё")
        right_layout.addWidget(self.reset_btn)
        top_layout.addWidget(right_panel, stretch=1)
        root_layout.addLayout(top_layout, stretch=1)

        # === НИЖНЯЯ ПАНЕЛЬ ===
        self.bottom_panel = QGroupBox("Управление сплошным экраном")
        bottom_layout = QHBoxLayout(self.bottom_panel)
        self.screen_cb = QCheckBox("Включить сплошной экран")
        self.z_trans_slider = CustomSlider("Положение экрана по оси Z (м)", 0.05, 0.45, 0.2)
        bottom_layout.addWidget(self.screen_cb)
        bottom_layout.addWidget(self.z_trans_slider)
        root_layout.addWidget(self.bottom_panel)
        
        self.phi_input = QDoubleSpinBox()
        self.phi_input.setRange(-180.0, 180.0) # Градусы
        self.phi_input.setSingleStep(5.0)    # Шаг 5 градусов
        self.phi_input.setPrefix("phi (град): ")
        src_layout.addWidget(self.phi_input)

    def get_screen_coords(self):
        # Массив для расчета физики тоже сужаем до +-15 мм
        return np.linspace(-0.015, 0.015, 1000)

    def update_scene_elements(self):
        """Обновление источников и отрисовка экрана с прорезанными щелями"""
        if not self.controller: return

        for item in self.source_items + self.slit_items:
            self.scene_plot.removeItem(item)
        self.source_items.clear()
        self.slit_items.clear()

        cfg = self.controller.config
        slits_on = getattr(cfg, 'slits_enabled', False)
        
        if hasattr(cfg, 'x_src'):
            for idx in range(len(cfg.x_src)):
                width = cfg.src_widths[idx] if hasattr(cfg, 'src_widths') else 0
                color = cfg.source_colors[idx] if hasattr(cfg, 'source_colors') else 'w'
                item = self._make_source_item(cfg.x_src[idx], color, width)
                self.scene_plot.addItem(item)
                self.source_items.append(item)

        if slits_on:
            z_pos = cfg.z_trans
            if hasattr(cfg, 'x_slit') and len(cfg.x_slit) > 0:
                slits_x = sorted(cfg.x_slit)
            else:
                slits_x = [-0.001, 0.001]  # По умолчанию дырки на +- 1 мм
            
            vis_w = 0.0005 # Визуальная ширина дырки теперь 0.5 мм 
            current_x = -0.05  
            
            for sx in slits_x:
                slit_bottom = sx - vis_w / 2
                slit_top = sx + vis_w / 2
                segment = pg.PlotDataItem([z_pos, z_pos], [current_x, slit_bottom], pen=pg.mkPen('w', width=3))
                self.scene_plot.addItem(segment)
                self.slit_items.append(segment)
                current_x = slit_top  
                
            segment = pg.PlotDataItem([z_pos, z_pos], [current_x, 0.05], pen=pg.mkPen('w', width=3))
            self.scene_plot.addItem(segment)
            self.slit_items.append(segment)

        obs_screen = pg.InfiniteLine(pos=cfg.z_screen, angle=90, pen=pg.mkPen('y', width=3))
        self.scene_plot.addItem(obs_screen)
        self.slit_items.append(obs_screen)