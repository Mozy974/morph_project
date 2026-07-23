"""
Module de métriques et d'observabilité Prometheus pour le SuperAgent (orchestrator/metrics.py).
Expose les métriques temps réel et l'endpoint GET /metrics pour le scraping Prometheus.

Support multi-processus Gunicorn et immunité au rechargement dynamique (Streamlit/FastAPI).
"""
import os
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess, REGISTRY
)
from fastapi import Response


# --- Répertoire multi-process Prometheus ---
PROMETHEUS_MULTIPROC_DIR = os.getenv(
    "PROMETHEUS_MULTIPROC_DIR",
    "/tmp/prometheus_multiproc_dir"
)

os.makedirs(PROMETHEUS_MULTIPROC_DIR, exist_ok=True)
os.environ["prometheus_multiproc_dir"] = PROMETHEUS_MULTIPROC_DIR


def _get_or_create_metric(metric_cls, name, documentation, labelnames=(), **kwargs):
    """
    Crée une métrique Prometheus ou réutilise la métrique existante si elle est déjà enregistrée.
    Évite les erreurs `ValueError: Duplicated timeseries in CollectorRegistry` lors des rechargements Streamlit.
    """
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]

    try:
        return metric_cls(name, documentation, labelnames=labelnames, **kwargs)
    except ValueError:
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        for collector in list(REGISTRY._collectors):
            if hasattr(collector, '_name') and collector._name == name:
                try:
                    REGISTRY.unregister(collector)
                except Exception:
                    pass
        return metric_cls(name, documentation, labelnames=labelnames, **kwargs)


# ---------------------------------------------------------
# DÉCLARATION DES MÉTRIQUES PROMETHEUS (SÉCURISÉES STREAMLIT)
# ---------------------------------------------------------

# Compteur total des tâches déléguées par statut ("ACCEPTED", "SUCCESS", "FAILED")
TASKS_TOTAL = _get_or_create_metric(
    Counter,
    "superagent_tasks_total",
    "Nombre total de tâches déléguées au SuperAgent",
    labelnames=["status"]
)

# Compteur des résultats d'exécution Pytest dans la Sandbox ("PASSED", "FAILED")
PYTEST_RESULTS = _get_or_create_metric(
    Counter,
    "superagent_pytest_results",
    "Résultats d'exécution Pytest dans la Sandbox d'isolation",
    labelnames=["result"]
)

# Gauge des jobs en cours d'exécution
ACTIVE_JOBS = _get_or_create_metric(
    Gauge,
    "superagent_active_jobs",
    "Nombre de jobs SuperAgent actuellement en cours d'exécution"
)

# Histogramme des durées d'exécution par nœud du graphe
TASK_DURATION = _get_or_create_metric(
    Histogram,
    "superagent_task_duration_seconds",
    "Temps d'exécution en secondes par nœud du graphe d'état",
    labelnames=["node"]
)

# Compteur Prometheus pour le routage de l'IntentSentimentClassifier
CLASSIFIER_ROUTED_TOTAL = _get_or_create_metric(
    Counter,
    "superagent_classifier_routed_total",
    "Nombre total de requêtes routées par le classifieur d'intention",
    labelnames=["intent", "target_agent"]
)

# Gauge Prometheus pour le ratio de hits dans le cache d'intentions
CLASSIFIER_CACHE_HIT_RATIO = _get_or_create_metric(
    Gauge,
    "superagent_classifier_cache_hit_ratio",
    "Ratio de requêtes servies depuis le cache d'intentions"
)

# Compteur Prometheus de coût estimé des requêtes LLM en USD
CLASSIFIER_QUERY_COST_USD = _get_or_create_metric(
    Counter,
    "superagent_classifier_query_cost_usd",
    "Coût cumulé estimé des requêtes LLM en USD",
    labelnames=["model"]
)

# Compteur d'accès éphémères JIT suspects
SUSPICIOUS_ACCESS_COUNTER = _get_or_create_metric(
    Counter,
    "superagent_suspicious_access_attempts_total",
    "Nombre total de tentatives d'accès suspectes ou non autorisées",
    labelnames=["reason"]
)


def setup_metrics_route(app):
    """
    Enregistre l'endpoint GET /metrics dans l'application FastAPI pour Prometheus.
    Utilise un registre multi-processus pour agréger les métriques de tous les workers Gunicorn.
    """
    @app.get("/metrics", include_in_schema=False)
    async def get_prometheus_metrics():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
