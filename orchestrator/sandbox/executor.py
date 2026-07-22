"""
Module d'exécution sécurisée et isolée (Sandbox) pour le code Python généré par le SuperAgent.
"""

import os
import sys
import time
import tempfile
import subprocess
from typing import Dict, Any


def execute_code_in_sandbox(code_content: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Exécute un script Python dans un sous-processus isolé avec timeout strict et capture de la sortie.

    Args:
        code_content: Le code Python à exécuter.
        timeout: Temps d'exécution maximal en secondes (défaut: 10s).

    Returns:
        Un dictionnaire contenant :
        {
            "success": True/False,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "execution_time": float,
            "error": str ou None
        }
    """
    start_time = time.time()
    
    # Nettoyage d'éventuelles balises markdown si le code contient ```python
    clean_code = code_content.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code[9:]
    elif clean_code.startswith("```"):
        clean_code = clean_code[3:]
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
    clean_code = clean_code.strip()

    # Création d'un fichier temporaire
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_filepath = temp_file.name
        temp_file.write(clean_code)

    try:
        # Exécution isolée du sous-processus
        process = subprocess.run(
            [sys.executable, temp_filepath],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
        )

        exec_time = round(time.time() - start_time, 3)
        success = (process.returncode == 0)

        return {
            "success": success,
            "exit_code": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "execution_time": exec_time,
            "error": None if success else process.stderr.strip()
        }

    except subprocess.TimeoutExpired:
        exec_time = round(time.time() - start_time, 3)
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"❌ TimeoutExpired : L'exécution a dépassé la limite de {timeout} secondes.",
            "execution_time": exec_time,
            "error": "TimeoutExpired"
        }
    except Exception as e:
        exec_time = round(time.time() - start_time, 3)
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "execution_time": exec_time,
            "error": str(e)
        }
    finally:
        # Nettoyage du fichier temporaire
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass
