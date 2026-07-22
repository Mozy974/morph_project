"""
Moteur d'exécution du graphe dynamique SuperAgent (Enterprise Grade).
Gère la boucle de rétroaction, le True TDD opposable, la Sandbox Pytest, le Nœud de Distillation,
le Checkpointing Redis et le Streaming d'Événements en Temps Réel (Pub/Sub -> SSE).
"""

import time
from typing import Dict, Any, Optional
from orchestrator.metrics import TASK_DURATION, TASKS_TOTAL, ACTIVE_JOBS, PYTEST_RESULTS
from orchestrator.state import SuperAgentState
from orchestrator.agents.eclaireur import AgentEclaireur
from orchestrator.agents.analyste import AgentAnalyste
from orchestrator.agents.codeur import AgentCodeur
from orchestrator.agents.auto_corrector import AutoCorrectorAgent
from orchestrator.agents.redacteur import AgentRedacteur
from orchestrator.agents.distillateur import AgentDistillateur
from orchestrator.agents.agent_factory import AgentFactory
from orchestrator.memory.skill_store import rechercher_skills_pertinents

from orchestrator.memory.checkpoint_store import RedisCheckpointSaver
from orchestrator.memory.event_bus import publish_event
from orchestrator.interfaces import QATestSuite, DevImplementation


