"""
Agent Codeur : développe la solution technique (`main.py`) pour satisfaire la suite de tests opposable (`test_main.py`) de l'Analyste (True TDD).
"""

import json
from typing import Dict, Any, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_CODEUR
from orchestrator.sandbox.executor import execute_code_in_sandbox
from orchestrator.sandbox.workspace_runner import execute_workspace_tests
from orchestrator.interfaces import QATestSuite, DevImplementation, WorkspacePayload
from orchestrator.memory.event_bus import publish_event


class AgentCodeur:
    def __init__(self):
        self.nom = "Codeur Dev"

    def resoudre_tests_tdd(
        self,
        instruction: str,
        qa_test_suite: QATestSuite,
        max_attempts: int = 3,
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        True TDD : Reçoit le contrat de tests opposables et immuables (`test_main.py`)
        conçu par l'Analyste QA, et écrit uniquement l'implémentation `main.py` pour faire
        passer `pytest -v --tb=short` à 100% GREEN.
        """
        print(f"[{self.nom}] 💻 Résolution True TDD contre la suite de tests QA immuable...")
        publish_event(job_id, "codeur_start", f"💻 Le Codeur Dev s'attaque à la résolution TDD (immuable)...")

        system_prompt = """Tu es un développeur Python senior.
Un ingénieur Assurance Qualité (QA) a rédigé une suite de tests unitaire stricte (test_main.py).
Ta mission est d'écrire l'implémentation complète dans main.py pour faire passer la commande pytest au vert.

RÈGLES STRICTES :
1. Tu dois générer UNIQUEMENT la solution technique dans main.py.
2. Tu n'as PAS LE DROIT de modifier ou supprimer les tests de test_main.py.
3. Tu dois répondre UNIQUEMENT avec un dictionnaire JSON valide :
{
    "explication_code": "Explication de la solution technique adoptée",
    "main_code": "Code Python complet du fichier main.py"
}
4. Assure-toi que toutes les fonctions et classes importées par test_main.py sont correctement définies et gèrent tous les cas d'erreurs/exceptions attendus."""

        attempt = 1
        last_error_log = ""

        while attempt <= max_attempts:
            msg_attempt = f"⚙️ Génération du code main.py (Tentative TDD #{attempt}/{max_attempts})..."
            print(f"[{self.nom}] {msg_attempt}")
            publish_event(job_id, "code_attempt", msg_attempt, {"attempt": attempt})

            user_prompt = f"SPÉCIFICATION ET TÂCHE :\n{instruction}\n\n"
            user_prompt += f"CONTRAT DE TESTS IMMUABLE (test_main.py) :\n```python\n{qa_test_suite.test_main_code}\n```\n\n"

            if attempt > 1:
                user_prompt += f"⚠️ L'EXÉCUTION PRÉCÉDENTE DE PYTEST A ÉCHOUÉ AVEC LE RAPPORT SUIVANT :\n{last_error_log}\n\nCorrige main.py pour faire passer tous les tests."

            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_CODEUR,
                json_mode=True,
            )

            try:
                data = json.loads(raw_response)
                dev_impl = DevImplementation(
                    explication_code=data.get("explication_code", "Implémentation main.py"),
                    main_code=data.get("main_code", "# main.py\n")
                )
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur parsing JSON DevImplementation: {e}")
                dev_impl = DevImplementation(
                    explication_code="Code extrait",
                    main_code=raw_response
                )

            # Assemblage du Workspace (main.py + test_main.py + requirements.txt)
            payload = WorkspacePayload.assemble(qa_test_suite, dev_impl)

            # Exécution dans la Sandbox Pytest avec --tb=short
            print(f"[{self.nom}] 🧪 Exécution de pytest -v --tb=short dans la Sandbox Workspace...")
            publish_event(job_id, "pytest_running", "🧪 Lancement de pytest -v --tb=short dans la Sandbox...")
            
            sandbox_res = execute_workspace_tests(payload.files, timeout=15)

            if sandbox_res["exit_code"] == 0:
                success_msg = f"🎉 100% DES TESTS PASSED en {sandbox_res['time']}s ! (Exit Code 0)"
                print(f"[{self.nom}] {success_msg}")
                publish_event(job_id, "pytest_success", success_msg, {"logs": sandbox_res["logs"], "time": sandbox_res["time"]})

                return {
                    "success": True,
                    "attempts_count": attempt,
                    "dev_implementation": dev_impl.dict(),
                    "sandbox_results": sandbox_res,
                    "workspace_payload": payload.dict()
                }

            last_error_log = sandbox_res["logs"]
            fail_msg = f"❌ Échec Pytest (Tentative #{attempt}) : Traceback ré-injecté pour auto-correction."
            print(f"[{self.nom}] {fail_msg}")
            publish_event(job_id, "pytest_failed", fail_msg, {"logs": last_error_log[:300], "attempt": attempt})

            attempt += 1

        print(f"[{self.nom}] ⚠️ Limite de tentatives ({max_attempts}) atteinte.")
        publish_event(job_id, "pytest_max_attempts", f"⚠️ Limite de {max_attempts} tentatives d'auto-correction atteinte.")

        return {
            "success": False,
            "attempts_count": max_attempts,
            "dev_implementation": dev_impl.dict(),
            "sandbox_results": sandbox_res,
            "workspace_payload": payload.dict()
        }

    def generer_et_tester_code(
        self,
        instruction: str,
        contexte_analyse: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Méthode legacy de repli pour script unique.
        """
        print(f"[{self.nom}] 💻 Début du processus de codage simple pour : '{instruction[:80]}...'")

        system_prompt = """Tu es un développeur expert Python. Écris un script autonome valide."""
        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=instruction,
            model=DEFAULT_MODEL,
            temperature=TEMP_CODEUR,
            json_mode=False,
        )

        clean_code = raw_response.strip()
        if "```python" in clean_code:
            clean_code = clean_code.split("```python")[1].split("```")[0].strip()
        elif "```" in clean_code:
            clean_code = clean_code.split("```")[1].split("```")[0].strip()

        sandbox_res = execute_code_in_sandbox(clean_code, timeout=10)
        return {
            "success": sandbox_res["success"],
            "attempts_count": 1,
            "code": clean_code,
            "sandbox_results": sandbox_res,
            "correction_history": []
        }
