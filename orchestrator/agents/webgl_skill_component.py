"""
Composant WebGL 3D / GLSL Dark Neon Grid - Évolution des Compétences IA (< 0.5 ms Rerender).
Intégré au Dashboard Principal SuperAgent Morph.
"""

import os
import streamlit.components.v1 as components


def render_webgl_skill_evolution(height: int = 720):
    """
    Rend le composant WebGL 3D GLSL Néon d'évolution des compétences (< 0.5 ms par frame).
    """
    chart_path = os.path.join(
        os.path.dirname(__file__), "..", "static", "webgl_skill_evolution.html"
    )
    if not os.path.exists(chart_path):
        chart_path = "static/webgl_skill_evolution.html"

    with open(chart_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    components.html(html_code, height=height, scrolling=False)
