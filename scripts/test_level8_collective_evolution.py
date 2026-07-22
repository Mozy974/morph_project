"""
Script d'intégration et de validation Level 8.0 — Auto-Évolution Collective & Swarm Multi-Guildes.
Valide la chaîne complète : PeerImprovementNetwork -> OrgSwarmRouter -> CapabilitySynthesizer -> FleetSwarmOptimizer.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.peer_improvement_network import PeerImprovementNetwork
from orchestrator.agents.org_swarm_router import OrgSwarmRouter
from orchestrator.agents.capability_synthesizer import CapabilitySynthesizer
from orchestrator.agents.fleet_swarm_optimizer import FleetSwarmOptimizer


def main():
    print("=" * 60)
    print("🚀 VALIDATION INTÉGRALE LEVEL 8.0 (AUTO-ÉVOLUTION COLLECTIVE & SWARM)")
    print("=" * 60)

    # 1. Validation PeerImprovementNetwork
    print("\n1️⃣ Test PeerImprovementNetwork...")
    p2p = PeerImprovementNetwork()
    critique_res = p2p.peer_critique("Codeur", "AutoCorrector", {"main_code": "def run(): pass"})
    assert "approved" in critique_res
    print("   ✅ PeerImprovementNetwork P2P fonctionnel !")

    # 2. Validation OrgSwarmRouter
    print("\n2️⃣ Test OrgSwarmRouter...")
    router = OrgSwarmRouter()
    plan_res = router.route_task_to_guilds("Déployer une API FastAPI sécurisée sur Kubernetes")
    assert "primary_guild" in plan_res
    print(f"   ✅ OrgSwarmRouter routage guilde : '{plan_res.get('primary_guild')}' !")

    # 3. Validation CapabilitySynthesizer
    print("\n3️⃣ Test CapabilitySynthesizer...")
    synth = CapabilitySynthesizer()
    cap_res = synth.synthesize_capability("JWT Token Verifier", "Valider les jetons JWT HS256.")
    assert os.path.exists(cap_res["file_path"])
    print(f"   ✅ CapabilitySynthesizer capacité synthétisée : {cap_res['status']} !")

    # 4. Validation FleetSwarmOptimizer
    print("\n4️⃣ Test FleetSwarmOptimizer...")
    optimizer = FleetSwarmOptimizer()
    opt_res = optimizer.optimize_fleet_telemetry({"active_jobs": 5, "error_rate": 0.01})
    assert "strategy" in opt_res
    print(f"   ✅ FleetSwarmOptimizer stratégie adoptée : '{opt_res['strategy']}' !")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES COMPOSANTS LEVEL 8.0 SONT ETABLIS ET VALIDÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
