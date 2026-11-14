from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QLabel, QTextEdit, QSplitter, QMessageBox, QInputDialog, QApplication)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize

# Импортируем наш бэкенд!
from backend import FlatpakBackend

class FlatpakManager(QWidget):
    def __init__(self):
        super().__init__()
        self.backend = FlatpakBackend() # Создаем экземпляр бэкенда
        self.initUI()
        self.load_apps_to_list()

    def initUI(self):
        self.setWindowTitle('easy flatpak manager')
        self.resize(900, 600)

        main_layout = QHBoxLayout()
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
        
        action_layout = QHBoxLayout()
        self.btn_kill = QPushButton("Закрыть приложение") # Исправил bth на btn
        self.btn_run = QPushButton("▶ Запустить")
        self.btn_update = QPushButton("🔄 Обновить")
        self.btn_uninstall = QPushButton("❌ Удалить")
        
        self.btn_kill.clicked.connect(self.action_kill)
        self.btn_run.clicked.connect(self.action_run)
        self.btn_update.clicked.connect(self.action_update)
        self.btn_uninstall.clicked.connect(self.action_uninstall)
        
        action_layout.addWidget(self.btn_kill)
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

    def set_buttons_enabled(self, enabled):
        self.btn_kill.setEnabled(enabled)
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

        # Вызываем бэкенд!
        apps = self.backend.get_installed_apps()
        for app_name, app_id, app_version in apps:
            item = QListWidgetItem(app_name)
            item.setData(Qt.UserRole, app_id)
            item.setData(Qt.UserRole + 1, app_version)
            
            icon = QIcon.fromTheme(app_id)
            if not icon.isNull():
                item.setIcon(icon)
            self.list_widget.addItem(item)

    def on_app_selected(self, current, previous):
        if not current: return
        app_id = current.data(Qt.UserRole)
        app_version = current.data(Qt.UserRole + 1)
        
        self.name_label.setText(current.text())
        self.id_label.setText(app_id)
        self.set_buttons_enabled(True)
        
        icon = QIcon.fromTheme(app_id)
        if not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(64, 64))
        else:
            self.icon_label.clear()

        self.desc_label.setText(f"Версия: {app_version}\n\n⏳ Загрузка описания...")
        QApplication.processEvents()
        
        # Вызываем бэкенд!
        description = self.backend.get_app_description(app_id)
        self.desc_label.setText(f"Версия: {app_version}\n\n{description}")

    def get_current_app_id(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def action_run(self):
        app_id = self.get_current_app_id()
        if app_id: self.backend.run_app(app_id)

    def action_kill(self):
        app_id = self.get_current_app_id()
        if app_id: self.backend.kill_app(app_id)

    def action_update(self):
        app_id = self.get_current_app_id()
        if app_id:
            QMessageBox.information(self, "Обновление", f"Обновление {app_id} началось. Подождите...")
            success, error = self.backend.update_app(app_id)
            if success:
                QMessageBox.information(self, "Успех", f"{app_id} обновлен!")
            else:
                QMessageBox.warning(self, "Ошибка", error)
            self.load_apps_to_list()

    def action_uninstall(self):
        app_id = self.get_current_app_id()
        if not app_id: return
        
        reply = QMessageBox.question(self, 'Подтверждение', f'Удалить {app_id}?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, error = self.backend.uninstall_app(app_id)
            if success:
                QMessageBox.information(self, "Успех", f"{app_id} удален.")
                self.load_apps_to_list()
            else:
                QMessageBox.warning(self, "Ошибка", error)

    def action_install(self):
        app_id, ok = QInputDialog.getText(self, "Установка приложения", 
                                          "Введите ID приложения из Flathub\n(например: org.kde.krita):")
        if ok and app_id.strip():
            app_id = app_id.strip()
            self.setWindowTitle(f"Установка {app_id}...")
            QApplication.processEvents()
            
            success, error = self.backend.install_app(app_id)
            
            self.setWindowTitle('Менеджер Flatpak')
            if success:
                QMessageBox.information(self, "Успех", f"✅ {app_id} успешно установлено!")
                self.load_apps_to_list()
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось установить:\n{error}")