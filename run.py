import sys
import os
import time
import logging
import base64
import ctypes

# Force Windows to recognize this as a unique application and bypass icon cache
try:
    app_id = "HPR.CodeSaver.IDE.v4.2"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except Exception:
    pass

# =====================================================================
# Engine Settings: Ensure compatibility and disable hardware acceleration
# =====================================================================

chromium_flags = [
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-webgl",
    "--no-sandbox",
    "--log-level=3"
]
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(chromium_flags)
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QT_OPENGL"] = "software"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

if "--disable-gpu" not in sys.argv:
    sys.argv.extend(["--disable-gpu", "--no-sandbox"])

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from codesaver.main import MainWindow

try:
    from codesaver.core import splash_data
except ImportError:
    splash_data = None

def get_splash_pixmap():
    if not splash_data:
        return None
        
    img_data = None
    for var_name in dir(splash_data):
        if not var_name.startswith("__"):
            val = getattr(splash_data, var_name)
            if isinstance(val, (str, bytes)):
                img_data = val
                break
                
    if img_data:
        try:
            if isinstance(img_data, str):
                img_data = base64.b64decode(img_data)
                
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            
            if not pixmap.isNull():
                return pixmap
        except Exception as e:
            print(f"Error decoding splash data: {e}")
            
    return None

def start_app_with_splash():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Ultimate Taskbar Fix: Extract icon directly from the running EXE file
    try:
        if getattr(sys, 'frozen', False):
            app.setWindowIcon(QIcon(sys.executable))
        else:
            from codesaver.core.resource_manager import ResourceManager
            icon_path = ResourceManager.get_path("app_icon.ico")
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"Failed to set global icon: {e}")
    
    splash_image = get_splash_pixmap()
    splash = None
    
    if splash_image:
        splash = QSplashScreen(splash_image, Qt.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
        time.sleep(5)
    
    try:
        window = MainWindow()
        window.show()
        
        if splash:
            splash.finish(window)
            
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting app: {e}")

if __name__ == "__main__":
    start_app_with_splash()