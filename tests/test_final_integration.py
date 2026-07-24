"""
Tests de Validation de l'Intégration Finale (tests/test_final_integration.py).
Vérifie la présence et le bon fonctionnement de tous les composants de production WebGL / Go / Streamlit.
"""

import os
import pytest


def test_backend_go_source_exists():
    path = "orchestrator/skills_backend.go"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "package main" in code
    assert "/api/skills" in code
    assert "json.NewEncoder" in code


def test_webgl_frontend_minified_or_standard_exists():
    std_path = "static/webgl_skill_evolution.html"
    assert os.path.exists(std_path)
    with open(std_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "WebGL 3D Skill Evolution Radar" in content
    assert "THREE.WebGLRenderer" in content


def test_streamlit_component_wrapper_exists():
    path = "orchestrator/agents/webgl_skill_component.py"
    assert os.path.exists(path)
    from orchestrator.agents.webgl_skill_component import render_webgl_skill_evolution
    assert callable(render_webgl_skill_evolution)


def test_chroma_maintenance_integrated():
    path = "orchestrator/memory/chroma_maintenance.py"
    assert os.path.exists(path)
    from orchestrator.memory.chroma_maintenance import ChromaMaintenanceManager
    assert hasattr(ChromaMaintenanceManager, "audit_health")


def test_circuit_breaker_integrated():
    path = "orchestrator/circuit_breaker.py"
    assert os.path.exists(path)
    from orchestrator.circuit_breaker import mistral_circuit_breaker, tavily_circuit_breaker
    assert mistral_circuit_breaker.failure_threshold == 3
    assert tavily_circuit_breaker.failure_threshold == 3
