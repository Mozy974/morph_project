"""
Tests unitaires pour le composant de visualisation des compétences SuperAgent (tests/test_skills_chart.py).
"""

import os
import pytest
from orchestrator.agents.skills_chart_component import render_neon_skills_chart


def test_skills_chart_html_exists():
    html_path = "static/neon_skills_chart.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<canvas id=\"chartCanvas\">" in content
    assert "SuperAgent Skills Competency Tracker" in content
    assert "Code & Sandbox TDD" in content
    assert "RAG & ChromaDB Memory" in content
    assert "Web Search & Discovery" in content
    assert "Sécurité & Invariants RGPD" in content
    assert "&lt; 1 ms" in content or "< 1ms" in content



def test_skills_chart_canvas_performance_specs():
    html_path = "static/neon_skills_chart.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "shadowBlur = 15" in content  # Grille & Ligne néon violette/cyan
    assert "requestAnimationFrame(render)" in content  # Frame loop 60+ FPS
    assert "renderDuration = t1 - t0" in content  # Suivi de performance < 1 ms
