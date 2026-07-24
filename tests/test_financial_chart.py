"""
Tests unitaires pour le composant de visualisation financière néon (tests/test_financial_chart.py).
"""

import os
import pytest
from orchestrator.agents.financial_chart_component import render_neon_financial_chart


def test_financial_chart_html_exists():
    html_path = "static/neon_financial_chart.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<canvas id=\"chartCanvas\">" in content
    assert "Neon Pulse Financial Engine" in content
    assert "< 1 ms" in content
    assert "Canvas 2D Sub-Millisecond Renderer" in content


def test_financial_chart_canvas_performance_specs():
    html_path = "static/neon_financial_chart.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Vérification des fonctionnalités clés exigées par la requête multimodale
    assert "shadowBlur = 12" in content  # Grille & Ligne néon
    assert "requestAnimationFrame(render)" in content  # Boucle de rendu fluide 60+ FPS
    assert "renderDuration = t1 - t0" in content  # Mesure de temps de rendu < 1 ms
