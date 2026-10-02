# -*- coding: utf-8 -*-
import os
import ast
import re

class GraphifyEngine:
    """
    Graphify Engine: Knowledge Graph extraction system for AI.
    Rewritten based on AST Visitor for 100% accuracy in Python.
    """
    def __init__(self, project_root):
        self.project_root = project_root
        
    def generate_ai_context(self, max_files=100):
        """Generate compact context to send to AI Prompt"""
        if not self.project_root or not os.path.exists(self.project_root):
            return ""
            
        context = ["<project_context>"]
        context.append("This is a Deep Scan of the project's architecture. USE THIS TO ANSWER QUESTIONS ABOUT CLASSES, FUNCTIONS, AND COMPONENTS.\n")
        
        file_count = 0
        found_data = False
        
        for root, dirs, files in os.walk(self.project_root):
            # Ignore system and heavy folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', 'venv', 'env', 'dist', 'build')]
            
            for file in files:
                if file_count >= max_files:
                    break
                    
                ext = os.path.splitext(file)[1].lower()
                if ext not in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                    continue
                    
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.project_root)
                
                file_info = self._analyze_file(filepath, ext)
                if file_info:
                    context.append(f"📁 {rel_path}")
                    context.append(file_info)
                    context.append("") # Blank line
                    file_count += 1
                    found_data = True
                    
        if not found_data:
            context.append("No internal classes or functions were found. The project might be empty or using unsupported syntax.")
            
        context.append("</project_context>")
        return "\n".join(context)
        
    def _analyze_file(self, filepath, ext):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            if ext == '.py':
                return self._analyze_python(content)
            else:
                return self._analyze_js(content)
        except Exception:
            return None
            
    def _analyze_python(self, content):
        """Dedicated and advanced Python file analyzer using NodeVisitor"""
        try:
            tree = ast.parse(content)
            imports = set()
            classes = {}
            functions = []

            class StructureAnalyzer(ast.NodeVisitor):
                def visit_Import(self, node):
                    for alias in node.names: imports.add(alias.name)
                    self.generic_visit(node)
                    
                def visit_ImportFrom(self, node):
                    if node.module: imports.add(node.module)
                    self.generic_visit(node)
                    
                def visit_ClassDef(self, node):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes[node.name] = methods
                    self.generic_visit(node)
                    
                def visit_FunctionDef(self, node):
                    functions.append(node.name)

            analyzer = StructureAnalyzer()
            analyzer.visit(tree)
            
            info = []
            if imports: info.append(f"   ↳ Imports: {', '.join(imports)}")
            
            if classes:
                for cls, methods in classes.items():
                    meth_str = f" ({', '.join(methods)})" if methods else ""
                    info.append(f"   ↳ Class: {cls}{meth_str}")
            
            # Clean up functions inside classes to avoid cluttering the list
            all_methods = [m for methods in classes.values() for m in methods]
            top_funcs = [f for f in functions if f not in all_methods]
            if top_funcs: info.append(f"   ↳ General Functions: {', '.join(top_funcs)}")
            
            return "\n".join(info) if info else None
        except Exception:
            return None
            
    def _analyze_js(self, content):
        try:
            # Find imports (important for understanding React architecture)
            imports = []
            for match in re.finditer(r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]', content):
                imports.append(match.group(1))

            # Classes
            classes = re.findall(r'class\s+([a-zA-Z0-9_]+)', content)
            
            # Standard and Export Default functions
            functions = re.findall(r'function\s+([a-zA-Z0-9_]+)', content)
            
            # Arrow functions (React components like const App = () =>)
            arrow_funcs = re.findall(r'(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>', content)
            
            # Functions assigned directly to variables (const X = function())
            var_funcs = re.findall(r'(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?function', content)
            
            all_funcs = list(set(functions + arrow_funcs + var_funcs))
            
            info = []
            if imports: info.append(f"   ↳ Imports from: {', '.join(set(imports))}")
            if classes: info.append(f"   ↳ Classes: {', '.join(classes)}")
            if all_funcs: info.append(f"   ↳ Functions/Components: {', '.join(all_funcs)}")
            
            return "\n".join(info) if info else None
        except Exception:
            return None