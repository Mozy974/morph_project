"""
Script de benchmark automatisé pour évaluer la latence et la stabilité du RAG Hybride.
"""

import time
import statistics
from rag_pipeline import HybridRAGPipeline

TEST_QUERIES = [
    ("Qu'est-ce que l'architecture RAG ?", "LOCAL"),
    ("Quelles sont les fonctionnalités de FastAPI ?", "WEB"),
    ("Quelle est la météo à Paris ?", "WEB"),
    ("Explique-moi la différence entre LlamaIndex et LangChain", "HYBRID"),
    ("Quels sont les avantages de DuckDuckGo en RAG ?", "WEB")
]

def run_benchmark(num_iterations: int = 2):
    print("=" * 60)
    print("🚀 LANCEMENT DU BENCHMARK RAG HYBRIDE")
    print("=" * 60)

    pipeline = HybridRAGPipeline()
    pipeline.init_vector_store()

    durations = []
    mode_durations = {"WEB": [], "LOCAL": [], "HYBRID": []}

    total_runs = len(TEST_QUERIES) * num_iterations
    completed = 0

    start_total = time.time()

    for i in range(num_iterations):
        print(f"\n--- Passation {i + 1}/{num_iterations} ---")
        for query, mode in TEST_QUERIES:
            t0 = time.time()
            res = pipeline.hybrid_query(query, search_mode=mode, max_web_results=2, n_local_results=2)
            elapsed = time.time() - t0

            used_mode = res.get("mode_used", mode)
            durations.append(elapsed)
            mode_durations[used_mode].append(elapsed)

            completed += 1
            print(f"[{completed}/{total_runs}] Query: '{query[:30]}...' | Mode: {used_mode} | Temps: {elapsed:.3f}s")

    total_time = time.time() - start_total

    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DU BENCHMARK")
    print("=" * 60)
    print(f"Requêtes totales exécutées : {completed}")
    print(f"Temps total du benchmark  : {total_time:.2f}s")
    print(f"Débit moyen (RPS)          : {completed / total_time:.2f} req/s")
    print(f"Latence Moyenne           : {statistics.mean(durations):.3f}s")
    print(f"Latence Médiane (p50)     : {statistics.median(durations):.3f}s")
    print(f"Latence Min / Max          : {min(durations):.3f}s / {max(durations):.3f}s")

    print("\n--- Détail par Mode de Recherche ---")
    for m, d_list in mode_durations.items():
        if d_list:
            avg_m = statistics.mean(d_list)
            print(f"Mode {m:6s} | Executions: {len(d_list)} | Latence moy: {avg_m:.3f}s")

    print("=" * 60)

if __name__ == "__main__":
    run_benchmark(num_iterations=2)
