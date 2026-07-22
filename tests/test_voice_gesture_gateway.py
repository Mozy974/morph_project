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
