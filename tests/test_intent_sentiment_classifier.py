"""
Tests unitaires pour IntentSentimentClassifier (Cache Stratifié, TTL Dynamiques, Audit Trail RGPD).
"""

import pytest
from orchestrator.agents.intent_sentiment_classifier import IntentSentimentClassifier


def test_classify_intent_code_fr_urgent():
    classifier = IntentSentimentClassifier()
    res = classifier.classify("Écris en urgence une fonction Python pour corriger le crash de prod")
    assert res["intent"] == "INTENT_CODE"
    assert res["target_agent"] == "AgentCodeur"
    assert res["is_urgent"] is True
    assert res["ttl_seconds"] == 3600
    assert res["recommended_tone"] == "DIRECT_CONCISE_LOGS"


def test_classify_intent_research_ttl():
    classifier = IntentSentimentClassifier()
    res = classifier.classify("Search and investigate the documentation for this library")
    assert res["intent"] == "INTENT_RESEARCH"
    assert res["ttl_seconds"] == 86400


def test_stratified_cache_hits():
    classifier = IntentSentimentClassifier()
    res1 = classifier.classify("Rédiger un rapport et la documentation")
    assert res1["cache_level"] == "MISS"
    res2 = classifier.classify("Rédiger un rapport et la documentation")
    assert res2["cached"] is True
    assert res2["cache_level"] == "L1_MEM"


def test_gdpr_access_audit_trail_and_purge():
    classifier = IntentSentimentClassifier()
    audit = classifier.audit_access(user_id="user_sec_01", action="READ_DECRYPTED_FEEDBACK", job_id="job_777")
    assert audit["rgpd_compliant"] is True
    assert audit["user_id"] == "user_sec_01"
    assert len(classifier.audit_trail) == 1
    purged = classifier.purge_old_audit_logs(retention_days=30)
    assert purged == 0
    assert len(classifier.audit_trail) == 1

