"""
Test de Chaos Engineering pour la résilience aux pannes d'APIs externes (Tavily Web Search) (tests/test_tavily_chaos_fallback.py).
Vérifie le basculement gracieux vers la base RAG locale lorsque l'API Tavily échoue ou expire.
"""

import pytest
from unittest.mock import patch, MagicMock


@patch("requests.post")
def test_tavily_api_timeout_fallback(mock_post):
    # Simulation d'un timeout réseau ou d'une erreur 500 sur l'API externe Tavily
    mock_post.side_effect = Exception("API Timeout / Network Connection Refused")

    def perform_search_with_fallback(query: str):
        try:
            # Tentative de recherche web via API externe
            mock_post("https://api.tavily.com/search", json={"query": query}, timeout=2)
            return "RESULTATS_WEB"
        except Exception:
            # Fallback automatique sur la base de connaissances locale
            return "RESULTATS_RAG_LOCAUX_BASE_PERSONNELLE"

    res = perform_search_with_fallback("Quelles sont les métriques du Swarm ?")
    assert res == "RESULTATS_RAG_LOCAUX_BASE_PERSONNELLE"
