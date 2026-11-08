#Проверить что ls показывает test.py и flatpak_apps.txt перед запуском, а то будет неочень.
import subprocess

# Путь к flatpak и к списку с приложениями(в будущем сделать универсальным)
FLATPAK = "/usr/bin/flatpak"
FILENAME = "flatpak_apps.txt"

def get_flatpak_list():
    """Получает список приложений, сохраняет в файл и возвращает текст."""
    # Просим flatpak выдать данные через табуляцию для удобного разбора
    command = [FLATPAK, "list", "--app", "--columns=name,application,version"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0: # если все прошло норм то
        # Сохраняем в файл
        with open(FILENAME, "w", encoding="utf-8") as f: # оnкрываем txt где будут все нужные данные
            f.write(result.stdout) # пишем туда всю инфу
        print(f"Список сохранен в файл {FILENAME}") 
        return result.stdout
    else: # если ошибка появилась то
        print(f"Ошибка при получении списка: {result.stderr}")
        return ""

def get_flatpak_version():
    """Получает версию flatpak."""
    result = subprocess.run([FLATPAK, "--version"], capture_output=True, text=True)
    return result.stdout.strip()

def parse_and_show_saved_list():
    """Читает файл и разбирает его на составляющие."""
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Разбиваем строку по табуляции
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0]
                    app_id = parts[1]
                    version = parts[2]
                    
                    # Выводим так, как можно понять:
                    print(f"Приложение: {name} | ID: {app_id} | Версия: {version}")
    except FileNotFoundError:
        print(f"Файл {FILENAME} не найден. Сначала выберите пункт 1.")

def del_flatpak_app(app_id):
    del_resalt = subprocess.run([FLATPAK, "remove","-y", app_id], capture_output=True, text=True)
    if del_resalt.returncode == 0:
        return f"Успешно удалено: {app_id}\n{del_resalt.stderr.strip()}"
    else:
        return f"Ошибка при удалении {app_id}:\n{del_resalt.stderr.strip()}"

def install_flatpak_app(app_id):
    print("Устанваливаем ",app_id)
    install_resalt = subprocess.run([FLATPAK,"install","-y","flathub", app_id], capture_output=True, text=True)
    if install_resalt.returncode == 0:
        return f"Успешна установка: {app_id}\n{install_resalt.stderr.strip()}"
    else:
        return f"Ошибка при установке {app_id}:\n{install_resalt.stderr.strip()}"

# --- Основной цикл программы ---
while True:
    print("\nМеню:")
    print("1 - посмотреть и сохранить список приложений flatpak")
    print("2 - посмотреть версию flatpak")
    print("3 - удалить приложение из пакетов flatpak")
    print("4 - установить приложение из flathub")
    print("0 - выход")
    
    choice = input("Ваш выбор: ")

    if choice == "1":
        print("\nТекущие приложения:")
        get_flatpak_list()
        parse_and_show_saved_list()  # Выводим то, что получили
        
    elif choice == "2":
        print(f"\nВерсия Flatpak: {get_flatpak_version()}")

    elif choice == "3":
        what_app = input("Какое приложение удалить (пример : com.google.Chrome) : ")
        print(del_flatpak_app(what_app))

    elif choice == "4":
        what_app = input("Какое придожение хотите установить из flathub (пример : com.google.Chrome) : ")
        print(install_flatpak_app(what_app))
        
    elif choice == "0":
        print("Выход из программы.")
        break
        
    else:
        print("Неверный ввод. Попробуйте снова.")