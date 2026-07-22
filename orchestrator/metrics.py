"""
Module de métriques et d'observabilité Prometheus pour le SuperAgent (orchestrator/metrics.py).
Expose les métriques temps réel et l'endpoint GET /metrics pour le scraping Prometheus.

Support multi-processus Gunicorn : utilise PROMETHEUS_MULTIPROC_DIR pour que tous les workers
Gunicorn puissent exposer leurs métriques agrégées via un registre partagé.
"""
import os
import shutil
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess
)
from fastapi import Response


# --- Répertoire multi-process Prometheus ---
# Chaque worker Gunicorn écrit ses fichiers .db dans ce répertoire.
# Le registre multi-process les agrège à la volée lors du scrape /metrics.
PROMETHEUS_MULTIPROC_DIR = os.getenv(
    "PROMETHEUS_MULTIPROC_DIR",
    "/tmp/prometheus_multiproc_dir"
)

# Nettoyage effectué au démarrage du conteneur dans docker-compose.yml
os.makedirs(PROMETHEUS_MULTIPROC_DIR, exist_ok=True)

os.environ["prometheus_multiproc_dir"] = PROMETHEUS_MULTIPROC_DIR


# ---------------------------------------------------------
# DÉCLARATION DES MÉTRIQUES PROMETHEUS
# ---------------------------------------------------------

# Compteur total des tâches déléguées par statut ("ACCEPTED", "SUCCESS", "FAILED")
TASKS_TOTAL = Counter(
    "superagent_tasks_total",
    "Nombre total de tâches déléguées au SuperAgent",
    ["status"]
)

# Compteur des résultats d'exécution Pytest dans la Sandbox ("PASSED", "FAILED")
PYTEST_RESULTS = Counter(
    "superagent_pytest_results",
    "Résultats d'exécution Pytest dans la Sandbox d'isolation",
    ["result"]
)

# Gauge des jobs en cours d'exécution
ACTIVE_JOBS = Gauge(
    "superagent_active_jobs",
    "Nombre de jobs SuperAgent actuellement en cours d'exécution"
)

# Histogramme des durées d'exécution par nœud du graphe (Éclaireur, Analyste, QA_Tests, Codeur, Rédacteur, Distillateur)
TASK_DURATION = Histogram(
    "superagent_task_duration_seconds",
    "Temps d'exécution en secondes par nœud du graphe d'état",
    ["node"]
)

# Compteur Prometheus pour le routage de l'IntentSentimentClassifier (Mission Control)
CLASSIFIER_ROUTED_TOTAL = Counter(
    "superagent_classifier_routed_total",
    "Nombre total de requêtes routées par le classifieur d'intention",
    ["intent", "target_agent"]
)

# Gauge Prometheus pour le ratio de hits dans le cache d'intentions
CLASSIFIER_CACHE_HIT_RATIO = Gauge(
    "superagent_classifier_cache_hit_ratio",
    "Ratio de requêtes servies depuis le cache d'intentions"
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
