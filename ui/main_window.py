from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF, QTimer
import pyqtgraph as pg
import numpy as np
from ui.controls import CustomSlider
from utils.color_map import wavelength_to_rgb

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Интерференция и когерентность")
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # === СЦЕНА ===
        self.scene_view = pg.GraphicsLayoutWidget()
        self.scene_plot = self.scene_view.addPlot(title="Распространение волн (x-z)")
        self.scene_plot.setAspectLocked(False)
        self.scene_plot.setXRange(-0.05, controller.config.z_screen + 0.15)
        self.scene_plot.setYRange(-0.12, 0.12)
        self.scene_plot.setLabel('bottom', 'z (м)')
        self.scene_plot.setLabel('left', 'x (м)')
        self.scene_plot.setMouseEnabled(x=False, y=False)
        self.scene_plot.vb.setMouseEnabled(x=False, y=False)
        self.scene_plot.getAxis('bottom').autoSIPrefix = False
        self.scene_plot.getAxis('left').autoSIPrefix = False
        main_layout.addWidget(self.scene_view, 3)

        # === ПАНЕЛЬ УПРАВЛЕНИЯ ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        src_group = QGroupBox("Добавление источников")
        src_layout = QVBoxLayout()
        self.btn_point = QPushButton("Точечный источник")
        self.btn_point.clicked.connect(lambda: controller.activate_placement('point'))
        self.btn_extended = QPushButton("Протяжённый источник")
        self.btn_extended.clicked.connect(lambda: controller.activate_placement('extended'))
        src_layout.addWidget(self.btn_point)
        src_layout.addWidget(self.btn_extended)
        src_group.setLayout(src_layout)
        right_layout.addWidget(src_group)

        slit_group = QGroupBox("Две щели")
        slit_layout = QVBoxLayout()
        self.slit_slider = CustomSlider("Расстояние между щелями (мм)", 0, 100, 40)
        self.slit_slider.valueChanged.connect(lambda v: setattr(controller, 'slit_distance_mm', v))
        self.btn_add_slits = QPushButton("Добавить две щели")
        self.btn_add_slits.clicked.connect(controller.add_two_slits)
        slit_layout.addWidget(self.slit_slider)
        slit_layout.addWidget(self.btn_add_slits)
        slit_group.setLayout(slit_layout)
        right_layout.addWidget(slit_group)

        self.intensity_view = pg.GraphicsLayoutWidget()
        self.intensity_plot = self.intensity_view.addPlot(title="Интерференция I_norm(x)")
        self.intensity_plot.setLabel('bottom', 'x (м)')
        self.intensity_plot.setLabel('left', 'Интенсивность (норм.)')
        self.intensity_curve = self.intensity_plot.plot(pen='y')
        right_layout.addWidget(self.intensity_view, 1)

        reset_btn = QPushButton("Очистить всё")
        reset_btn.clicked.connect(controller.reset_all)
        right_layout.addWidget(reset_btn)
        main_layout.addWidget(right_panel, 1)

        # Инициализация списков для графических элементов
        self.source_items = []
        self.slit_items = []
        self.wave_curves = []
        self.preview_item = None
        self.preview_color = None
        self.preview_width = 0.0

        # Таймер для непрерывной генерации волн
        self.wave_gen_timer = QTimer()
        self.wave_gen_timer.timeout.connect(self._generate_new_waves)
        self.wave_gen_timer.start(200)  # каждые 200 мс создаём новую волну от каждого источника

        self.update_scene_elements()

    def _generate_new_waves(self):
        """Периодически добавляет новые сферические волны от всех активных источников."""
        if hasattr(self.controller, 'add_waves_from_sources'):
            self.controller.add_waves_from_sources()
        else:
            # fallback: если в контроллере нет такого метода, создаём волны напрямую через drawer
            if hasattr(self.controller, 'wavefront_drawer') and hasattr(self.controller, 'config'):
                drawer = self.controller.wavefront_drawer
                cfg = self.controller.config
                for idx in range(cfg.N_src):
                    drawer.add_wave(cfg.x_src[idx], color=cfg.source_colors[idx])

    def stop_wave_generation(self):
        """Останавливает таймер генерации волн (вызывается при закрытии окна)."""
        if self.wave_gen_timer.isActive():
            self.wave_gen_timer.stop()

    def closeEvent(self, event):
        """Корректно останавливаем таймер при закрытии окна."""
        self.stop_wave_generation()
        event.accept()

    def update_wave_visuals(self):
        """Отрисовка сферических фронтов через pg.PlotCurveItem"""
        # Удаляем старые кривые
        for c in self.wave_curves:
            self.scene_plot.removeItem(c)
        self.wave_curves.clear()

        drawer = self.controller.wavefront_drawer
        theta = np.linspace(0, 2 * np.pi, 80)

        for wave in drawer.waves:
            r = wave['radius']
            if r <= 1e-9:
                continue
            z = r * np.cos(theta)
            x = wave['center_x'] + r * np.sin(theta)
            rgb = wave['color']
            curve = pg.PlotCurveItem(z, x, pen=pg.mkPen(color=rgb, width=2))
            self.scene_plot.addItem(curve)
            self.wave_curves.append(curve)

    def _make_source_item(self, x, color, width):
        """Создаёт статичный элемент источника: точка или полностью закрашенный прямоугольник"""
        if width > 0:
            rect = QGraphicsRectItem(QRectF(-0.005, x - width / 2, 0.01, width))
            rect.setPen(pg.mkPen(color=color, width=2))
            rect.setBrush(pg.mkBrush(color=color))
            return rect
        else:
            spot = pg.ScatterPlotItem([0], [x], symbol='o', size=10, pen=color, brush=color)
            return spot

    def update_scene_elements(self):
        """Обновление источников и щелей на сцене"""
        for item in self.source_items + self.slit_items:
            self.scene_plot.removeItem(item)
        self.source_items.clear()
        self.slit_items.clear()

        cfg = self.controller.config
        for idx in range(cfg.N_src):
            item = self._make_source_item(cfg.x_src[idx], cfg.source_colors[idx], cfg.src_widths[idx])
            self.scene_plot.addItem(item)
            self.source_items.append(item)

        for x_slit in cfg.x_slit:
            line = pg.InfiniteLine(pos=(cfg.z_trans, x_slit), angle=90, pen=pg.mkPen('b', width=2))
            self.scene_plot.addItem(line)
            self.slit_items.append(line)

    def update_intensity_display(self, I_norm, x_vals, _):
        self.intensity_curve.setData(x_vals, I_norm)

    def start_source_preview(self, color, width):
        self.preview_color = color
        self.preview_width = width

    def stop_source_preview(self):
        if self.preview_item:
            self.scene_plot.removeItem(self.preview_item)
        self.preview_item = None

    def update_source_preview(self, x):
        """Отрисовка предпросмотра источника при движении мыши"""
        self.stop_source_preview()
        item = self._make_source_item(x, self.preview_color, self.preview_width)
        self.scene_plot.addItem(item)
        self.preview_item = item