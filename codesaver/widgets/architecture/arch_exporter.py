# codesaver/widgets/arch_exporter.py
from PySide6.QtWidgets import QFileDialog, QMessageBox

class ArchitectureExporter:
    @staticmethod
    def export_to_md(parent_widget, graph_nodes, graph_links, health_data):
        if not graph_nodes:
            QMessageBox.warning(parent_widget, "Error", "No data to export.")
            return

        title = "Save Markdown File"
        file_path, _ = QFileDialog.getSaveFileName(parent_widget, title, "project_architecture.md", "Markdown Files (*.md)")
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Project Architecture Map\n\n")
                if health_data:
                    f.write("## 📊 Health Dashboard\n")
                    f.write(f"- **Health Score:** {health_data.get('score', 0)}/100\n")
                    f.write(f"- **Total Files:** {health_data.get('total_files', 0)}\n")
                    f.write(f"- **Buggy Cycles:** {health_data.get('cycles_count', 0)}\n")
                    f.write(f"- **Isolated Files:** {health_data.get('isolated_count', 0)}\n\n")
                
                f.write("## 🗂️ Modules & Files\n\n")
                
                sorted_nodes = sorted(graph_nodes, key=lambda x: (x.get('group', ''), x.get('name', '')))
                current_group = None
                
                for node in sorted_nodes:
                    if node.get('group') != current_group:
                        current_group = node.get('group')
                        f.write(f"### 📁 {current_group}\n")
                        
                    f.write(f"#### 📄 `{node.get('name', '')}`\n")
                    f.write(f"- **Path:** `{node.get('id', '')}`\n")
                    f.write(f"- **Lines of Code:** {node.get('loc', 0)}\n")
                    
                    incoming = [link['source'] for link in graph_links if link.get('target') == node.get('id')]
                    outgoing = [link['target'] for link in graph_links if link.get('source') == node.get('id')]
                    
                    if incoming:
                        f.write(f"- **📥 Imported By:**\n")
                        for inc in incoming:
                            f.write(f"  - `{inc}`\n")
                    if outgoing:
                        f.write(f"- **📤 Imports:**\n")
                        for out in outgoing:
                            f.write(f"  - `{out}`\n")
                    f.write("\n")
            
            success_title = "Success"
            success_msg = f"File successfully saved:\n{file_path}"
            QMessageBox.information(parent_widget, success_title, success_msg)
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", str(e))