import subprocess
import json
import os
import urllib.request
import urllib.error
import re
import requests

FLATPAK = "/usr/bin/flatpak"
DESC_CACHE_FILE = "flatpak_apps_description.json"

class FlatpakBackend:
    def __init__(self):
        self.desc_cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(DESC_CACHE_FILE):
            try:
                with open(DESC_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(DESC_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.desc_cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")

    def get_installed_apps(self):
        command = [FLATPAK, "list", "--app", "--columns=name,application,version"]
        result = subprocess.run(command, capture_output=True, text=True)
        
        apps = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line: continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    apps.append((parts[0], parts[1], parts[2]))
        return apps

    def get_app_description(self, app_id):
        if app_id in self.desc_cache and "Не удалось" not in self.desc_cache[app_id]:
            return self.desc_cache[app_id]

        url = f"https://flathub.org/api/v2/appstream/{app_id}"
        
        try:
            # Делаем запрос с таймаутом
            response = requests.get(url, timeout=10)
            
            # Если ответ 200 OK
            if response.status_code == 200:
                data = response.json()
                desc = data.get("description", data.get("summary", ""))
                
                if not desc:
                    desc = "Описание отсутствует."
                    
                desc = re.sub(r'<[^>]+>', '', desc).strip()
                self.desc_cache[app_id] = desc
                self._save_cache()
                return desc
            elif response.status_code == 404:
                return "Приложение не найдено в базе Flathub."
            else:
                return f"Ошибка сервера: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            print(f"Сетевая ошибка: {e}")
            return "Не удалось загрузить описание (проверьте интернет или VPN)."
        
    def run_app(self, app_id):
        subprocess.Popen([FLATPAK, "run", app_id])

    def kill_app(self, app_id):
        subprocess.Popen([FLATPAK, "kill", app_id])

    def update_app(self, app_id):
        res = subprocess.run([FLATPAK, "update", "-y", app_id], capture_output=True, text=True)
        return res.returncode == 0, res.stderr

    def uninstall_app(self, app_id):
        res = subprocess.run([FLATPAK, "remove", "-y", app_id], capture_output=True, text=True)
        return res.returncode == 0, res.stderr

    def install_app(self, app_id):
        res = subprocess.run([FLATPAK, "install", "-y", "flathub", app_id], capture_output=True, text=True)
        return res.returncode == 0, res.stderr