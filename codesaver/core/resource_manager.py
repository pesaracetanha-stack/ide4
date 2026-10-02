# -*- coding: utf-8 -*-
# codesaver/core/resource_manager.py
import sys
import os
import ctypes

class ResourceManager:
    @staticmethod
    def get_path(relative_path):
        """
        مسیر دقیق فایل‌ها را پیدا می‌کند.
        اگر برنامه exe شده باشد، از پوشه‌ی موقت (MEIPASS) می‌خواند.
        اگر در محیط توسعه باشد، از مسیر اصلی پروژه می‌خواند.
        """
        try:
            # حالت اجرای فایل .exe (کامپایل شده)
            base_path = sys._MEIPASS
        except AttributeError:
            # حالت توسعه (Development Mode)
            # دو پوشه به عقب برمی‌گردیم تا به روتِ پروژه برسیم
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        return os.path.join(base_path, relative_path)

    @staticmethod
    def setup_windows_app_id(app_id="HPR.CodeSaver.IDE.v4"):
        """
        این متد به ویندوز می‌فهماند که این یک برنامه‌ی مستقل است، نه یک اسکریپت ساده‌ی پایتون.
        بدون این متد، ویندوز آیکونِ اختصاصی تو را در تسک‌بار (Taskbar) نمایش نخواهد داد!
        """
        if sys.platform == 'win32':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception:
                pass