# codesaver/core/restore_points.py
import os
import json
import zipfile
import datetime
from PySide6.QtCore import QObject, Signal

class RestorePointManager(QObject):
    progress = Signal(int, str)

    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root
        self.rp_dir = os.path.join(project_root, ".codesaver", "restorepoints")
        os.makedirs(self.rp_dir, exist_ok=True)

    def create_restore_point(self, name):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        zip_name = f"{safe_name}_{timestamp}.zip"
        zip_path = os.path.join(self.rp_dir, zip_name)

        total_files = 0
        for root, dirs, files in os.walk(self.project_root):
            if ".codesaver" in root.split(os.sep):
                continue
            total_files += len(files)
        processed = 0

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.project_root):
                if ".codesaver" in root.split(os.sep):
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.project_root)
                    zipf.write(file_path, arcname)
                    processed += 1
                    percent = int(processed * 100 / total_files) if total_files else 0
                    self.progress.emit(percent, f"Zipping: {arcname}")

        meta = {"name": safe_name, "timestamp": timestamp, "created": datetime.datetime.now().isoformat()}
        meta_path = os.path.join(self.rp_dir, f"{safe_name}_{timestamp}.json")
        with open(meta_path, 'w') as f:
            json.dump(meta, f)
        self.progress.emit(100, "Done")

    def list_restore_points(self):
        points = []
        for f in os.listdir(self.rp_dir):
            if f.endswith(".json"):
                meta_path = os.path.join(self.rp_dir, f)
                try:
                    with open(meta_path, 'r') as mf:
                        meta = json.load(mf)
                    points.append((meta['name'], meta['timestamp']))
                except:
                    continue
        return points

    def restore_restore_point(self, name):
        zip_path = None
        for f in os.listdir(self.rp_dir):
            if f.startswith(name + "_") and f.endswith(".zip"):
                zip_path = os.path.join(self.rp_dir, f)
                break
        if not zip_path:
            raise FileNotFoundError(f"No restore point found with name {name}")

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            total = len(file_list)
        extracted = 0
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for info in zipf.infolist():
                zipf.extract(info, self.project_root)
                extracted += 1
                percent = int(extracted * 100 / total) if total else 0
                self.progress.emit(percent, f"Restoring: {info.filename}")
        self.progress.emit(100, "Restore complete")