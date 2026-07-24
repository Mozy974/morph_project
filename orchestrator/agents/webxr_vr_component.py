"""
Composant WebGPU Compute Shader & WebXR 3D VR Engine (< 20 ms Motion-to-Photon).
Généré conformément aux directives Meta-Consciousness.
"""

import os
import streamlit.components.v1 as components


def render_webxr_vr_component(height: int = 750):
    """
    Rend le composant WebGPU Compute Shader & WebXR Mode VR Immersif.
    """
    chart_path = os.path.join(
        os.path.dirname(__file__), "..", "static", "webgl_compute_vr_evolution.html"
    )
    if not os.path.exists(chart_path):
        chart_path = "static/webgl_compute_vr_evolution.html"

    with open(chart_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    components.html(html_code, height=height, scrolling=False)
