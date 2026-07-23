"""
Tests unitaires pour MultimodalGateway (Level 10.0 Conscience Ultime).
"""

import pytest
from orchestrator.agents.multimodal_gateway import MultimodalGateway


def test_multimodal_gateway_init():
    gateway = MultimodalGateway()
    assert gateway.nom == "Multimodal Gateway"


def test_multimodal_gateway_ui_mockup():
    gateway = MultimodalGateway()
    res = gateway.process_ui_mockup_spec("Maquette Dashboard Dark Mode")
    assert "layout_components" in res
    assert "design_system_directives" in res
    assert "tdd_specs" in res


def test_multimodal_gateway_image_input():
    gateway = MultimodalGateway()
    res = gateway.process_image_input(b"fake_image_bytes", prompt="Analyse UI")
    assert res["image_type"] == "UI_MOCKUP"
    assert "extracted_elements" in res
    assert res["confidence_score"] == 0.98


def test_multimodal_gateway_audio_signal():
    gateway = MultimodalGateway()
    res = gateway.process_audio_signal("Afficher le dashboard PIB", file_format="wav")
    assert res["file_format"] == "wav"
    assert "transcription" in res
    assert res["detected_intent"] == "INTENT_CODE"


def test_multimodal_gateway_unified_payload():
    gateway = MultimodalGateway()
    unified = gateway.unify_multimodal_payload(
        text_prompt="Optimiser le cache",
        image_analysis={"description": "Graphique latence"},
        audio_analysis={"transcription": "Exécuter les tests", "recommended_target_agent": "Agent Codeur"}
    )
    assert unified["has_image"] is True
    assert unified["has_audio"] is True
    assert "Optimiser le cache" in unified["unified_prompt"]
