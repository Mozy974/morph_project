#!/usr/bin/env python3
"""
ProgramBench — Enterprise Benchmark Suite pour SuperAgent Morph.
Mesure la performance, la précision TDD et le taux de succès (Pass@1)
du SuperAgent sur des tâches d'ingénierie logicielle réelles.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- LISTE DES DEFIS DE BENCHMARK (PROGRAM BENCH SUITE) ---
BENCHMARK_SUITE = [
    {
        "id": "PB-001",
        "title": "Cache LRU Async & TTL Thread-Safe",
        "domain": "Concurrence & Structure de Données",
        "task": (
            "Implémenter un cache LRU asynchrone `CacheLRU` en Python avec gestion du TTL "
            "(Time To Live) supportant les stratégies EAGER et LAZY. "
            "Le cache doit être thread-safe avec asyncio.Lock et lever CacheError si la clé est introuvable."
        ),
        "max_retries": 2
    },
    {
        "id": "PB-002",
        "title": "Rate Limiter Sliding Window",
        "domain": "API & Algorithmique",
        "task": (
            "Implémenter un limiteur de débit `RateLimiter` par fenêtre glissante (Sliding Window). "
            "La méthode `check_rate_limit(client_id: str)` doit lever `RateLimitExceeded` "
            "si le client dépasse X requêtes par intervalle de N secondes."
        ),
        "max_retries": 2
    },
    {
        "id": "PB-003",
        "title": "Client HTTP avec Exponential Backoff",
        "domain": "Résilience Réseau & Async",
        "task": (
            "Implémenter un client HTTP asynchrone `RetryHttpClient` avec mécanisme de retry "
            "et Exponential Backoff configurable (max_retries, base_delay, backoff_factor). "
            "Lever `MaxRetriesExceededError` en cas d'échecs répétés."
        ),
        "max_retries": 2
    },
    {
        "id": "PB-004",
        "title": "Bug Fix & Refactoring (SWE-Bench Style)",
        "domain": "Maintenance & Patching de Code",
        "task": (
            "Déboguer et réparer une fonction `calculate_discount(prices, discount_pct)` "
            "qui lève actuellement `ZeroDivisionError` et ne gère pas les listes vides. "
            "Appliquer le patch minimal pour que les tests unitaires repassent 100% au vert."
        ),
        "max_retries": 2
    }
]



def delegate_task(task_desc: str, max_retries: int = 2) -> str:
    """Envoie une tâche d'ingénierie au SuperAgent et retourne le job_id."""
    payload = json.dumps({
        "user_id": 999,
        "task": task_desc,
        "max_retries": max_retries
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{API_URL}/delegate_task",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("job_id", "")


def poll_job_status(job_id: str, poll_interval: int = 3, timeout_seconds: int = 300) -> Dict[str, Any]:
    """Attend la fin d'un job SuperAgent et extrait les métriques complètes."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(f"{API_URL}/status/{job_id}", method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                status = data.get("status", "PENDING")
                if status in ("SUCCESS", "FAILED"):
                    return data
        except Exception as e:
            print(f"  ⚠️ Erreur lors du polling du job {job_id} : {e}")
        time.sleep(poll_interval)

    return {"status": "TIMEOUT", "job_id": job_id}


def run_benchmark():
    print("=" * 70)
    print("  🚀 PROGRAM BENCH — SuperAgent Morph Evaluation Suite")
    print(f"  Target API: {API_URL} | Challenges: {len(BENCHMARK_SUITE)}")
    print("=" * 70 + "\n")

    results: List[Dict[str, Any]] = []
    total_start_time = time.time()

    for idx, test_case in enumerate(BENCHMARK_SUITE, start=1):
        print(f"[{idx}/{len(BENCHMARK_SUITE)}] 🧪 Running {test_case['id']} — {test_case['title']} ({test_case['domain']})")
        print(f"    Consigne: {test_case['task'][:80]}...")

        start_time = time.time()
        try:
            job_id = delegate_task(test_case["task"], max_retries=test_case["max_retries"])
            print(f"    ✅ Job délégué avec succès (ID: {job_id})")
            print("    ⏳ Attente de la résolution TDD par le SuperAgent...")

            status_data = poll_job_status(job_id)
            elapsed_time = round(time.time() - start_time, 2)

            status = status_data.get("status", "UNKNOWN")
            retries = status_data.get("retries", status_data.get("retry_count", 0))
            analyst_score = status_data.get("analyst_score", status_data.get("score_confiance", "N/A"))

            pass_at_1 = (status == "SUCCESS" and retries == 0)

            res_entry = {
                "id": test_case["id"],
                "title": test_case["title"],
                "domain": test_case["domain"],
                "status": status,
                "duration_s": elapsed_time,
                "retries": retries,
                "score": analyst_score,
                "pass_at_1": pass_at_1
            }
            results.append(res_entry)

            status_icon = "✅" if status == "SUCCESS" else "❌"
            print(f"    {status_icon} Résultat: {status} en {elapsed_time}s | Retries: {retries} | Score Analyste: {analyst_score}/100\n")

        except Exception as e:
            elapsed_time = round(time.time() - start_time, 2)
            print(f"    ❌ Échec du test : {e}\n")
            results.append({
                "id": test_case["id"],
                "title": test_case["title"],
                "domain": test_case["domain"],
                "status": "ERROR",
                "duration_s": elapsed_time,
                "retries": 0,
                "score": 0,
                "pass_at_1": False
            })

    total_duration = round(time.time() - total_start_time, 2)
    successes = sum(1 for r in results if r["status"] == "SUCCESS")
    pass_1_count = sum(1 for r in results if r["pass_at_1"])
    avg_duration = round(sum(r["duration_s"] for r in results) / len(results), 2) if results else 0

    # --- GENERATION DU RAPPORT SUMMARY ---
    summary_md = f"""# 🚀 SuperAgent Morph — ProgramBench Results

- **Date Execution** : {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Tâches Évaluées** : {len(results)}
- **Taux de Succès Global** : {successes}/{len(results)} ({round(successes / len(results) * 100, 1)}%)
- **Taux Pass@1 (1er Essai)** : {pass_1_count}/{len(results)} ({round(pass_1_count / len(results) * 100, 1)}%)
- **Durée Totale Benchmark** : {total_duration}s (Moyenne : {avg_duration}s / tâche)

---

### 📊 Tableau Récapitulatif des Performances

| Challenge ID | Titre du Défi | Domaine | Statut | Pass@1 | Durée (s) | Retries | Score Analyste |
|---|---|---|---|---|---|---|---|
"""
    for r in results:
        p1_str = "✅ Oui" if r["pass_at_1"] else "🔄 Itéré"
        status_str = "✅ SUCCESS" if r["status"] == "SUCCESS" else f"❌ {r['status']}"
        summary_md += f"| **{r['id']}** | {r['title']} | {r['domain']} | {status_str} | {p1_str} | {r['duration_s']}s | {r['retries']} | {r['score']}/100 |\n"

    summary_md += "\n---\n*Benchmark généré automatiquement par `scripts/program_bench.py`*\n"

    # Sauvegarde du rapport
    report_file = os.path.join(os.path.dirname(__file__), "..", "program_bench_results.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print("=" * 70)
    print(f"📊 BENCHMARK COMPLETE — {successes}/{len(results)} Succès | Pass@1: {round(pass_1_count / len(results) * 100, 1)}%")
    print(f"📄 Rapport détaillé enregistré dans: {os.path.abspath(report_file)}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
