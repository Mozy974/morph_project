"""
Tests unitaires pour MultimodalGateway (Level 10.0 Conscience Ultime).
"""

import pytest
from orchestrator.agents.multimodal_gateway import MultimodalGateway


def test_multimodal_gateway_init():
    gateway = MultimodalGateway()
    assert gateway.nom == "Multimodal Gateway"
