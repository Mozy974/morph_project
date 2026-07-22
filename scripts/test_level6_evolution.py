"""
Script d'intégration et de validation Level 6.0 — Agents Auto-Évolutifs.
Valide la chaîne complète : PromptOptimizerAgent -> AgentFactory -> ExperienceReplayStore.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.prompt_optimizer import PromptOptimizerAgent
from orchestrator.agents.agent_factory import AgentFactory
from orchestrator.memory.experience_replay import ExperienceReplayStore
from orchestrator.agents.auto_corrector import AutoCorrectorAgent


def main():
    print("=" * 60)
    print("🚀 VALIDATION BÉNÉVOLE ET INTÉGRATION LEVEL 6.0")
    print("=" * 60)

    # 1. Validation ExperienceReplayStore
    print("\n1️⃣ Test ExperienceReplayStore...")
    exp_store = ExperienceReplayStore()
    exp_store.record_experience(
        error_traceback="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        failing_code="res = a + b",
        patch_applied="res = int(a) + int(b)",
        resolved=True,
        keywords=["TypeError"]
    )
    ctx = exp_store.get_few_shot_prompt_context("TypeError operand +")
    assert "FEW-SHOT REPLAY" in ctx
    print("   ✅ ExperienceReplayStore fonctionnel !")

    # 2. Validation AgentFactory
    print("\n2️⃣ Test AgentFactory...")
    factory = AgentFactory()
    agent = factory.synthesize_agent(
        domain_need="sql_spanner_optimizer",
        task_description="Optimiser les requêtes SQL complexes pour Cloud Spanner."
    )
    assert agent.nom is not None
    assert agent.domain == "sql_spanner_optimizer"
    print(f"   ✅ Agent synthetisé : '{agent.nom}' (Domaine: {agent.domain})")

    # 3. Validation PromptOptimizerAgent
    print("\n3️⃣ Test PromptOptimizerAgent...")
    optimizer = PromptOptimizerAgent()
    prompt_res = optimizer.get_active_prompt("AutoCorrector", "Prompt d'origine")
    assert prompt_res is not None
    print(f"   ✅ PromptOptimizerAgent prêt avec prompt actif pour 'AutoCorrector'")

    # 4. Validation AutoCorrector avec intégration Level 6.0
    print("\n4️⃣ Test d'intégration AutoCorrectorAgent...")
    corrector = AutoCorrectorAgent()
    assert hasattr(corrector, "replay_store")
    assert hasattr(corrector, "prompt_optimizer")
    print("   ✅ AutoCorrectorAgent prêt avec briques Level 6.0 intégrées !")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES COMPOSANTS LEVEL 6.0 SONT VALIDÉS ET FONCTIONNELS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
