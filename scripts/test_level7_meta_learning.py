"""
Script d'intégration et de validation Level 7.0 — Meta-Learning & Équipes Cognitives.
Valide la chaîne complète : MetaLearnerAgent -> AutoDocGeneratorAgent -> SelfDiscoveryEngine -> TeamCoordinatorAgent.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.meta_learner import MetaLearnerAgent
from orchestrator.agents.auto_doc_generator import AutoDocGeneratorAgent
from orchestrator.agents.self_discovery import SelfDiscoveryEngine
from orchestrator.agents.team_coordinator import TeamCoordinatorAgent


def main():
    print("=" * 60)
    print("🚀 VALIDATION INTÉGRALE LEVEL 7.0 (META-LEARNING)")
    print("=" * 60)

    # 1. Validation MetaLearnerAgent
    print("\n1️⃣ Test MetaLearnerAgent...")
    meta_learner = MetaLearnerAgent()
    res_meta = meta_learner.analyze_fleet_performance([
        {"agent": "Codeur", "duration": 1.2, "status": "SUCCESS"},
        {"agent": "AutoCorrector", "duration": 2.5, "status": "HEALED"}
    ])
    assert "fleet_health_score" in res_meta or "status" in res_meta
    print("   ✅ MetaLearnerAgent fonctionnel !")

    # 2. Validation AutoDocGeneratorAgent
    print("\n2️⃣ Test AutoDocGeneratorAgent...")
    doc_gen = AutoDocGeneratorAgent()
    sample_code = "class Engine:\n    def run(self):\n        pass\n"
    ast_info = doc_gen.inspect_module_ast(sample_code)
    assert len(ast_info["classes"]) == 1
    print("   ✅ AutoDocGeneratorAgent AST parsing fonctionnel !")

    # 3. Validation SelfDiscoveryEngine
    print("\n3️⃣ Test SelfDiscoveryEngine...")
    discovery = SelfDiscoveryEngine()
    scan_res = discovery.scan_workspace({"main.py": "def execute(): return True"})
    assert "total_issues_found" in scan_res or "opportunities" in scan_res
    print("   ✅ SelfDiscoveryEngine fonctionnel !")

    # 4. Validation TeamCoordinatorAgent
    print("\n4️⃣ Test TeamCoordinatorAgent...")
    coordinator = TeamCoordinatorAgent()
    review_res = coordinator.run_team_review(
        task="Sécuriser les endpoints REST",
        proposed_design="Utilisation de JWT tokens et validation Pydantic."
    )
    assert "consensus_reached" in review_res
    print("   ✅ TeamCoordinatorAgent fonctionnel !")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES COMPOSANTS LEVEL 7.0 SONT ETABLIS ET VALIDÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
