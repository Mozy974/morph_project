"""
Script d'intégration et de validation Level 9.0 — Conscience Collective & Symbiose Humain-IA.
Valide la chaîne complète : SharedCollectiveMind -> SystemAutoRepair -> DistributedRLEngine -> SymbioticHumanInterface.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.shared_collective_mind import SharedCollectiveMind
from orchestrator.agents.system_auto_repair import SystemAutoRepair
from orchestrator.agents.distributed_rl_engine import DistributedRLEngine
from orchestrator.agents.symbiotic_human_interface import SymbioticHumanInterface


def main():
    print("=" * 60)
    print("🚀 VALIDATION INTÉGRALE LEVEL 9.0 (CONSCIENCE COLLECTIVE & SYMBIOSE)")
    print("=" * 60)

    # 1. Validation SharedCollectiveMind
    print("\n1️⃣ Test SharedCollectiveMind...")
    mind = SharedCollectiveMind()
    state = mind.update_mind_state(
        focus="Global Swarm Optimization",
        belief_updates=["TDD quality set to 80% weight"],
        context_data={"level": "9.0"}
    )
    assert state["collective_focus"] == "Global Swarm Optimization"
    print("   ✅ SharedCollectiveMind synchronisé avec succès !")

    # 2. Validation SystemAutoRepair
    print("\n2️⃣ Test SystemAutoRepair...")
    repair = SystemAutoRepair()
    safe_res = repair.evaluate_and_repair("REDIS_RECONNECT", {})
    assert safe_res["requires_hitl"] is False
    crit_res = repair.evaluate_and_repair("POSTGRES_SCHEMA_MIGRATION", {})
    assert crit_res["requires_hitl"] is True
    print("   ✅ SystemAutoRepair stratégie graduée autonomie/HITL validée !")

    # 3. Validation DistributedRLEngine
    print("\n3️⃣ Test DistributedRLEngine...")
    rl_engine = DistributedRLEngine(weight_tdd=0.8, weight_speed=0.2)
    score_res = rl_engine.calculate_reward_score(tdd_passed=True, attempts=1, duration_sec=8.0)
    assert score_res["reward_score"] == 1.0
    print(f"   ✅ DistributedRLEngine reward score calculé : {score_res['reward_score']} (80/20) !")

    # 4. Validation SymbioticHumanInterface
    print("\n4️⃣ Test SymbioticHumanInterface...")
    symbiotic = SymbioticHumanInterface()
    chat_res = symbiotic.clarify_human_intent("Développer une API REST autonome")
    assert "intent_clear" in chat_res
    print("   ✅ SymbioticHumanInterface dialogue partenaire validé !")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES COMPOSANTS LEVEL 9.0 SONT SCELLES ET VALIDÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
