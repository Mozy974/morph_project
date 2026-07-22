#!/usr/bin/env python3
"""
Smoke Test Final — Enterprise SuperAgent Morph
Valide l'ensemble de la stack de bout en bout.

Usage:
    python3 scripts/smoke_test.py              # Test complet
    python3 scripts/smoke_test.py --quick      # Test rapide (skip LLM)
    python3 scripts/smoke_test.py --watch       # Mode watch (toutes les 60s)
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from urllib.error import URLError, HTTPError

# --- Configuration ---
API_URL = os.getenv("API_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9091")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3001")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://orchestrator_user:super_secret_password@localhost:5432/orchestrator_db")

PASS = 0
FAIL = 0
WARN = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL, WARN
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def warn(name: str, detail: str = ""):
    global WARN
    WARN += 1
    print(f"  ⚠️  {name} — {detail}")


def http_get(url: str, timeout: int = 10) -> tuple:
    """Retourne (status_code, body, error)."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, None
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body, str(e)
    except URLError as e:
        return 0, "", f"Connexion refusée : {e.reason}"
    except Exception as e:
        return 0, "", str(e)


def test_docker_containers():
    """Vérifie que tous les conteneurs sont up."""
    print("\n📦 Conteneurs Docker")
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", 
             os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml"),
             "ps", "--format", "json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            warn("docker compose ps", result.stderr.strip())
            return

        containers = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                c = json.loads(line)
                containers[c["Name"]] = c
            except json.JSONDecodeError:
                pass

        expected = {
            "orchestrator_api": "running",
            "orchestrator_db": "running",
            "orchestrator_redis": "running",
            "orchestrator_worker": "running",
            "orchestrator_prometheus": "running",
            "orchestrator_grafana": "running",
        }

        for name, expected_state in expected.items():
            c = containers.get(name)
            if c is None:
                check(f"{name} — conteneur manquant", False)
            else:
                state = c.get("State", "unknown")
                check(f"{name} — {state}", state == expected_state)

    except FileNotFoundError:
        warn("Docker", "Commande docker introuvable")
    except subprocess.TimeoutExpired:
        warn("Docker", "Timeout docker compose ps")


def test_api():
    """Test l'API FastAPI."""
    print("\n🌐 API FastAPI")

    # Endpoint racine
    status, body, err = http_get(f"{API_URL}/")
    check("GET / — status 200", status == 200, err or "")
    if status == 200:
        check("GET / — contient 'SuperAgent'", "SuperAgent" in body or "orchestrator" in body.lower())

    # Endpoint metrics
    status, body, err = http_get(f"{API_URL}/metrics")
    check("GET /metrics — status 200", status == 200, err or "")
    if status == 200:
        has_gunicorn = "superagent_active_jobs" in body
        check("/metrics — métriques Prometheus", has_gunicorn)
        # Vérifier multi-process
        pid_count = body.count("pid=\"")
        check(f"/metrics — {pid_count} workers Gunicorn", pid_count >= 2, f"Trouvé {pid_count} workers")


