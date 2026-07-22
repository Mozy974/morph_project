"""
Module d'exécution d'espaces de travail multi-fichiers et suites de tests Pytest (`workspace_runner.py`).
"""

import os
import sys
import time
import subprocess
import shutil
from typing import Dict, Any


def execute_workspace_tests(files: Dict[str, str], timeout: int = 15) -> Dict[str, Any]:
    """
    Crée un projet multi-fichiers temporaire, installe les dépendances si nécessaires,
    et exécute la suite de tests avec `pytest -v --tb=short`.

    Args:
        files: Dictionnaire {"nom_fichier": "contenu_du_fichier"}.
        timeout: Temps maximal d'exécution (défaut: 15s).

    Returns:
        Dictionnaire avec `exit_code`, `logs`, `time`.
    """
    start_time = time.time()
    workspace_dir = tempfile.mkdtemp(prefix="superagent_workspace_")

    try:
        # 1. Matérialisation des fichiers sur le disque
        for filename, content in files.items():
            filepath = os.path.join(workspace_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            clean_content = content.strip()
            if clean_content.startswith("```python"):
                clean_content = clean_content[9:]
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            clean_content = clean_content.strip()

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(clean_content)

        # 2. Détection du langage et du runner de test approprié
        has_go = any(f.endswith(".go") for f in files)
        has_js_ts = any(f.endswith(".js") or f.endswith(".ts") or f == "package.json" for f in files)

        env = {**os.environ, "PYTHONPATH": workspace_dir, "PYTHONDONTWRITEBYTECODE": "1"}

        if has_go and shutil.which("go"):
            cmd = ["go", "test", "-v", "./..."]
        elif has_js_ts and shutil.which("node"):
            cmd = ["node", "--test"]
        else:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", workspace_dir]

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workspace_dir,
            env=env
        )

        exec_time = round(time.time() - start_time, 2)
        logs = process.stdout + ("\n" + process.stderr if process.stderr else "")

        return {
            "exit_code": process.returncode,
            "logs": logs.strip(),
            "time": exec_time
        }

    except subprocess.TimeoutExpired:
        exec_time = round(time.time() - start_time, 2)
        return {
            "exit_code": 124,
            "logs": f"❌ TimeoutError : La suite de tests pytest a dépassé la limite de {timeout}s.",
            "time": exec_time
        }
    except Exception as e:
        exec_time = round(time.time() - start_time, 2)
        return {
            "exit_code": 1,
            "logs": f"❌ Exception Sandbox : {str(e)}",
            "time": exec_time
        }
    finally:
        # Nettoyage
        try:
            import shutil
            shutil.rmtree(workspace_dir, ignore_errors=True)
        except Exception:
            pass
