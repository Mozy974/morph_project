"""
Bus d'événements Redis Pub/Sub pour le streaming en temps réel (Server-Sent Events).
Permet le streaming de logs et d'événements structurés entre les workers Celery et FastAPI.
"""

import os
import json
import time
import asyncio
import datetime
from typing import Dict, Any, AsyncGenerator

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_sync_client = None

try:
    import redis
    redis_sync_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_sync_client.ping()
    print("[EventBus] 🔌 Connexion Redis Pub/Sub active !")
except Exception as e:
    redis_sync_client = None
    print(f"[EventBus] ℹ️ Redis Pub/Sub synchrone non disponible : {e}")


def publish_event(job_id: str, event_type: str, message: str, payload: Dict[str, Any] = None) -> None:
    """
    Publie un événement structuré sur le canal Redis Pub/Sub `channel:{job_id}`.
    """
    if not job_id:
        return

    event_data = {
        "job_id": job_id,
        "event_type": event_type,  # "node_start", "node_success", "feedback_loop", "code_attempt", "pytest_failed", "pytest_success", "info"
        "message": message,
        "payload": payload or {},
        "timestamp": datetime.datetime.now().isoformat()
    }

    serialized = json.dumps(event_data, ensure_ascii=False)

    if redis_sync_client:
        try:
            channel_name = f"channel:{job_id}"
            redis_sync_client.publish(channel_name, serialized)
            print(f"[EventBus] 📢 Event publié sur '{channel_name}' [{event_type}]: {message[:80]}")
        except Exception as e:
            print(f"[EventBus] ⚠️ Erreur publication Redis Pub/Sub : {e}")
    else:
        print(f"[EventBus] 📢 Event local [{event_type}]: {message[:80]}")


async def subscribe_events_async(job_id: str) -> AsyncGenerator[str, None]:
    """
    Générateur asynchrone SSE qui s'abonne au canal Redis `channel:{job_id}`
    et yield les messages sous le format Server-Sent Events (`data: {json}\n\n`).
    """
    channel_name = f"channel:{job_id}"
    print(f"[EventBus] 🎧 Début abonnement SSE pour client sur '{channel_name}'")

    # Événement initial de connexion
    init_event = json.dumps({
        "job_id": job_id,
        "event_type": "connected",
        "message": "🔌 Connexion SSE établie. Écoute du SuperAgent en direct...",
        "timestamp": datetime.datetime.now().isoformat()
    }, ensure_ascii=False)
    yield f"data: {init_event}\n\n"

    try:
        import redis.asyncio as aioredis
        async_redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        pubsub = async_redis.pubsub()
        await pubsub.subscribe(channel_name)

        timeout_counter = 0
        while True:
            # Attend les messages non-bloquant avec un petit délai
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                data = message.get("data")
                if data:
                    yield f"data: {data}\n\n"
                    # Si c'est l'événement de fin
                    try:
                        parsed = json.loads(data)
                        if parsed.get("event_type") in ["job_success", "job_failed"]:
                            break
                    except Exception:
                        pass
            else:
                # Keep-alive heartbeat toutes les 10 secondes pour éviter la fermeture HTTP
                timeout_counter += 1
                if timeout_counter >= 10:
                    heartbeat = json.dumps({"event_type": "heartbeat", "timestamp": datetime.datetime.now().isoformat()})
                    yield f"data: {heartbeat}\n\n"
                    timeout_counter = 0

                await asyncio.sleep(0.5)

    except Exception as e:
        err_msg = json.dumps({
            "job_id": job_id,
            "event_type": "error",
            "message": f"⚠️ Erreur flux SSE / Redis Pub/Sub : {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }, ensure_ascii=False)
        yield f"data: {err_msg}\n\n"
