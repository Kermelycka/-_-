import sys
import os
import shutil

# --- НАСТРОЙКА ПУТЕЙ ---
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)

# --- ПРОВЕРКА ЗАВИСИМОСТЕЙ ---
def check_dependencies():
    # 1. Проверяем, установлен ли Flatpak в системе
    if not shutil.which('flatpak') and not os.path.exists('/usr/bin/flatpak'):
        print("Ошибка: flatpak не найдена в системе.")
        print("Пожалуйста, установите flatpak перед запуском программы.")
        sys.exit(1)

    # 2. Проверяем, установлена ли библиотека PyQt5
    try:
        import PyQt5
    except ImportError:
        print("Ошибка: Библиотека PyQt5 не установлена.")
        print("Выполните команду: pip install -r requirements.txt")
        sys.exit(1)

# --- ЗАПУСК ---
if __name__ == '__main__':
    print("Запуск Flatpak Менеджера...")
    check_dependencies()
    
    # Импортируем и запускаем главную функцию из main.py
    try:
        from main import main
        main()
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при запуске:\n{e}")