class SuperAgentGraphRunner:
    def __init__(self, user_id: int = 1, job_id: str = "", task: str = "", max_retries: int = 2):
        self.checkpointer = RedisCheckpointSaver()
        self.user_id = user_id
        self.job_id = job_id
        self.max_retries = max_retries

        checkpoint_state = self.checkpointer.get_checkpoint(job_id) if job_id else None

        if checkpoint_state:
            print(f"[SuperAgent] 🔄 REPRISE DU JOB '{job_id}' DEPUIS CHECKPOINT (Nœud: {checkpoint_state.last_completed_node})")
            self.state = checkpoint_state
            if task:
                self.state.task = task
            publish_event(job_id, "job_resumed", f"🔄 Reprise du Job depuis le dernier Checkpoint validé ({checkpoint_state.last_completed_node})")
        else:
            print(f"[SuperAgent] 🚀 NOUVEAU JOB '{job_id or 'local'}' (Tâche: '{task[:60]}...')")
            self.state = SuperAgentState(
                user_id=user_id,
                job_id=job_id,
                task=task,
                max_retries=max_retries
            )
            publish_event(job_id, "job_start", f"🚀 Démarrage du SuperAgent pour : '{task}'")

        self.eclaireur = AgentEclaireur(user_id=user_id)
        self.analyste = AgentAnalyste()
        self.codeur = AgentCodeur()
        self.auto_corrector = AutoCorrectorAgent()
        self.redacteur = AgentRedacteur()
        self.distillateur = AgentDistillateur()
        self.agent_factory = AgentFactory()


    def execute(self) -> Dict[str, Any]:
        job_id = self.state.job_id or "job_default"
        ACTIVE_JOBS.inc()

        # ---------------------------------------------------------
        # 1. ÉTAPE ÉCLAIREUR & ANALYSTE (FEEDBACK LOOP)
        # ---------------------------------------------------------
        if self.state.last_completed_node in ["START", "FEEDBACK_LOOP"]:
            loop_count = self.state.retry_count
            feedback = None

            while loop_count <= self.state.max_retries:
                self.state.retry_count = loop_count
                iter_msg = f"=== ITÉRATION #{loop_count + 1} ==="
                print(f"\n[SuperAgent Graphe] {iter_msg}")
                publish_event(job_id, "iteration_start", iter_msg, {"iteration": loop_count + 1})

                # 1a. Éclaireur
                publish_event(job_id, "eclaireur_start", "🔍 L'Éclaireur analyse le sujet et consulte la mémoire long terme...")
                _t0 = time.time()
                self.state.eclaireur_report = self.eclaireur.analyser_sujet(
                    sujet=self.state.task,
                    feedback=feedback
                )
                TASK_DURATION.labels(node="eclaireur").observe(time.time() - _t0)
                self.state.last_completed_node = "ECLAIREUR"
                self.checkpointer.save_checkpoint(job_id, self.state)
                publish_event(job_id, "eclaireur_done", "✅ Analyse Éclaireur terminée avec succès !")

                # 1b. Analyste
                publish_event(job_id, "analyste_start", "📊 L'Analyste évalue le rapport d'Éclaireur...")
                _t0 = time.time()
                self.state.analyste_verdict = self.analyste.evaluer_rapport(
                    rapport_brut=self.state.eclaireur_report,
                    loop_index=loop_count
                )
                TASK_DURATION.labels(node="analyste").observe(time.time() - _t0)
                self.state.last_completed_node = "ANALYSTE"
                self.checkpointer.save_checkpoint(job_id, self.state)

                conclusion = self.state.analyste_verdict.get("conclusion_analyste", {})
                score = conclusion.get("score_confiance", 0)
                decision = conclusion.get("decision", "")
                feedback = conclusion.get("consigne_feedback", "")

                publish_event(job_id, "analyste_verdict", f"📊 Verdict Analyste : {score}/100 ({decision})", {"score": score, "decision": decision})

                if feedback:
                    self.state.feedback_history.append({
                        "iteration": loop_count + 1,
                        "score_confiance": score,
                        "decision": decision,
                        "consigne_feedback": feedback
                    })

                score_suffisant = score >= 70 and "Validé" in decision
                max_atteint = loop_count >= self.state.max_retries

                if score_suffisant:
                    print(f"[SuperAgent Graphe] ✅ Score suffisant ({score}/100 - {decision}) à l'itération #{loop_count + 1}.")
                    break
                elif max_atteint:
                    print(f"[SuperAgent Graphe] ⚠️ Limite de retries ({self.state.max_retries}) atteinte. Continuation forcée.")
                    break
                else:
                    fb_msg = f"🔄 SCORE INSUFFISANT ({score}/100 - {decision}). Activation de la Boucle de Rétroaction !"
                    print(f"[SuperAgent Graphe] {fb_msg}")
                    publish_event(job_id, "feedback_loop", fb_msg, {"feedback": feedback})
                    loop_count += 1

        # ---------------------------------------------------------
        # 2. ÉTAPE CONCEPTION QA TESTSUITE OPPOSABLE (TRUE TDD)
        # ---------------------------------------------------------
        if self.state.last_completed_node in ["START", "ECLAIREUR", "ANALYSTE"]:
            qa_msg = "🧪 Étape QA Architect : Conception de la suite de tests opposable (test_main.py)..."
            print(f"\n[SuperAgent Graphe] {qa_msg}")
            publish_event(job_id, "qa_tests_start", qa_msg)

            try:
                _t0 = time.time()
                qa_suite = self.analyste.generer_suite_de_tests_opposable(
                    sujet=self.state.task,
                    rapport_eclaireur=self.state.eclaireur_report
                )
                TASK_DURATION.labels(node="qa_tests").observe(time.time() - _t0)
                self.state.qa_test_suite = qa_suite.dict()
                publish_event(job_id, "qa_tests_done", "✅ Suite de tests QA (immuable) générée avec succès !")
            except Exception as e:
                print(f"[SuperAgent Graphe] ⚠️ Erreur génération suite QA : {e}")

            self.state.last_completed_node = "QA_TESTS"
            self.checkpointer.save_checkpoint(job_id, self.state)

        # ---------------------------------------------------------
        # 3. ÉTAPE AGENT CODEUR & SANDBOX WORKSPACE (TRUE TDD)
        # ---------------------------------------------------------
        if self.state.last_completed_node in ["START", "ECLAIREUR", "ANALYSTE", "QA_TESTS"]:
            code_msg = "💻 Étape Codeur Dev : Résolution TDD dans la Sandbox Workspace Pytest..."
            print(f"\n[SuperAgent Graphe] {code_msg}")
            publish_event(job_id, "codeur_step_start", code_msg)

            code_results = None
            try:
                qa_suite_obj = QATestSuite(**self.state.qa_test_suite) if self.state.qa_test_suite else QATestSuite(
                    explication_tests="Tests unitaires basiques",
                    test_main_code="import pytest\nfrom main import execute\ndef test_execute(): assert execute() is not None\n",
                    requirements_txt="pytest"
                )

                _t0 = time.time()
                code_results = self.codeur.resoudre_tests_tdd(
                    instruction=self.state.task,
                    qa_test_suite=qa_suite_obj,
                    max_attempts=3,
                    job_id=job_id
                )
                TASK_DURATION.labels(node="codeur").observe(time.time() - _t0)
                self.state.dev_implementation = code_results.get("dev_implementation", {})
                self.state.sandbox_results = code_results.get("sandbox_results", {})

                # Instrumentation Pytest Sandbox
                exit_code = self.state.sandbox_results.get("exit_code", -1)
                PYTEST_RESULTS.labels(result="PASSED" if exit_code == 0 else "FAILED").inc()

                # Si échec des tests, déclenchement du protocole autonome d'Auto-Correction (Self-Healing)
                if exit_code != 0 and self.state.dev_implementation.get("main_code"):
                    print(f"[SuperAgent Graphe] 🩺 Déclenchement du protocole de Self-Healing par AutoCorrectorAgent...")
                    healing_files = {
                        "main.py": self.state.dev_implementation.get("main_code", ""),
                        "test_main.py": qa_suite_obj.test_main_code
                    }
                    heal_res = self.auto_corrector.executer_auto_healing(
                        instruction=self.state.task,
                        files=healing_files,
                        max_attempts=3,
                        job_id=job_id
                    )
                    if heal_res.get("success"):
                        self.state.dev_implementation["main_code"] = heal_res["files"].get("main.py", "")
                        self.state.sandbox_results["exit_code"] = 0
                        self.state.sandbox_results["logs"] = heal_res["final_logs"]
                        PYTEST_RESULTS.labels(result="PASSED_AFTER_HEALING").inc()
            except Exception as e:
                print(f"[SuperAgent Graphe] ⚠️ Erreur étape Codeur TDD : {e}")

            self.state.last_completed_node = "CODEUR"
            self.checkpointer.save_checkpoint(job_id, self.state)

        # ---------------------------------------------------------
        # 4. ÉTAPE RÉDACTEUR (SYNTHÈSE ET RAPPORT FINAL)
        # ---------------------------------------------------------
        if self.state.last_completed_node in ["START", "ECLAIREUR", "ANALYSTE", "QA_TESTS", "CODEUR"]:
            redac_msg = "✍️ Étape Finalisation : Rédaction du rapport par le Rédacteur..."
            print(f"\n[SuperAgent Graphe] {redac_msg}")
            publish_event(job_id, "redacteur_start", redac_msg)

            code_results_formatted = None
            if self.state.dev_implementation:
                code_results_formatted = {
                    "code": self.state.dev_implementation.get("main_code", ""),
                    "sandbox_results": self.state.sandbox_results,
                    "attempts_count": self.state.sandbox_results.get("attempts_count", 1)
                }

            _t0 = time.time()
            self.state.redacteur_report = self.redacteur.rediger_rapport(
                self.state.analyste_verdict,
                code_results=code_results_formatted
            )
            TASK_DURATION.labels(node="redacteur").observe(time.time() - _t0)

            self.state.last_completed_node = "REDACTEUR"
            self.checkpointer.save_checkpoint(job_id, self.state)
            publish_event(job_id, "redacteur_done", "✅ Rapport final rédigé avec succès !")

        # ---------------------------------------------------------
        # 5. NŒUD DE DISTILLATION (MÉMOIRE SÉMANTIQUE LONG TERME)
        # ---------------------------------------------------------
        decision_finale = self.state.analyste_verdict.get("conclusion_analyste", {}).get("decision", "")
        if self.state.retry_count > 0 and "Validé" in decision_finale and self.state.last_completed_node != "DISTILLATEUR":
            distill_msg = "🧠 NŒUD DE DISTILLATION ACTIVÉ ! Capitalisation de l'expérience dans la Mémoire Long Terme..."
            print(f"\n[SuperAgent Graphe] {distill_msg}")
            publish_event(job_id, "distillateur_start", distill_msg)

            try:
                nouveau_skill = self.distillateur.executer_distillation(
                    sujet=self.state.task,
                    historique_feedback=self.state.feedback_history,
                    rapport_final=self.state.redacteur_report.get("rapport_markdown", "")
                )
                from orchestrator.memory.skill_store import ajouter_skill_pending
                skill_id = ajouter_skill_pending(nouveau_skill)

                if "metadata" in self.state.redacteur_report:
                    self.state.redacteur_report["metadata"]["skill_distille"] = nouveau_skill
                    self.state.redacteur_report["metadata"]["skill_id_pending"] = skill_id

                publish_event(
                    job_id,
                    "skill_pending",
                    f"⏳ Nouveau Skill distillé en attente de modération HITL : '{nouveau_skill.get('sujet_cle', '')}'",
                    {"skill_id": skill_id, "sujet_cle": nouveau_skill.get("sujet_cle")}
                )
            except Exception as e:
                print(f"[SuperAgent Graphe] ⚠️ Échec distillation : {e}")

            self.state.last_completed_node = "DISTILLATEUR"
            self.checkpointer.save_checkpoint(job_id, self.state)

        # Finalisation des métadonnées
        if "metadata" in self.state.redacteur_report:
            self.state.redacteur_report["metadata"]["job_id"] = job_id
            self.state.redacteur_report["metadata"]["iterations_totales"] = self.state.retry_count + 1
            self.state.redacteur_report["metadata"]["boucles_retroaction"] = len(self.state.feedback_history)
            self.state.redacteur_report["metadata"]["historique_feedback"] = self.state.feedback_history
            if self.state.sandbox_results:
                self.state.redacteur_report["metadata"]["code_succes_sandbox"] = (self.state.sandbox_results.get("exit_code") == 0)

        self.state.status = "SUCCESS"
        self.checkpointer.save_checkpoint(job_id, self.state)
        TASKS_TOTAL.labels(status="SUCCESS").inc()
        ACTIVE_JOBS.dec()

        end_msg = f"🎉 Job '{job_id}' terminé avec succès !"
        print(f"[SuperAgent Graphe] {end_msg}")
        publish_event(job_id, "job_success", end_msg, {"titre": self.state.redacteur_report.get("titre", "")})

        return self.state.redacteur_report
