"""
Agent AutoCorrector (Self-Healing Framework) :
Analyse automatiquement les échecs d'exécution de la Sandbox Pytest (tracebacks, exceptions),
catégorise la cause racine des pannes et génère de façon autonome des patchs correctifs ciblés.
"""

import re
import json
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_CODEUR
from orchestrator.sandbox.workspace_runner import execute_workspace_tests
from orchestrator.memory.experience_replay import ExperienceReplayStore
from orchestrator.agents.prompt_optimizer import PromptOptimizerAgent


class AutoCorrectorAgent:
    def __init__(self):
        self.nom = "Auto-Corrector (Self-Healing)"
        self.replay_store = ExperienceReplayStore()
        self.prompt_optimizer = PromptOptimizerAgent()

    def analyser_echec_pytest(self, logs: str) -> Dict[str, Any]:
        """
        Extrait les informations clés à partir des logs d'erreur Pytest :
        - Type d'exception (AssertionError, TypeError, KeyError, AttributeError, etc.)
        - Fichier et ligne de la panne
        - Description exacte de l'erreur
        """
        analysis = {
            "failed_tests": [],
            "primary_error_type": "UnknownError",
            "error_summary": "",
            "raw_traceback": logs
        }

        # Détection des tests en FAILED
        failed_matches = re.findall(r"FAILED\s+([^\s:]+)::([^\s]+)", logs)
        if failed_matches:
            analysis["failed_tests"] = [f"{test_file}::{test_name}" for test_file, test_name in failed_matches]

        # Détection du type d'exception courante
        error_types = [
            "AssertionError", "TypeError", "ValueError", "KeyError",
            "AttributeError", "IndexError", "ImportError", "NameError",
            "ZeroDivisionError", "SyntaxError", "TimeoutError"
        ]
        for etype in error_types:
            if etype in logs:
                analysis["primary_error_type"] = etype
                break

        # Extraction des lignes de résumé d'erreur
        summary_lines = []
        for line in logs.splitlines():
            if "E   " in line or "FAILED " in line or "Error:" in line:
                summary_lines.append(line.strip())

        analysis["error_summary"] = "\n".join(summary_lines[-8:]) if summary_lines else logs[-500:]

        return analysis

    def generer_patch(
        self,
        instruction: str,
        files: Dict[str, str],
        error_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Sollicite le LLM pour générer un patch correctif chirurgical du fichier `main.py`
        afin d'éliminer l'erreur détectée.
        """
        default_system_prompt = """Tu es un expert en Auto-Correction de Code (Self-Healing Agent).
Un test automatisé a échoué dans la Sandbox.
Ton objectif est de corriger UNIQUEMENT le fichier de code source (main.py) pour résoudre l'erreur.

RÈGLES STRICTES :
1. Analyse minutieusement le type d'erreur et le traceback fourni.
2. Ne modifie JAMAIS le fichier de test immuable (test_main.py).
3. Réponds UNIQUEMENT avec un objet JSON structuré :
{
    "diagnostic": "Explication succincte de la cause de la panne",
    "corrected_main_code": "Code Python corrigé et complet pour main.py"
}"""
        system_prompt = self.prompt_optimizer.get_active_prompt("AutoCorrector", default_system_prompt)

        few_shot_context = self.replay_store.get_few_shot_prompt_context(error_analysis.get("error_summary", ""))

        user_prompt = f"INSTRUCTION DE DÉPART :\n{instruction}\n\n"
        if few_shot_context:
            user_prompt += f"{few_shot_context}\n"
        user_prompt += f"FICHIER ACTUEL main.py :\n```python\n{files.get('main.py', '')}\n```\n\n"

        if "test_main.py" in files:
            user_prompt += f"SUITE DE TESTS (test_main.py) :\n```python\n{files.get('test_main.py', '')}\n```\n\n"

        user_prompt += f"RAPPORT DE PANNE AUTOCORRECTEUR :\n"
        user_prompt += f"- Type d'erreur : {error_analysis['primary_error_type']}\n"
        user_prompt += f"- Tests échoués : {', '.join(error_analysis['failed_tests'])}\n"
        user_prompt += f"- Extrait de Traceback :\n{error_analysis['error_summary']}\n\n"
        user_prompt += "Génère le patch pour corriger main.py."

        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=DEFAULT_MODEL,
            temperature=TEMP_CODEUR,
            json_mode=True
        )

        try:
            data = json.loads(raw_response)
            return {
                "diagnostic": data.get("diagnostic", "Correction appliquée"),
                "main_code": data.get("corrected_main_code", files.get("main.py", ""))
            }
        except Exception:
            return {
                "diagnostic": "Patch brut appliqué",
                "main_code": raw_response
            }

        return {"diagnostic": "Aucune modification", "main_code": files.get("main.py", "")}

    def executer_auto_healing(
        self,
        instruction: str,
        files: Dict[str, str],
        max_attempts: int = 3,
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Boucle complète d'auto-correction (Self-Healing Loop) :
        1. Exécute les tests initialement.
        2. Si FAILED, déclenche l'analyse d'erreur et génère un patch.
        3. Re-teste jusqu'à obtention du statut GREEN ou épuisement des tentatives.
        """
        print(f"[{self.nom}] 🩺 Démarrage du protocole de Self-Healing...")
        publish_event(job_id, "auto_healing_start", "🩺 Lancement du protocole d'Auto-Correction autonome...")

        attempt = 1
        current_files = dict(files)
        healing_history = []

        while attempt <= max_attempts:
            print(f"[{self.nom}] 🧪 Validation Sandbox (Tentative #{attempt}/{max_attempts})...")
            res = execute_workspace_tests(current_files, timeout=15)

            if res["exit_code"] == 0:
                msg = f"🎉 GREEN ! Suite de tests passée avec succès à la tentative #{attempt} !"
                print(f"[{self.nom}] {msg}")
                publish_event(job_id, "auto_healing_success", msg, {"time": res["time"], "attempts": attempt})

                # Niveau 6.0 : Enregistrement de l'expérience de correction réussie
                if healing_history:
                    last_h = healing_history[-1]
                    self.replay_store.record_experience(
                        error_traceback=last_h.get("error_summary", res["logs"]),
                        failing_code=files.get("main.py", ""),
                        patch_applied=current_files.get("main.py", ""),
                        resolved=True,
                        keywords=[last_h.get("error_type", "UnknownError")]
                    )

                return {
                    "success": True,
                    "attempts": attempt,
                    "files": current_files,
                    "final_logs": res["logs"],
                    "history": healing_history
                }

            # Échec détecté -> Analyse de la panne
            print(f"[{self.nom}] ⚠️ Échec détecté (Exit Code {res['exit_code']}). Analyse du Traceback...")
            analysis = self.analyser_echec_pytest(res["logs"])
            
            publish_event(
                job_id,
                "auto_healing_patching",
                f"🩺 Erreur {analysis['primary_error_type']} détectée. Génération du patch correctif...",
                {"error_type": analysis["primary_error_type"], "failed_tests": analysis["failed_tests"]}
            )

            # Génération et application du patch
            patch_info = self.generer_patch(instruction, current_files, analysis)
            current_files["main.py"] = patch_info["main_code"]

            healing_history.append({
                "attempt": attempt,
                "error_type": analysis["primary_error_type"],
                "error_summary": analysis["error_summary"],
                "diagnostic": patch_info["diagnostic"],
                "exit_code": res["exit_code"]
            })

            attempt += 1

        # Si toujours échoué après max_attempts -> Auto-Tuning du Prompt Système (Niveau 6.0)
        fail_msg = f"❌ Échec de l'Auto-Correction après {max_attempts} tentatives. Déclenchement de l'Auto-Tuning..."
        print(f"[{self.nom}] {fail_msg}")
        publish_event(job_id, "auto_healing_failed", fail_msg, {"history": healing_history})

        self.prompt_optimizer.optimize_prompt(
            agent_name="AutoCorrector",
            current_prompt="Tu es un expert en Auto-Correction de Code.",
            execution_failures=healing_history,
            success_rate=0.0
        )

        return {
            "success": False,
            "attempts": max_attempts,
            "files": current_files,
            "final_logs": res["logs"],
            "history": healing_history
        }

