
import os
os.environ["QT_API"] = "pyside6"
import sys
from qtpy.QtWidgets import QApplication
from femora.gui.main_window import MainWindow


DEBUG = False

def main():    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()