import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from app_controller import AppController
from config.defaults import DEFAULT_CONFIG

def main():
    app = QApplication(sys.argv)
    
    # 1. Создаем пустое окно
    window = MainWindow() 
    
    # 2. Создаем контроллер, передаем ему окно и УЖЕ ГОТОВЫЙ конфиг
    controller = AppController(window, DEFAULT_CONFIG)
    
    # 3. Финально связываем UI и логику
    window.finalize_init(controller)
    
    # 4. Запускаем окно и таймеры симуляции
    window.show()
    controller.run()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()