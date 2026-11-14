import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon # <--- Импортируем QIcon
from ui import FlatpakManager

def main():
    app = QApplication(sys.argv)
    
    # Вычисляем путь к иконке. 
    # __file__ - это путь к main.py (папка src). 
    # Нам нужно подняться на уровень выше (в корень) и зайти в assets.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "assets", "icon.png")
    
    # Устанавливаем иконку для всего приложения
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = FlatpakManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()