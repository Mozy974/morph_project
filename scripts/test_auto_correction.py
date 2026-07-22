#!/usr/bin/env python3
"""
Script de validation du prototype d'Auto-Correction des Échecs (Self-Healing).
"""

import os
import sys

# Ajout du dossier racine au PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.agents.auto_corrector import AutoCorrectorAgent


def test_analyse_logs():
    print("1. 🔍 Test d'analyse du Traceback Pytest...")
    corrector = AutoCorrectorAgent()
    
    sample_log = """
============================= FAILURES =============================
_________________________ test_calcul_facture ________________________
    def test_calcul_facture():
>       assert calcul_facture(100, 0.2) == 120.0
E       AssertionError: assert 100.0 == 120.0
E        +  where 100.0 = calcul_facture(100, 0.2)

FAILED test_main.py::test_calcul_facture - AssertionError: assert 100.0 == 120.0
======================== 1 failed in 0.05s =========================
"""
    analysis = corrector.analyser_echec_pytest(sample_log)
    print(f"   Type d'erreur détecté : {analysis['primary_error_type']}")
    print(f"   Tests en échec : {analysis['failed_tests']}")
    assert analysis["primary_error_type"] == "AssertionError"
    assert "test_main.py::test_calcul_facture" in analysis["failed_tests"]
    print("   ✅ Analyse de log valide !")


def test_auto_healing_execution():
    print("\n2. 🩺 Test de la boucle complète d'Auto-Correction (Self-Healing)...")
    corrector = AutoCorrectorAgent()

    # Code initial bogué (oublie d'ajouter la TVA)
    buggy_main = """
def calcul_facture(montant_ht: float, taux_tva: float) -> float:
    # BUG : retourne seulement le montant HT au lieu du TTC
    return montant_ht
"""

    # Test immuable exigeant le montant TTC
    immutable_test = """
import pytest
from main import calcul_facture

def test_calcul_facture():
    assert calcul_facture(100.0, 0.2) == 120.0
    assert calcul_facture(50.0, 0.1) == 55.0
"""

    files = {
        "main.py": buggy_main,
        "test_main.py": immutable_test
    }

    result = corrector.executer_auto_healing(
        instruction="Calculer le montant TTC d'une facture à partir du montant HT et du taux de TVA.",
        files=files,
        max_attempts=3,
        job_id="test_self_healing_1"
    )

    print(f"   Succès de l'Auto-Correction : {result['success']}")
    print(f"   Nombre de tentatives : {result['attempts']}")
    print(f"   Historique des diagnostics : {result['history']}")

    assert result["success"] is True, "L'auto-correction aurait dû réussir à réparer le code !"
    print("   ✅ Boucle de Self-Healing validée avec succès !")


def main():
    print("=" * 60)
    print("  🚀 VALIDATION DU PROTOTYPE D'AUTO-CORRECTION DES ÉCHECS")
    print("=" * 60)

    test_analyse_logs()
    test_auto_healing_execution()

    print("\n=" * 60)
    print("  ✅ TOUS LES TESTS D'AUTO-CORRECTION SONT VALIDÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()
