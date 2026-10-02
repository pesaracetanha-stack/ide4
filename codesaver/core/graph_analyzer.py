# codesaver/core/graph_analyzer.py
import os
import re
import ast
import subprocess
import concurrent.futures
import networkx as nx
from PySide6.QtCore import QThread, Signal

class GraphWorker(QThread):
    finished = Signal(dict)
    progress = Signal(int)
    log_msg = Signal(str)

    def __init__(self, root_dir, supported_exts, commit_hash=None):
        super().__init__()
        self.root_dir = root_dir
        self.supported_exts = supported_exts
        self.commit_hash = commit_hash

    def get_file_color(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.supported_exts: 
            return self.supported_exts[ext][1]
        return '#8b949e'

    def read_file_content(self, rel_path):
        if self.commit_hash:
            git_path = rel_path.replace('\\', '/')
            try:
                result = subprocess.run(['git', 'show', f'{self.commit_hash}:{git_path}'], 
                                      cwd=self.root_dir, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0: 
                    return result.stdout
            except: 
                pass
            return ""
        else:
            try:
                with open(os.path.join(self.root_dir, rel_path), 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e: 
                self.log_msg.emit(f"Warning: Could not load {rel_path} - {str(e)}")
                return ""

    def extract_imports(self, rel_path, content):
        imports = []
        current_dir = os.path.dirname(rel_path).replace('\\', '/')
        current_dir_parts = current_dir.split('/') if current_dir else []

        try:
            if rel_path.endswith('.py'):
                tree = ast.parse(content, filename=rel_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names: 
                            imports.append(alias.name.replace('.', '/'))
                    elif isinstance(node, ast.ImportFrom):
                        lvl = node.level
                        mod = node.module.replace('.', '/') if node.module else ""
                        base_path = ""
                        
                        if lvl > 0:
                            if lvl <= len(current_dir_parts) + 1:
                                base_parts = current_dir_parts[:len(current_dir_parts) - lvl + 1]
                                base_path = '/'.join(base_parts)
                        
                        if lvl > 0:
                            mod_path = f"{base_path}/{mod}".strip('/') if mod else base_path
                        else:
                            mod_path = mod
                            
                        imports.append(mod_path)
                        for alias in node.names:
                            imports.append(f"{mod_path}/{alias.name}".strip('/'))

            elif rel_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.vue')):
                patterns = [
                    r'import\s+(?:(?:\w+\s*,)?\s*\{[^}]+\}\s*|\w+\s+)?from\s*[\'"]([^\'"]+)[\'"]',
                    r'import\s*[\'"]([^\'"]+)[\'"]',
                    r'export\s+.*\s+from\s*[\'"]([^\'"]+)[\'"]',
                    r'(?:require|import)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
                ]
                for p in patterns:
                    for m in re.findall(p, content):
                        raw_import = m.strip()
                        for ext in ['.js', '.jsx', '.ts', '.tsx', '.vue']:
                            if raw_import.endswith(ext):
                                raw_import = raw_import[:-len(ext)]
                                break
                        
                        if raw_import.startswith('.'):
                            try:
                                import_path = os.path.normpath(os.path.join(current_dir, raw_import)).replace('\\', '/')
                                imports.append(import_path)
                            except: pass
                        elif raw_import.startswith('@/'):
                            imports.append('src/' + raw_import[2:])
                        else:
                            imports.append(raw_import)
            
            elif rel_path.endswith(('.c', '.cpp', '.h', '.hpp')):
                for m in re.findall(r'#include\s*["<]([^">]+)[">]', content): 
                    imports.append(os.path.splitext(os.path.basename(m))[0])
            
            elif rel_path.endswith(('.java', '.cs', '.php', '.kt')):
                for m in re.findall(r'(?:import|using|require_once|include_once)\s+([a-zA-Z0-9_\.]+)', content): 
                    imports.append(m.replace('.', '/').rstrip(';'))
            
            elif rel_path.endswith('.rs'):
                for m in re.findall(r'(?:use|mod)\s+([a-zA-Z0-9_:]+)', content): 
                    imports.append(m.replace('::', '/').rstrip(';'))
            
            elif rel_path.endswith('.swift'):
                for m in re.findall(r'import\s+([a-zA-Z0-9_]+)', content): 
                    imports.append(m)

        except Exception: 
            pass
            
        return imports

    def process_single_file(self, file_info):
        full_path, rel_path = file_info
        file_name = os.path.basename(rel_path)
        top_folder = rel_path.split('/')[0] if '/' in rel_path else "Root"
        node_color = self.get_file_color(file_name)
        content = self.read_file_content(rel_path)
        loc = len(content.splitlines())
        deps = self.extract_imports(rel_path, content)
        return rel_path, file_name, top_folder, node_color, loc, deps

    def run(self):
        try:
            ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode', 'dist', 'build', '.codesaver'}
            all_files_info = []
            watched_dirs = set()
            valid_extensions = tuple(self.supported_exts.keys()) + ('.htm', '.yml', '.json', '.md')
            detected_exts = set()

            path_map = {}
            name_map = {}

            if self.commit_hash:
                result = subprocess.run(['git', 'ls-tree', '-r', '--name-only', self.commit_hash], cwd=self.root_dir, capture_output=True, text=True)
                for f in result.stdout.strip().split('\n'):
                    if f.endswith(valid_extensions):
                        all_files_info.append((os.path.join(self.root_dir, f), f))
                        ext = os.path.splitext(f)[1].lower()
                        if ext in self.supported_exts: detected_exts.add(ext)
            else:
                for root, dirs, files in os.walk(self.root_dir):
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]
                    watched_dirs.add(root)
                    for file in files:
                        if file.endswith(valid_extensions):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, self.root_dir).replace('\\', '/')
                            all_files_info.append((full_path, rel_path))
                            ext = os.path.splitext(file)[1].lower()
                            if ext in self.supported_exts: detected_exts.add(ext)
            
            total = len(all_files_info)
            if total == 0:
                self.finished.emit({"error": f"<h2 style='color:#8b949e; text-align:center; margin-top:50px;'>No processable files found in the project.</h2>"})
                return

            for full_path, rel_path in all_files_info:
                path_without_ext = os.path.splitext(rel_path)[0].replace('\\', '/')
                name_without_ext = os.path.splitext(os.path.basename(rel_path))[0]
                
                path_map[path_without_ext] = rel_path
                
                parts = path_without_ext.split('/')
                if len(parts) > 1:
                    alt_path = '/'.join(parts[1:])
                    if alt_path not in path_map:
                        path_map[alt_path] = rel_path
                
                if name_without_ext not in name_map:
                    name_map[name_without_ext] = []
                name_map[name_without_ext].append(rel_path)

            graph = nx.DiGraph()
            processed_count = 0
            last_progress = -1 
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self.process_single_file, info): info for info in all_files_info}
                for future in concurrent.futures.as_completed(futures):
                    rel_path, file_name, top_folder, node_color, loc, deps = future.result()
                    graph.add_node(rel_path, name=file_name, label=file_name, color=node_color, path=rel_path, group=top_folder, loc=loc)
                    
                    for dep in deps:
                        matched = False
                        if dep in path_map:
                            target_rel_path = path_map[dep]
                            if rel_path != target_rel_path:
                                graph.add_edge(rel_path, target_rel_path)
                            matched = True
                        
                        if not matched:
                            dep_name = dep.split('/')[-1]
                            if dep_name in name_map:
                                target_rel_path = name_map[dep_name][0]
                                if rel_path != target_rel_path:
                                    graph.add_edge(rel_path, target_rel_path)
                    
                    processed_count += 1
                    current_progress = int((processed_count / total) * 100)
                    if current_progress != last_progress:
                        self.progress.emit(current_progress)
                        last_progress = current_progress

            try:
                cycles = list(nx.simple_cycles(graph))
                cycle_edges = set()
                cycle_paths = []
                for cycle in cycles:
                    path_str = " ➔ ".join(cycle) + f" ➔ {cycle[0]}"
                    cycle_paths.append(path_str)
                    
                    for j in range(len(cycle)): 
                        cycle_edges.add((cycle[j], cycle[(j+1) % len(cycle)]))
            except:
                cycles = []
                cycle_edges = set()
                cycle_paths = []

            # 🚀 NEW LOGIC: Intelligent filter for naturally isolated files
            def is_naturally_isolated(file_path):
                p = file_path.lower().replace('\\', '/')
                name = os.path.basename(p)
                if name == '__init__.py': 
                    return True
                if name.endswith(('.html', '.js', '.json', '.md', '.css')): 
                    return True
                if 'plugins/' in p or p.startswith('plugins'): 
                    return True
                return False

            all_isolated = [n for n, d in graph.degree() if d == 0]
            true_isolated = [n for n in all_isolated if not is_naturally_isolated(n)]

            health_score = max(0, 100 - (len(cycles) * 5) - (len(true_isolated) * 2))
            
            health_data = {
                "score": health_score, 
                "total_files": total, 
                "cycles_count": len(cycles),
                "cycle_paths": cycle_paths,
                "isolated_count": len(true_isolated),
                "top_hubs": [os.path.basename(n) for n in sorted(graph.nodes(), key=lambda n: graph.degree(n), reverse=True)[:5]],
                "watched_dirs": list(watched_dirs) 
            }

            nodes_data = []
            links_data = []

            import urllib.parse
            for node_id, attrs in graph.nodes(data=True):
                in_degree = graph.in_degree(node_id)
                out_degree = graph.out_degree(node_id)
                file_ext = os.path.splitext(attrs['name'])[1].lower() or '.other'
                
                in_names = [graph.nodes[src]['name'] for src, _ in graph.in_edges(node_id)]
                out_names = [graph.nodes[tgt]['name'] for _, tgt in graph.out_edges(node_id)]
                
                in_list_html = "<br>".join([f"• {name}" for name in in_names]) if in_names else "No files"
                out_list_html = "<br>".join([f"• {name}" for name in out_names]) if out_names else "No files"
                
                panel_html = f"""
                    <div style='font-size: 18px; color: {attrs['color']}; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px;'>{attrs['name']}</div>
                    <div style='margin-bottom: 10px;'><b>Path:</b> <span style='color: #8b949e;'>{attrs['path']}</span></div>
                    <div style='margin-bottom: 10px;'><b>Lines of Code:</b> <span style='color: #a371f7;'>{attrs['loc']}</span></div>
                    <hr style='border: 0; border-top: 1px solid #30363d; margin: 15px 0;'>
                    <div style='margin-bottom: 10px;'>📥 <b>Incoming (Imported by):</b> <span style='color: #58a6ff;'>{in_degree}</span></div>
                    <div style='margin-bottom: 15px;'>📤 <b>Outgoing (Imports):</b> <span style='color: #d29922;'>{out_degree}</span></div>
                    
                    <button onclick="var d=document.getElementById('deps-{node_id}'); d.style.display=d.style.display==='none'?'block':'none';" style='width: 100%; padding: 8px; background: #1f6feb; color: white; border: none; border-radius: 5px; font-family: Tahoma; cursor: pointer; margin-bottom: 10px;'>📋 View Related Files</button>
                    <div id='deps-{node_id}' style='display: none; margin-bottom: 10px; background: rgba(0,0,0,0.4); padding: 12px; border-radius: 6px; font-size: 12px; max-height: 150px; overflow-y: auto; border: 1px solid #30363d;'>
                        <b style='color: #58a6ff;'>Files that import this:</b><br>
                        <span style='color: #c9d1d9; line-height: 1.6;'>{in_list_html}</span><br><br>
                        <b style='color: #d29922;'>Files imported by this:</b><br>
                        <span style='color: #c9d1d9; line-height: 1.6;'>{out_list_html}</span>
                    </div>
                """
                
                svg_icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 444 572"><path fill="{attrs["color"]}" stroke="#0d1117" stroke-width="30" d="M224 136V0H24C10.7 0 0 10.7 0 24v464c0 13.3 10.7 24 24 24h336c13.3 0 24-10.7 24-24V160H248c-13.2 0-24-10.8-24-24zm160-14.1v6.1H256V0h6.1c6.4 0 12.5 2.5 17 7l97.9 98c4.5 4.5 7 10.6 7 16.9z"/></svg>'
                
                nodes_data.append({
                    "id": node_id, "name": attrs['name'], "group": attrs['group'], "loc": attrs['loc'],
                    "color": attrs['color'], "ext": file_ext, "val": 5 + ((in_degree + out_degree) * 1.5), 
                    "size2d": 28 + ((in_degree + out_degree) * 4), 
                    "svgIcon": "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(svg_icon),
                    "panelContent": panel_html
                })

            for source, target in graph.edges():
                links_data.append({"source": source, "target": target, "is_cycle": (source, target) in cycle_edges})

            self.finished.emit({
                "health": health_data, 
                "detected_exts": list(detected_exts),
                "nodes": nodes_data,
                "links": links_data
            })
            
            if self.commit_hash: 
                self.log_msg.emit(f"Graph rendered for commit {self.commit_hash}.")
            else: 
                self.log_msg.emit("File processing completed.")

        except Exception as e:
            self.log_msg.emit(f"Critical Error: {str(e)}")
            self.finished.emit({"error": f"<h3 style='color:#f85149; text-align:center;'>Error processing files</h3>"})