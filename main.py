import sys
from PyQt6.QtWidgets import QApplication
from app_controller import AppController

def main():
    app = QApplication(sys.argv)
    ctrl = AppController()
    ctrl.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()