# -*- coding: utf-8 -*-
# codesaver/core/config.py
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "codesaver_system.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".codesaver")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.project_root = ""
        self.hidden_folders = []
        self.font_family = "Tahoma"
        self.font_size = 12
        self.language = "en"  # Default language set to English
        
        # User account information
        self.username = "Guest"
        self.email = "Not Logged In"
        self.days_remaining = 0

    def load(self):
        if not os.path.exists(self.config_file):
            logging.info("Configuration file not found. Default values applied.")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.project_root = data.get("project_root", "")
                self.hidden_folders = data.get("hidden_folders", [])
                self.font_family = data.get("font_family", "Tahoma")
                
                # 🚀 FIX: Validation check to guarantee font_size is always a valid integer
                raw_size = data.get("font_size", 12)
                if isinstance(raw_size, int) and raw_size > 0:
                    self.font_size = raw_size
                else:
                    self.font_size = 12  # Fallback to default safe value
                    
                self.language = data.get("language", "en")
                self.username = data.get("username", "Guest")
                self.email = data.get("email", "Not Logged In")
                self.days_remaining = data.get("days_remaining", 0)
            logging.info("User settings loaded successfully.")
        except json.JSONDecodeError as e:
            logging.error(f"JSON configuration file syntax error: {e}")
        except PermissionError as e:
            logging.error(f"Permission denied to read configuration file: {e}")
        except Exception as e:
            logging.error(f"Unknown error loading settings: {e}")

    def save(self):
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)

            data = {
                "project_root": self.project_root,
                "hidden_folders": self.hidden_folders,
                "font_family": self.font_family,
                "font_size": self.font_size,
                "language": self.language,
                "username": self.username,
                "email": self.email,
                "days_remaining": self.days_remaining
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info("New settings successfully saved to disk.")
        except PermissionError as e:
            # 🚀 FIX: Safe handling for Read-Only or locked permission scenarios
            logging.error(f"Permission error while overwriting configuration file: {e}")
        except Exception as e:
            logging.error(f"Error saving structured configuration data: {e}")