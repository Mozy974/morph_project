"""
Tests unitaires pour PeerImprovementNetwork (Level 8.0 Auto-Évolution Collective).
"""

import pytest
from orchestrator.agents.peer_improvement_network import PeerImprovementNetwork


def test_peer_improvement_network_init():
    net = PeerImprovementNetwork()
    assert net.nom == "P2P Peer Improvement Network"
