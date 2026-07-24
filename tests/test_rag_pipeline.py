import os
import pytest
from rag_pipeline import HybridRAGPipeline, load_documents

def test_load_documents_non_existent(tmp_path):
    dossier = tmp_path / "dossier_inexistant"
    docs, sources = load_documents(str(dossier))
    assert docs == []
    assert sources == []

def test_load_documents_with_files(tmp_path):
    dossier = tmp_path / "docs"
    dossier.mkdir()
    f1 = dossier / "test1.txt"
    f1.write_text("Ceci est un premier paragraphe de test avec plus de 50 caracteres pour la validation.\n\nCeci est un second paragraphe de test valide pour la recherche RAG.", encoding="utf-8")
    
    docs, sources = load_documents(str(dossier))
    assert len(docs) == 2
    assert len(sources) == 2
    assert "test1.txt" in sources[0]

def test_search_duckduckgo():
    pipeline = HybridRAGPipeline()
    results = pipeline.search_duckduckgo("python fast api", max_results=2)
    assert isinstance(results, list)
    if results:
        assert "title" in results[0]
        assert "snippet" in results[0]
        assert "url" in results[0]

def test_hybrid_query_web_mode():
    pipeline = HybridRAGPipeline()
    res = pipeline.hybrid_query("test query", search_mode="WEB", max_web_results=2)
    assert "mode_used" in res
    assert res["mode_used"] == "WEB"
    assert "context" in res
    assert isinstance(res["local_results"], list)
    assert isinstance(res["web_results"], list)
