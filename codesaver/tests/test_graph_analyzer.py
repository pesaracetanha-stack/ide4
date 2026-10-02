# -*- coding: utf-8 -*-
# codesaver/tests/test_graph_analyzer.py
import pytest
from core.graph_analyzer import GraphWorker

def test_graph_analyzer_discovers_dependencies(tmp_path, qtbot):
    project_dir = tmp_path / "fake_project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("import helper\n", encoding="utf-8")
    (project_dir / "helper.py").write_text("import os\n", encoding="utf-8")
    
    ext_pool = {'.py': ('Python', '#9b59b6')}
    worker = GraphWorker(str(project_dir), ext_pool)
    
    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.start()
        
    result_data = blocker.args[0]
    assert "nodes" in result_data and "links" in result_data
    node_names = [n.get("name", "") for n in result_data["nodes"]]
    assert "main.py" in node_names
    assert "helper.py" in node_names

def test_graph_analyzer_survives_circular_imports_and_bad_encoding(tmp_path, qtbot):
    project_dir = tmp_path / "chaos_project"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("import b\n", encoding="utf-8")
    (project_dir / "b.py").write_text("import a\n", encoding="utf-8")
    (project_dir / "corrupt.py").write_bytes(b'\xff\xfe\x00\x00\x01\x02')
    
    worker = GraphWorker(str(project_dir), {'.py': ('Python', '#9b59b6')})
    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.start()
        
    result_data = blocker.args[0]
    assert result_data["health"]["cycles_count"] > 0
    assert len(result_data["nodes"]) >= 2