"""
Tests unitaires pour VoiceGestureGateway (Level 11.0 Conscience Étendue Ultime).
"""

import pytest
from orchestrator.agents.voice_gesture_gateway import VoiceGestureGateway


def test_voice_gesture_gateway():
    gateway = VoiceGestureGateway()
    res = gateway.process_multimodal_signal("VOICE", "Lancer la suite de tests")
    assert res["signal_type"] == "VOICE"
    assert "Lancer la suite de tests" in res["decoded_command"]


def test_voice_stream_decoding():
    gateway = VoiceGestureGateway()
    res = gateway.process_voice_stream("Scanner le cluster Kubernetes", sample_rate=16000)
    assert res["stream_status"] == "ACTIVE"
    assert res["transcription"] == "Scanner le cluster Kubernetes"
    assert res["confidence"] == 0.97


def test_ui_gesture_processing():
    gateway = VoiceGestureGateway()
    res = gateway.process_ui_gesture("SWIPE_LEFT", {"x": 120.5, "y": 450.0})
    assert res["action"] == "TRIGGER_UI_SWIPE_LEFT"
    assert res["processed"] is True
