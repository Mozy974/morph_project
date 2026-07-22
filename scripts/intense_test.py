#!/usr/bin/env python3
"""
Test Intense (Stress Test Parallel) — Enterprise SuperAgent Morph
Lance 5 tâches complexes d'ingénierie logicielle simultanément
pour évaluer la résilience sous charge, la stabilité Redis/PostgreSQL
et la tenue en mémoire (8 Go RAM CPU).
"""

import sys
import os
import time
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

API_URL = os.getenv("API_URL", "http://localhost:8000")

INTENSE_TASKS = [
    {
        "name": "Task-A: Cache LRU Concurrent",
        "task": "Implémenter un cache LRU avec expiration TTL et sécurité multithread en Python.",
    },
    {
        "name": "Task-B: Rate Limiter Sliding Log",
        "task": "Implémenter un algorithme de Rate Limiting Sliding Window Log avec asyncio.",
    },
    {
        "name": "Task-C: Retry Client HTTP",
        "task": "Implémenter un client HTTP asynchrone avec Exponential Backoff et circuit breaker.",
    },
    {
        "name": "Task-D: Parseur Log High-Throughput",
        "task": "Implémenter un parseur de fichier log asynchrone haute performance extrayant les métriques p95/p99.",
    },
    {
        "name": "Task-E: Pool de Connexions Thread-Safe",
        "task": "Implémenter un gestionnaire de pool de connexions thread-safe réentrant avec timeout d'acquisition.",
    }
]


def delegate_single_task(item: Dict[str, str]) -> Dict[str, Any]:
    name = item["name"]
    task_desc = item["task"]
    start_t = time.time()

    print(f"🚀 [LANCEMENT PARALLÈLE] {name}...")

    payload = json.dumps({
        "user_id": 888,
        "task": task_desc,
        "max_retries": 1
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{API_URL}/delegate_task",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            job_id = data.get("job_id", "")

        if not job_id:
            return {"name": name, "status": "FAILED_DELEGATION", "time": round(time.time() - start_t, 2)}

        # Polling
        while time.time() - start_t < 300:
            time.sleep(4)
            try:
                s_req = urllib.request.Request(f"{API_URL}/status/{job_id}", method="GET")
                with urllib.request.urlopen(s_req, timeout=10) as s_resp:
                    s_data = json.loads(s_resp.read().decode("utf-8"))
                    status = s_data.get("status", "PENDING")
                    if status in ("SUCCESS", "FAILED"):
                        elapsed = round(time.time() - start_t, 2)
                        print(f"  ✅ [TERMINÉ] {name} -> {status} en {elapsed}s")
                        return {"name": name, "job_id": job_id, "status": status, "time": elapsed}
            except Exception:
                pass

        return {"name": name, "job_id": job_id, "status": "TIMEOUT", "time": round(time.time() - start_t, 2)}

    except Exception as e:
        return {"name": name, "status": f"ERROR: {e}", "time": round(time.time() - start_t, 2)}


def run_intense_stress_test():
    print("=" * 70)
    print("  🔥 TEST INTENSE DE CHARGE & RÉSILIENCE PARALLÈLE")
    print(f"  Volume : {len(INTENSE_TASKS)} jobs simultanés sur Celery/Redis")
    print("=" * 70 + "\n")

    overall_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=len(INTENSE_TASKS)) as executor:
        futures = [executor.submit(delegate_single_task, task_item) for task_item in INTENSE_TASKS]
        for future in as_completed(futures):
            results.append(future.result())

    total_time = round(time.time() - overall_start, 2)
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")

    print("\n" + "=" * 70)
    print(f"  📊 RÉSULTAT DU TEST INTENSE : {success_count}/{len(INTENSE_TASKS)} Succès")
    print(f"  ⏱️  Durée Totale sous Charge : {total_time}s")
    print("=" * 70)
    for r in results:
        icon = "✅" if r["status"] == "SUCCESS" else "❌"
        print(f"  {icon} {r['name']} | Status: {r['status']} | Temps: {r['time']}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_intense_stress_test()
