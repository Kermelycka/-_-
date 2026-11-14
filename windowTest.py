import sys
import subprocess
import json
import os
import urllib.request
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QLabel, QTextEdit, QSplitter, QMessageBox, QInputDialog)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize

FLATPAK = "/usr/bin/flatpak"
DESC_CACHE_FILE = "flatpak_apps_description.json"

class FlatpakManager(QWidget):
    def __init__(self):
        super().__init__()
        # Загружаем кэш описаний при старте
        self.desc_cache = self.load_description_cache()
        self.initUI()
        self.load_apps_to_list()

    def initUI(self):
        self.setWindowTitle('Менеджер Flatpak')
        self.resize(900, 600)

        main_layout = QHBoxLayout()

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.btn_refresh = QPushButton("🔄 Обновить список")
        self.btn_refresh.clicked.connect(self.load_apps_to_list)
        
        self.btn_install = QPushButton("➕ Установить из Flathub")
        self.btn_install.clicked.connect(self.action_install)
        
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.currentItemChanged.connect(self.on_app_selected)
        
        left_layout.addWidget(self.btn_refresh)
        left_layout.addWidget(self.btn_install)
        left_layout.addWidget(self.list_widget)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        header_layout = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        
        title_layout = QVBoxLayout()
        self.name_label = QLabel("Выберите приложение")
        self.name_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.id_label = QLabel("")
        self.id_label.setStyleSheet("color: gray;")
        title_layout.addWidget(self.name_label)
        title_layout.addWidget(self.id_label)
        
        header_layout.addWidget(self.icon_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.desc_label = QTextEdit()
        self.desc_label.setReadOnly(True)
        self.desc_label.setPlaceholderText("Описание приложения...")

        action_layout = QHBoxLayout()
        self.bth_kill = QPushButton("Закрыть приложение")
        self.btn_run = QPushButton("▶ Запустить")
        self.btn_update = QPushButton("🔄 Обновить")
        self.btn_uninstall = QPushButton("❌ Удалить")
        
        self.bth_kill.clicked.connect(self.action_kill)
        self.btn_run.clicked.connect(self.action_run)
        self.btn_update.clicked.connect(self.action_update)
        self.btn_uninstall.clicked.connect(self.action_uninstall)
        
        action_layout.addWidget(self.bth_kill)
        action_layout.addWidget(self.btn_run)
        action_layout.addWidget(self.btn_update)
        action_layout.addWidget(self.btn_uninstall)

        right_layout.addLayout(header_layout)
        right_layout.addWidget(QLabel("Описание:"))
        right_layout.addWidget(self.desc_label)
        right_layout.addLayout(action_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        self.set_buttons_enabled(False)

    # --- РАБОТА С ОПИСАНИЙ ---
    def load_description_cache(self):
        """Загружает сохраненные описания из файла"""
        if os.path.exists(DESC_CACHE_FILE):
            try:
                with open(DESC_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_description_cache(self):
        """Сохраняет текущий кэш в файл"""
        try:
            with open(DESC_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.desc_cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")

    def get_app_description_from_flathub(self, app_id):
        """Скачивает описание с API Flathub"""
        # Если уже есть в кэше — берем оттуда
        if app_id in self.desc_cache:
            return self.desc_cache[app_id]

        # Если нет — идем в интернет
        try:
            url = f"https://flathub.org/api/v2/appstream/{app_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
                # Берем описание или краткое содержание
                desc = data.get("description", data.get("summary", "Описание отсутствует."))
                
                # Убираем HTML-теги (Flathub отдает описание с HTML тегами)
                desc = re.sub(r'<[^>]+>', '', desc).strip()
                
                # Сохраняем в кэш и на диск
                self.desc_cache[app_id] = desc
                self.save_description_cache()
                
                return desc
        except Exception:
            return "Не удалось загрузить описание с Flathub (проверьте интернет)."
    # -------------------------------

    def set_buttons_enabled(self, enabled):
        self.bth_kill.setEnabled(enabled)
        self.btn_run.setEnabled(enabled)
        self.btn_update.setEnabled(enabled)
        self.btn_uninstall.setEnabled(enabled)

    def load_apps_to_list(self):
        self.list_widget.clear()
        self.name_label.setText("Выберите приложение")
        self.id_label.setText("")
        self.desc_label.clear()
        self.icon_label.clear()
        self.set_buttons_enabled(False)

        command = [FLATPAK, "list", "--app", "--columns=name,application,version"]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line: continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    app_name = parts[0]
                    app_id = parts[1]
                    app_version = parts[2] # Сохраняем версию
                    
                    item = QListWidgetItem(app_name)
                    item.setData(Qt.UserRole, app_id)
                    item.setData(Qt.UserRole + 1, app_version) # Прячем версию в данных
                    
                    icon = QIcon.fromTheme(app_id)
                    if not icon.isNull():
                        item.setIcon(icon)
                        
                    self.list_widget.addItem(item)

    def on_app_selected(self, current, previous):
        if not current: return
        self.load_app_details(current)

    def load_app_details(self, item):
        app_id = item.data(Qt.UserRole)
        app_version = item.data(Qt.UserRole + 1)
        
        self.name_label.setText(item.text())
        self.id_label.setText(app_id)
        self.set_buttons_enabled(True)
        
        # Иконка
        icon = QIcon.fromTheme(app_id)
        if not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(64, 64))
        else:
            self.icon_label.clear()

        # Показываем версию и ставим заглушку, пока грузится описание
        self.desc_label.setText(f"Версия: {app_version}\n\n⏳ Загрузка описания...")
        QApplication.processEvents() # Чтобы интерфейс не замирал
        
        # Берем описание из кэша или скачиваем
        description = self.get_app_description_from_flathub(app_id)
        
        # Выводим итоговый текст
        self.desc_label.setText(f"Версия: {app_version}\n\n{description}")

    def get_current_app_id(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def action_run(self):
        app_id = self.get_current_app_id()
        if app_id:
            subprocess.Popen([FLATPAK, "run", app_id])

    def action_kill(self):
        app_id = self.get_current_app_id()
        if app_id:
            subprocess.Popen([FLATPAK, "kill", app_id])

    def action_update(self):
        app_id = self.get_current_app_id()
        if app_id:
            QMessageBox.information(self, "Обновление", f"Обновление {app_id} началось. Подождите...")
            res = subprocess.run([FLATPAK, "update", "-y", app_id], capture_output=True, text=True)
            if res.returncode == 0:
                QMessageBox.information(self, "Успех", f"{app_id} обновлен!")
            else:
                QMessageBox.warning(self, "Ошибка", res.stderr)
            self.load_apps_to_list()

    def action_uninstall(self):
        app_id = self.get_current_app_id()
        if not app_id: return
        
        reply = QMessageBox.question(self, 'Подтверждение', f'Удалить {app_id}?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            res = subprocess.run([FLATPAK, "remove", "-y", app_id], capture_output=True, text=True)
            if res.returncode == 0:
                QMessageBox.information(self, "Успех", f"{app_id} удален.")
                self.load_apps_to_list()
            else:
                QMessageBox.warning(self, "Ошибка", res.stderr)

    def action_install(self):
        app_id, ok = QInputDialog.getText(self, "Установка приложения", 
                                          "Введите ID приложения из Flathub\n(например: org.kde.krita):")
        if ok and app_id.strip():
            app_id = app_id.strip()
            self.setWindowTitle(f"Установка {app_id}...")
            QApplication.processEvents()
            
            res = subprocess.run([FLATPAK, "install", "-y", "flathub", app_id], capture_output=True, text=True)
            
            self.setWindowTitle('Менеджер Flatpak')
            if res.returncode == 0:
                QMessageBox.information(self, "Успех", f"✅ {app_id} успешно установлено!")
                self.load_apps_to_list()
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось установить:\n{res.stderr}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FlatpakManager()
    window.show()
    sys.exit(app.exec_())