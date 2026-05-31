import pyqtgraph as pg

class SceneManager:
    def __init__(self, plot_widget):
        self.plot = plot_widget
        self.setup_static_elements()
        
    def setup_static_elements(self):
        """Настройка фиксированной сцены по ТЗ [cite: 71, 77]"""
        self.plot.setXRange(0, 0.5) # Ось Z (горизонталь)
        self.plot.setYRange(-0.12, 0.12) # Ось X (вертикаль)
        self.plot.setMouseEnabled(x=False, y=False) # Запрет зума [cite: 77]
        
        # Линия экрана (z = 0.5) [cite: 76]
        self.screen_line = pg.InfiniteLine(pos=0.5, angle=90, pen='w')
        self.plot.addItem(self.screen_line)
        
        # Линия преград (z = 0.2) [cite: 75]
        self.slit_plane = pg.InfiniteLine(pos=0.2, angle=90, pen='d')
        self.plot.addItem(self.slit_plane)

    def draw_sources(self, sources):
        """Отрисовка самих источников (точки/прямоугольники) [cite: 78, 80]"""
        # Логика отрисовки графических примитивов источников
        pass