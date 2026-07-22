"""
Agent Juridique — Conformité RGPD, Analyse de Contrats & Audits (orchestrator/agents/juridical_agent.py).
"""

import hashlib
import datetime
from typing import Dict, Any, List


class JuridicalAgent:
    """Agent spécialisé en audit de conformité RGPD et analyse juridique de contrats."""

    def __init__(self):
        self.name = "Agent Juridique"
        self.rgpd_rules = [
            {
                "rule": "storage_limitation",
                "keywords": ["indéfiniment", "indefinitely", "sans limite de temps", "forever"],
                "description": "Violation de la durée de conservation limitée (Art. 5.1.e RGPD)"
            },
            {
                "rule": "data_minimization",
                "keywords": ["toutes vos données", "all your data", "accès total"],
                "description": "Violation du principe de minimisation des données (Art. 5.1.c RGPD)"
            }
        ]

    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Analyse un texte contractuel et identifie les violations de la réglementation RGPD."""
        violations: List[Dict[str, str]] = []
        lower_text = contract_text.lower()

        for rule_info in self.rgpd_rules:
            for kw in rule_info["keywords"]:
                if kw in lower_text:
                    violations.append({
                        "rule": rule_info["rule"],
                        "severity": "HIGH",
                        "description": rule_info["description"]
                    })
                    break

        contract_hash = hashlib.sha256(contract_text.encode("utf-8")).hexdigest()
        is_compliant = len(violations) == 0

        return {
            "contract_hash": contract_hash,
            "compliant": is_compliant,
            "violations": violations,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def generate_legal_report(self, analysis: Dict[str, Any]) -> str:
        """Génère un rapport d'audit juridique formaté en Markdown."""
        status_str = "Conforme" if analysis.get("compliant") else "Non Conforme"
        violations = analysis.get("violations", [])

        report = f"""# Rapport d'Audit RGPD & Conformité Juridique
- **Statut d'Audit** : **{status_str}**
- **SHA-256 Empreinte Contrat** : `{analysis.get('contract_hash', '')[:16]}...`
- **Date d'Analyse** : `{analysis.get('timestamp', '')}`

---

## 🔍 Violations Identifiées ({len(violations)})

"""
        if not violations:
            report += "Aucune non-conformité majeure n'a été détectée dans les clauses analysées.\n"
        else:
            for v in violations:
                report += f"- **[{v.get('severity', 'HIGH')}]** `{v.get('rule', '')}` : {v.get('description', '')}\n"

        return report
