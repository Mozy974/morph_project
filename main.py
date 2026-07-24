"""
API FastAPI pour l'architecture RAG Hybride (LlamaIndex / Mistral + DuckDuckGo)
Expose les endpoints HTTP pour l'interrogation RAG, la vérification de santé et les métriques Prometheus.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header, Depends, Response, status
from pydantic import BaseModel, Field
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from rag_pipeline import HybridRAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_api")

app = FastAPI(
    title="RAG Hybride API",
    description="API HTTP scalable pour le requêtage RAG Hybride (ChromaDB + DuckDuckGo/Tavily)",
    version="1.0.0"
)

# Initialisation du pipeline RAG au démarrage
rag_pipeline = HybridRAGPipeline()
try:
    rag_pipeline.init_vector_store()
except Exception as e:
    logger.warning(f"Initialisation vectorielle au démarrage incomplète : {e}")


# --- MODÈLES PYDANTIC ---
class QueryRequest(BaseModel):
    query: str = Field(..., description="La question posée par l'utilisateur", example="Qu'est-ce que FastAPI et comment s'intègre-t-il avec LlamaIndex ?")
    search_mode: str = Field("AUTO", description="Mode de recherche (AUTO, HYBRID, WEB, LOCAL)")
    max_web_results: int = Field(3, ge=1, le=10, description="Nombre de résultats Web à extraire")
    n_local_results: int = Field(3, ge=1, le=10, description="Nombre de fragments locaux à extraire")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Historique optionnel de la conversation")


class QueryResponse(BaseModel):
    query: str
    mode_used: str
    response: str
    context: str
    duration_seconds: float


class HealthResponse(BaseModel):
    status: str
    environment: str
    vector_store_ready: bool


# --- DÉPENDANCE DE SÉCURITÉ ---
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Vérifie la présence d'une clé API valide si RAG_API_KEY est configurée dans l'environnement."""
    expected_key = os.environ.get("RAG_API_KEY")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante dans les en-têtes (X-API-Key)."
        )


# --- ENDPOINTS ---
@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Endpoint de santé pour Kubernetes / Load Balancer."""
    return HealthResponse(
        status="ok",
        environment=os.environ.get("ENVIRONMENT", "development"),
        vector_store_ready=rag_pipeline.is_indexed
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Endpoint Prometheus exposant les métriques d'application."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)], tags=["RAG"])
async def query_rag(request: QueryRequest):
    """Endpoint principal de requêtage RAG.
    
    Exécute le requêtage Hybride (ChromaDB + DuckDuckGo) et génère une réponse augmentée.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La requête ne peut pas être vide.")

    try:
        # Exécution de la recherche
        rag_res = rag_pipeline.hybrid_query(
            query=request.query,
            search_mode=request.search_mode,
            max_web_results=request.max_web_results,
            n_local_results=request.n_local_results
        )

        # Génération de la réponse via le LLM
        final_answer = rag_pipeline.generate_response(
            query=request.query,
            context=rag_res["context"],
            history=request.history
        )

        return QueryResponse(
            query=request.query,
            mode_used=rag_res["mode_used"],
            response=final_answer,
            context=rag_res["context"],
            duration_seconds=rag_res.get("duration_seconds", 0.0)
        )
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur interne : {str(e)}")
