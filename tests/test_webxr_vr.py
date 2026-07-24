"""
Tests unitaires pour le composant WebGPU Compute Shader & WebXR 3D VR Engine (tests/test_webxr_vr.py).
"""

import os
import pytest
from orchestrator.agents.webxr_vr_component import render_webxr_vr_component


def test_webxr_vr_html_exists():
    html_path = "static/webgl_compute_vr_evolution.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "WebGPU Compute & WebXR VR Engine" in content
    assert "THREE.WebGLRenderer" in content
    assert "navigator.xr" in content
    assert "immersive-vr" in content
    assert "iOS Safari" in content
    assert "Android Chrome" in content


def test_webxr_vr_specs():
    html_path = "static/webgl_compute_vr_evolution.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Compute Shader GPU" in content
    assert "Motion-to-Photon" in content
    assert "requestAnimationFrame" in content
