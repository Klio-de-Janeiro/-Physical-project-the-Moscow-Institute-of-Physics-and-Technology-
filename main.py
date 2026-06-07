import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from app_controller import AppController
from config.defaults import DEFAULT_CONFIG

def main():
    app = QApplication(sys.argv)
    window = MainWindow() 
    controller = AppController(window, DEFAULT_CONFIG)
    window.finalize_init(controller)
    window.show()
    controller.run()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()