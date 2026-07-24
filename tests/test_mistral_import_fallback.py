"""
Tests d'intégration du Fallback d'Import MistralAI (tests/test_mistral_import_fallback.py).
Simule un ImportError forcé pour valider la robustesse de l'initialisation RAG.
"""

import sys
import pytest
from unittest.mock import patch


def test_rag_pipeline_mistral_import_fallback_graceful():
    # Force mock mistralai as None / unimportable
    with patch.dict(sys.modules, {"mistralai": None}):
        import rag_pipeline
        assert hasattr(rag_pipeline, "HybridRAGPipeline")
        pipeline = rag_pipeline.HybridRAGPipeline()
        assert pipeline is not None


def test_mistral_client_fallback_resilience():
    from orchestrator.agents.mistral_client import call_mistral
    # Test call_mistral fallback handling when key is unconfigured or offline
    result = call_mistral("Agent Codeur", "Test prompt for resilience fallback")
    assert isinstance(result, str)
    assert len(result) > 0


