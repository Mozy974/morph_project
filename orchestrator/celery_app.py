from celery import Celery
import os

broker_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
raw_backend_url = os.getenv('POSTGRES_URL', 'redis://redis:6379/1')

# --- LE FIX ANTI-CACHE DOCKER ---
# Si Docker envoie l'ancienne URL sans le "db+", Python la corrige automatiquement
if raw_backend_url.startswith("postgresql://"):
    result_backend = raw_backend_url.replace("postgresql://", "db+postgresql://")
else:
    result_backend = raw_backend_url

celery_app = Celery(
    'orchestrator',
    broker=broker_url,
    backend=result_backend,
    include=['orchestrator.tasks']
)

# --- Configuration pour le pipeline multi-agents ---
celery_app.conf.update(
    # Permet de voir l'état STARTED dans /status (utile pour suivre la chaîne)
    task_track_started=True,
    # Stocke des métadonnées étendues sur chaque résultat (parent, children...)
    result_extended=True,
    # --- Optimisations Production ---
    # Les tâches ne sont acquittées qu'après réussite.
    # Si un worker crash, la tâche est re-dispatchée à un autre worker.
    task_acks_late=True,
    # Empêche un worker rapide d'accaparer toutes les tâches en file d'attente.
    # Indispensable pour des tâches longues et asynchrones (LLM).
    worker_prefetch_multiplier=1,
    # --- Tâches Périodiques (Celery Beat) ---
    beat_schedule={
        'chroma-weekly-maintenance': {
            'task': 'orchestrator.tasks.task_chroma_weekly_maintenance',
            'schedule': 604800.0,  # 7 jours en secondes
            'kwargs': {'collection_name': 'superagent_knowledge'}
        },
    }
)

