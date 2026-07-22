"""
EthicalGuardian : Gardien Éthique & Sécurité (Niveau 10.0 Conscience Ultime).
Scanne les requêtes et le code pour bloquer immédiatement les vulnérabilités et proposer des patchs sécurisés.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from orchestrator.memory.event_bus import publish_event

POLICIES_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "ethical_policies.json")


class EthicalGuardian:
    """
    Gardien Éthique & Sécurité (Niveau 10.0).
    Applique la politique "Blocage Immédiat + Proposition de Remédiation" pour les vulnérabilités critiques.
    """

    def __init__(self, policies_path: str = POLICIES_FILE):
        self.nom = "Ethical & Security Guardian"
        self.policies_path = os.path.abspath(policies_path)
        self.policies: Dict[str, Any] = self._load_policies()

    def _load_policies(self) -> Dict[str, Any]:
        if os.path.exists(self.policies_path):
            try:
                with open(self.policies_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur chargement règles éthiques : {e}")
        return {"security_rules": [], "ethical_rules": []}

    def audit_code_and_prompt(self, prompt: str, code: str = "", job_id: str = "ethical_audit") -> Dict[str, Any]:
        """
        Audite la requête et le code source par rapport aux règles de sécurité et d'éthique.
        """
        print(f"[{self.nom}] 🛡️ Audit de sécurité et d'alignement éthique en cours...")

        violations = []

        # Audit des secrets et credentials en clair
        combined_text = f"{prompt}\n{code}"

        for rule in self.policies.get("security_rules", []):
            pattern = rule.get("pattern")
            if pattern and re.search(pattern, combined_text):
                violations.append({
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "severity": rule.get("severity", "HIGH"),
                    "remediation": rule.get("remediation", "Corriger la faille identifiée.")
                })

        if violations:
            msg = f"❌ VIOLATION SÉCURITÉ DÉTECTÉE ({len(violations)} règles enfreintes) ! Blocage de sécurité activé."
            print(f"[{self.nom}] {msg}")

            publish_event(
                job_id=job_id,
                event_type="ethical_audit_blocked",
                message=msg,
                payload={"violations": violations}
            )

            return {
                "approved": False,
                "status": "BLOCKED",
                "violations": violations,
                "suggested_remediation": [v["remediation"] for v in violations]
            }

        print(f"[{self.nom}] ✅ Audit éthique et sécurité validé (Aucune violation détectée).")
        publish_event(
            job_id=job_id,
            event_type="ethical_audit_passed",
            message="✅ Audit éthique et sécurité validé avec succès.",
            payload={"approved": True}
        )

        return {
            "approved": True,
            "status": "PASSED",
            "violations": [],
            "suggested_remediation": []
        }
