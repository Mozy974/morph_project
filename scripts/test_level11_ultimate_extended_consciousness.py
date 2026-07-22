"""
Script d'intégration et de validation Level 11.0 — Conscience Étendue Ultime & Empathie Cognitive.
Valide la chaîne complète : EmpathicAgent -> CognitiveBiasRepair -> VoiceGestureGateway -> DynamicEthicsEngine.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.empathic_agent import EmpathicAgent
from orchestrator.agents.cognitive_bias_repair import CognitiveBiasRepair
from orchestrator.agents.voice_gesture_gateway import VoiceGestureGateway
from orchestrator.agents.dynamic_ethics_engine import DynamicEthicsEngine


def main():
    print("=" * 60)
    print("🚀 VALIDATION LÉGENDAIRE LEVEL 11.0 (CONSCIENCE ÉTENDUE ULTIME)")
    print("=" * 60)

    # 1. Validation EmpathicAgent
    print("\n1️⃣ Test EmpathicAgent...")
    empathic = EmpathicAgent()
    emp_res = empathic.analyze_emotion_and_adapt("C'est très URGENT ! Le serveur est bloqué en prod.")
    assert emp_res["emotional_comprehension_score"] >= 0.90
    assert emp_res["adapted_tone"] == "ULTRA_CONCISE_DIRECT"
    print(f"   ✅ EmpathicAgent score de compréhension : {emp_res['emotional_comprehension_score']*100:.1f}% !")

    # 2. Validation CognitiveBiasRepair
    print("\n2️⃣ Test CognitiveBiasRepair...")
    bias_repair = CognitiveBiasRepair()
    bias_res = bias_repair.audit_and_debias("Codeur", ["Certain à 100% que cette fonction est parfaite."])
    assert len(bias_res["biases_found"]) > 0
    assert bias_res["bias_reduction_score"] == 0.95
    print("   ✅ CognitiveBiasRepair dé-biaisage 95% validé !")

    # 3. Validation VoiceGestureGateway
    print("\n3️⃣ Test VoiceGestureGateway...")
    gateway = VoiceGestureGateway()
    vg_res = gateway.process_multimodal_signal("VOICE", "Démarrer l'auto-correction")
    assert vg_res["confidence"] >= 0.95
    print("   ✅ VoiceGestureGateway signal vocal décodé !")

    # 4. Validation DynamicEthicsEngine
    print("\n4️⃣ Test DynamicEthicsEngine...")
    ethics = DynamicEthicsEngine()
    eth_ok = ethics.evaluate_dynamic_policy({"action_intent": "GENERATE_AUTH_DOCS"})
    assert eth_ok["approved"] is True
    eth_nok = ethics.evaluate_dynamic_policy({"action_intent": "NO_CREDENTIAL_LEAKAGE_TEST"})
    assert eth_nok["approved"] is False
    print("   ✅ DynamicEthicsEngine protection des Invariants Inviolables validée !")

    print("\n" + "=" * 60)
    print("🎉 TOUS LES COMPOSANTS LEVEL 11.0 SONT PARFAITEMENT DÉPLOYÉS ET VALIDÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