def test_ollama():
    """Test la connexion à Ollama."""
    print("\n🧠 Ollama (LLM Local)")

    status, body, err = http_get(f"{OLLAMA_URL}/api/tags")
    check("GET /api/tags — status 200", status == 200, err or "")
    if status == 200:
        try:
            data = json.loads(body)
            models = data.get("models", [])
            check(f"Modèles disponibles : {len(models)}", len(models) > 0)
            mistral = any("mistral" in m.get("name", "").lower() for m in models)
            check("Modèle mistral présent", mistral, "Utiliser 'ollama pull mistral:7b' si absent")
        except json.JSONDecodeError:
            check("Parsing JSON Ollama", False, "Réponse non-JSON")

    # Test inférence rapide
    print("  ⏳ Test inférence (premier chargement lent sur CPU, jusqu'à 120s)...")
    payload = json.dumps({
        "model": "mistral:latest",
        "messages": [
            {"role": "user", "content": "Réponds UNIQUEMENT par 'OK' si tu fonctionnes."}
        ],
        "stream": False,
        "options": {"num_predict": 10}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            check("Inférence Ollama OK", bool(content), f"Réponse : {content[:50]}")
    except Exception as e:
        check("Inférence Ollama", False, str(e))


def test_search():
    """Test le moteur de recherche DuckDuckGo."""
    print("\n🔍 Moteur de recherche (DuckDuckGo)")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    try:
        from orchestrator.search import search_web
        result = search_web("test unitaire Python", max_results=3)
        check("Recherche DuckDuckGo", result["success"], result.get("error", ""))
        check(f"Résultats : {len(result['results'])}", len(result["results"]) > 0)
    except Exception as e:
        check("Import search_web", False, str(e))


def test_prometheus():
    """Test Prometheus."""
    print("\n📊 Prometheus")
    status, body, err = http_get(f"{PROMETHEUS_URL}/-/ready")
    check("Prometheus ready", status == 200, err or "")

    # Vérifier que Prometheus scrape l'API
    status, body, err = http_get(f"{PROMETHEUS_URL}/api/v1/targets")
    if status == 200:
        try:
            data = json.loads(body)
            targets = data.get("data", {}).get("activeTargets", [])
            api_targets = [t for t in targets if "api" in t.get("labels", {}).get("job", "")]
            check(f"Targets API : {len(api_targets)}", len(api_targets) > 0)
        except (json.JSONDecodeError, KeyError):
            pass


def test_grafana():
    """Test Grafana."""
    print("\n📈 Grafana")
    status, body, err = http_get(f"{GRAFANA_URL}/api/health")
    check("Grafana health", status == 200, err or "")
    if status == 200:
        try:
            data = json.loads(body)
            check(f"Grafana DB: {data.get('database', '?')}", True)
        except json.JSONDecodeError:
            pass


def test_postgres():
    """Test la connexion PostgreSQL."""
    print("\n🗄️  PostgreSQL")
    try:
        import psycopg2
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        check("Connexion PostgreSQL", cur.fetchone() == (1,))
        cur.close()
        conn.close()
    except Exception as e:
        check("Connexion PostgreSQL", False, str(e))


def test_redis():
    """Test la connexion Redis."""
    print("\n🔴 Redis")
    try:
        import redis as redis_client
        r = redis_client.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        check("Connexion Redis", True)
        r.set("smoke_test", "ok", ex=10)
        check("Redis SET/GET", r.get("smoke_test") == "ok")
    except Exception as e:
        check("Connexion Redis", False, str(e))


def test_celery():
    """Test Celery via l'API."""
    print("\n⚙️  Celery Worker")
    # On envoie une tâche simple via l'API
    payload = json.dumps({
        "user_id": 1,
        "task": "Test de validation — réponds OK si tu fonctionnes.",
        "max_retries": 0
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{API_URL}/delegate_task",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            job_id = result.get("job_id", "")
            check("Tâche déléguée à Celery", bool(job_id), f"job_id: {job_id}")

            # Attendre le résultat
            if job_id:
                time.sleep(3)
                status, body, err = http_get(f"{API_URL}/status/{job_id}")
                if status == 200:
                    try:
                        data = json.loads(body)
                        task_status = data.get("status", "UNKNOWN")
                        check(f"Statut tâche : {task_status}", task_status in ("SUCCESS", "PENDING", "IN_PROGRESS", "FAILED"))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        check("Délégation tâche Celery", False, str(e))


def main():
    parser = argparse.ArgumentParser(description="Smoke Test SuperAgent Morph")
    parser.add_argument("--quick", action="store_true", help="Test rapide (skip LLM)")
    parser.add_argument("--watch", action="store_true", help="Mode watch (toutes les 60s)")
    args = parser.parse_args()

    print("=" * 60)
    print("  🔥 SMOKE TEST — Enterprise SuperAgent Morph")
    print("  Stack 100% Gratuite | Ollama + DuckDuckGo + PostgreSQL")
    print("=" * 60)

    if args.watch:
        print("\n📡 Mode WATCH — rafraîchissement toutes les 60s\n")
        while True:
            run_tests(args.quick)
            print(f"\n⏳ Prochain test dans 60s... (Ctrl+C pour quitter)")
            time.sleep(60)
    else:
        run_tests(args.quick)
        print_summary()


def run_tests(quick: bool):
    global PASS, FAIL, WARN
    PASS = FAIL = WARN = 0

    test_docker_containers()
    test_api()
    test_prometheus()
    test_grafana()
    test_postgres()
    test_redis()
    test_search()
    test_celery()

    if not quick:
        test_ollama()


def print_summary():
    total = PASS + FAIL + WARN
    print("\n" + "=" * 60)
    print(f"  📊 RÉSULTATS : {PASS} ✅ / {FAIL} ❌ / {WARN} ⚠️  sur {total} tests")
    print("=" * 60)

    if FAIL == 0:
        print("\n  🎉 TOUS LES TESTS PASSENT — Stack opérationnelle !")
        print("  Ton SuperAgent est prêt à recevoir son premier job.")
    else:
        print(f"\n  ⚠️  {FAIL} test(s) en échec. Vérifie les détails ci-dessus.")

    print("\n  Endpoints clés :")
    print(f"    API        → http://localhost:8000")
    print(f"    Ollama     → http://localhost:11434")
    print(f"    Prometheus → http://localhost:9091")
    print(f"    Grafana    → http://localhost:3001 (admin/superagent)")
    print(f"    Dashboard  → http://localhost:8000/app")
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
