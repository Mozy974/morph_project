"""
Tests unitaires pour le composant WebGL 3D GLSL Skill Evolution (tests/test_webgl_skill_evolution.py).
"""

import os
import pytest
from orchestrator.agents.webgl_skill_component import render_webgl_skill_evolution


def test_webgl_skill_evolution_html_exists():
    html_path = "static/webgl_skill_evolution.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "WebGL 3D Skill Evolution Radar" in content
    assert "THREE.WebGLRenderer" in content
    assert "THREE.GridHelper(16, 32, 0x00f7ff, 0x00f7ff)" in content  # Grille Néon Cyan #00f7ff
    assert "0xff00e6" in content  # Courbes Néon Magenta #ff00e6
    assert "exportPNG" in content
    assert "exportCSV" in content


def test_webgl_skill_evolution_performance():
    html_path = "static/webgl_skill_evolution.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "powerPreference: \"high-performance\"" in content
    assert "antialias: false" in content
    assert "renderDuration.toFixed(2)" in content
