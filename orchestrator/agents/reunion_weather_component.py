"""
Composant de Visualisation Météo Île de La Réunion (< 1 ms Rerender).
Généré par l'Agent Codeur conformément à la requête multimodale (Texte + Voix + Vision).
"""

import os
import streamlit.components.v1 as components


def render_reunion_weather_chart(height: int = 680):
    """
    Rend le composant HTML5 Canvas de visualisation météo néon de La Réunion (< 1 ms par frame).
    """
    chart_path = os.path.join(
        os.path.dirname(__file__), "..", "static", "neon_reunion_weather_chart.html"
    )
    if not os.path.exists(chart_path):
        chart_path = "static/neon_reunion_weather_chart.html"

    with open(chart_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    components.html(html_code, height=height, scrolling=False)
