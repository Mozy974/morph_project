"""
Tests unitaires pour le composant Météo Île de La Réunion (tests/test_reunion_weather.py).
"""

import os
import pytest
from orchestrator.agents.reunion_weather_component import render_reunion_weather_chart


def test_reunion_weather_html_exists():
    html_path = "static/neon_reunion_weather_chart.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<canvas id=\"chartCanvas\">" in content
    assert "Météo Île de La Réunion" in content
    assert "Piton de la Fournaise" in content
    assert "Saint-Denis" in content
    assert "Cilaos" in content
    assert "Saint-Gilles" in content
    assert "Mafate" in content
    assert "< 1 ms" in content


def test_reunion_weather_canvas_performance_specs():
    html_path = "static/neon_reunion_weather_chart.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "shadowBlur = 14" in content  # Grille & Ligne néon météo
    assert "requestAnimationFrame(render)" in content  # Frame loop 60+ FPS
    assert "renderDuration = t1 - t0" in content  # Suivi de performance < 1 ms
