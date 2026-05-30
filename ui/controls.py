from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal

class CustomSlider(QWidget):
    valueChanged = pyqtSignal(float)
    def __init__(self, label, min_val, max_val, init_val, parent=None):
        super().__init__(parent)
        self.min_val, self.max_val = min_val, max_val
        layout = QHBoxLayout(self)
        self.label = QLabel(f"{label}: {init_val:.1f}")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(self._to_slider(init_val))
        self.slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)

    def _to_slider(self, val): return int((val - self.min_val) / (self.max_val - self.min_val) * 1000)
    def _from_slider(self, sv): return self.min_val + (sv / 1000) * (self.max_val - self.min_val)
    def _on_slider(self, sv):
        val = self._from_slider(sv)
        self.label.setText(f"{self.label.text().split(':')[0]}: {val:.1f}")
        self.valueChanged.emit(val)
    def get_value(self): return self._from_slider(self.slider.value())