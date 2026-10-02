# codesaver/widgets/arch_bridge.py
import os
import shutil
from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtGui import QDesktopServices

class Bridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

    @Slot(str)
    def save_related_files(self, node_id):
        if not self.main_window.graph_nodes or not self.main_window.graph_links:
            QMessageBox.warning(self.main_window, "Error", "Graph data is not available.")
            return

        neighbors = set([node_id])
        for link in self.main_window.graph_links:
            src = link['source']
            tgt = link['target']
            if src == node_id:
                neighbors.add(tgt)
            elif tgt == node_id:
                neighbors.add(src)

        target_dir = QFileDialog.getExistingDirectory(self.main_window, "Select folder to save related files")
        if not target_dir:
            return

        main_dir = os.path.join(target_dir, f"files_{node_id.replace('/', '_')}")
        os.makedirs(main_dir, exist_ok=True)

        root_dir = self.main_window.project_root
        if not root_dir: return
        
        copied_count = 0

        for nid in neighbors:
            node = next((n for n in self.main_window.graph_nodes if n['id'] == nid), None)
            if not node:
                continue
            rel_path = node['id']
            full_path = os.path.join(root_dir, rel_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                dest_path = os.path.join(main_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)
                copied_count += 1

        list_file = os.path.join(main_dir, "_file_list.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(f"Main File: {node_id}\n")
            f.write(f"Total Related Files: {len(neighbors)}\n")
            f.write("="*50 + "\n")
            for nid in sorted(neighbors):
                f.write(f"{nid}\n")

        QMessageBox.information(self.main_window, "Success", f"{copied_count} files successfully copied to:\n{main_dir}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(main_dir))

    @Slot(str)
    def open_in_editor(self, node_id):
        self.main_window.open_file_requested.emit(node_id)