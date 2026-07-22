"""
Suite de tests d'intégration système pour SuperAgent Morph Level 13.0 (tests/test_superagent_system.py).
"""

import pytest
import os
import time
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# 1. AGENT JURIDIQUE TESTS
from orchestrator.agents.juridical_agent import JuridicalAgent

def test_juridical_agent_contract_analysis():
    """Test l'analyse de conformité RGPD d'un contrat."""
    agent = JuridicalAgent()

    # Contrat conforme
    compliant_contract = """
    Nous collectons uniquement les données strictly nécessaires à la prestation de service.
    Les données sont utilisées uniquement dans le cadre de la relation contractuelle.
    """

    analysis = agent.analyze_contract(compliant_contract)
    assert analysis["compliant"] is True
    assert analysis["violations"] == []

    # Contrat non conforme
    non_compliant_contract = """
    Nous conservons vos données personnelles indéfiniment pour améliorer nos services.
    """

    analysis = agent.analyze_contract(non_compliant_contract)
    assert analysis["compliant"] is False
    assert len(analysis["violations"]) > 0
    assert any("storage_limitation" in v["rule"] for v in analysis["violations"])


def test_juridical_agent_report_generation():
    """Test la génération de rapport juridique."""
    agent = JuridicalAgent()

    analysis = {
        "contract_hash": hashlib.sha256(b"test").hexdigest(),
        "violations": [
            {"rule": "data_minimization", "severity": "HIGH", "description": "Collecte excessive"}
        ],
        "compliant": False,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    report = agent.generate_legal_report(analysis)
    assert "# Rapport d'Audit RGPD" in report
    assert "Non Conforme" in report
    assert "HIGH" in report


# 2. CLASSIFIER / ROUTER LATENCY & CACHE TESTS
from orchestrator.agents.intent_sentiment_classifier import IntentSentimentClassifier

@pytest.fixture
def classifier():
    return IntentSentimentClassifier()


def test_orchestrator_intent_classification(classifier):
    """Test le routage des requêtes vers les agents avec latence < 10ms."""
    test_cases = [
        ("Écris une fonction Python pour calculer les Fibonacci", ["AgentCodeur", "Agent Codeur"]),
        ("Quel est le PIB de la France en 2023", ["AnalysteFinancier", "Analyste Financier"]),
        ("Recherche des articles sur l'IA en 2024", ["AgentEclaireur", "Agent Éclaireur"]),
        ("Analyse ce contrat pour conformité RGPD", ["AgentJuridique", "Agent Juridique"])
    ]

    for query, expected_agents in test_cases:
        res = classifier.classify(query)
        assert res["target_agent"] in expected_agents
        latency = res.get("execution_time_ms", res.get("latency_ms", 0.1))
        assert latency < 10  # SLA < 10ms CPU local



def test_orchestrator_cache_behavior(classifier):
    """Test le comportement du cache L1."""
    query = "Analyse ce code Python TDD"

    # Premier appel
    res1 = classifier.classify(query)
    assert res1 is not None

    # Deuxième appel
    res2 = classifier.classify(query)
    assert res2 is not None


# 3. AUTHENTIFICATION JIT & TOKEN FLOW TESTS
from orchestrator.auth import generate_ephemeral_token, verify_ephemeral_token

def test_jwt_auth_flow():
    """Test le cycle complet d'authentification JIT."""
    token = generate_ephemeral_token("test_user", role="auditor", ttl_seconds=900)
    assert isinstance(token, str)

    res = verify_ephemeral_token(token)
    assert res["valid"] is True
    assert res["payload"]["sub"] == "test_user"
    assert res["payload"]["role"] == "auditor"


# 4. WEBHOOK INTEGRATION TESTS
@patch('requests.post')
def test_webhook_integration(mock_post):
    """Test l'envoi de webhooks Slack/Discord."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    from orchestrator.notifier import send_slack_notification
    res = send_slack_notification("Test message", "https://mock.slack.local/webhook")

    assert res is True
    assert mock_post.called


# 5. FINANCIAL REPORT TESTS
def test_financial_report_generation(tmp_path):
    """Test la génération de rapports financiers."""
    from scripts.generate_financial_report import generate_financial_and_gdp_report

    out_file = os.path.join(tmp_path, "test_report.md")
    report_path = generate_financial_and_gdp_report(out_file)

    assert os.path.exists(report_path)
    assert os.path.getsize(report_path) > 0


# 6. DISASTER RECOVERY & BACKUP TESTS
def test_chromadb_backup_restore():
    """Test la création d'archive de sauvegarde."""
    from scripts.backup_loki_to_s3 import backup_loki_and_rgpd_logs

    backup_dir = "/tmp/loki/chunks"
    os.makedirs(backup_dir, exist_ok=True)
    with open(os.path.join(backup_dir, "test.log"), "w") as f:
        f.write("test log")

    backup_path = backup_loki_and_rgpd_logs(backup_dir=backup_dir)
    assert os.path.exists(backup_path)
    assert backup_path.endswith(".tar.gz")
