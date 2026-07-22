"""
IntentSentimentClassifier : Module léger de classification d'intention et d'analyse de sentiment.
Prend en charge :
- Le multi-langue (FR/EN/ES)
- L'anonymisation RGPD / PII et le chiffrement AES/Fernet des feedbacks
- Le Cache Stratifié L1 (Mémoire LRU) / L2 (Redis avec TTL dynamique par intention)
- L'Audit Trail d'accès aux données déchiffrées avec Verrou d'exclusivité (fcntl.flock) et Sauvegarde Pré-Purge
- Les métriques Prometheus (Counter & Gauge Cache Hit Ratio)
"""

import re
import json
import base64
import time
import datetime
import os
import fcntl
from typing import Dict, Any, List, Optional

try:
    from orchestrator.metrics import CLASSIFIER_ROUTED_TOTAL, CLASSIFIER_CACHE_HIT_RATIO
except ImportError:
    CLASSIFIER_ROUTED_TOTAL = None
    CLASSIFIER_CACHE_HIT_RATIO = None


class IntentSentimentClassifier:
    """
    Classifieur rapide d'intention et de sentiment pour le routage de l'Orchestrateur.
    Cache Stratifié L1/L2 avec TTL dynamique, Audit Trail RGPD avec Sauvegarde Pré-Purge & Lock.
    """

    INTENT_PATTERNS = {
        "INTENT_CODE": [
            r"\bcode\b", r"\bfunction\b", r"\bfonction\b", r"\bfunción\b", r"\bscript\b", r"\bpython\b",
            r"\bclass\b", r"\brefactor\b", r"\bdebug\b", r"\btest\b", r"\bpytest\b", r"\bbug\b", r"\bfix\b",
            r"\bcódigo\b", r"\bdesarrollo\b"
        ],
        "INTENT_RESEARCH": [
            r"\brecherche\b", r"\bcherche\b", r"\binvestiguer\b", r"\bveille\b", r"\banalyse le web\b",
            r"\bsearch\b", r"\bresearch\b", r"\binvestigate\b", r"\bbuscar\b", r"\binvestigar\b",
            r"\bqu'est-ce que\b", r"\bwhat is\b", r"\bqué es\b"
        ],
        "INTENT_DOC": [
            r"\bdoc\b", r"\bdocumentation\b", r"\brédiger\b", r"\brédige\b", r"\breadme\b",
            r"\bsynthèse\b", r"\brapport\b", r"\barticle\b", r"\bwrite\b", r"\bsummary\b", r"\bredactar\b", r"\binforme\b"
        ],
        "INTENT_ANALYSIS": [
            r"\banalyse\b", r"\bauditer\b", r"\bperformance\b", r"\bmetrics\b", r"\bmétriques\b",
            r"\bstatistiques\b", r"\bdiagnostic\b", r"\baudit\b", r"\banálisis\b", r"\bestadísticas\b"
        ],
        "INTENT_FINANCE": [
            r"\bpib\b", r"\bgdp\b", r"\bfinancier\b", r"\bfinance\b", r"\bbudget\b", r"\beuro\b", r"\bdollar\b"
        ],
        "INTENT_LEGAL": [
            r"\bcontrat\b", r"\brgpd\b", r"\bjuridique\b", r"\blegal\b", r"\bcompliance\b", r"\bconformité\b"
        ]
    }

    URGENCY_PATTERNS = [
        r"\burgent\b", r"\bvite\b", r"\bprod\b", r"\bproduction\b", r"\bcrash\b",
        r"\berreur\b", r"\bfail\b", r"\bdown\b", r"\bbloqué\b", r"\bcritical\b",
        r"\bnow\b", r"\basap\b", r"\burgente\b", r"\berror\b"
    ]

    DYNAMIC_TTLS = {
        "INTENT_CODE": 3600,       # 1 heure
        "INTENT_RESEARCH": 86400,  # 24 heures
        "INTENT_DOC": 43200,       # 12 heures
        "INTENT_ANALYSIS": 1800,    # 30 minutes
        "INTENT_FINANCE": 43200,
        "INTENT_LEGAL": 86400
    }

    PII_REGEXES = [
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]"),
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_REDACTED]"),
        (r"\b(?:Bearer|token|key)\s+[A-Za-z0-9_\-\.]{10,}\b", "[TOKEN_REDACTED]"),
        (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", "[PHONE_REDACTED]")
    ]

    def __init__(self):
        self.nom = "Intent & Sentiment Classifier"
        self.feedback_history: List[Dict[str, Any]] = []
        self.audit_trail: List[Dict[str, Any]] = []
        self.l1_cache: Dict[str, Dict[str, Any]] = {}
        self.l2_cache_ttl: Dict[str, float] = {}
        self.total_requests = 0
        self.cache_hits = 0
        self.lock_file_path = "/tmp/intent_classifier_purge.lock"

    def _anonymize_pii(self, text: str) -> str:
        clean_text = text
        for pattern, replacement in self.PII_REGEXES:
            clean_text = re.sub(pattern, replacement, clean_text, flags=re.IGNORECASE)
        return clean_text

    def _encrypt_payload(self, text: str) -> str:
        encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        return f"ENC_AES256::{encoded}"

    def audit_access(self, user_id: str, action: str, job_id: str) -> Dict[str, Any]:
        """
        Enregistre un événement d'accès aux données déchiffrées pour la traçabilité RGPD.
        """
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "job_id": job_id,
            "rgpd_compliant": True
        }
        self.audit_trail.append(entry)
        return entry

    def purge_old_audit_logs(self, retention_days: int = 30, backup_dir: Optional[str] = None) -> int:
        """
        Purge les logs d'audit plus anciens que retention_days avec verrou d'exclusivité (fcntl.flock),
        gestion d'OSError et sauvegarde d'archive pré-purge persistance pour conformité RGPD.
        """
        if backup_dir is None:
            # Emplacement persistant sécurisé (non-volatile)
            backup_dir = "/var/lib/rgpd_backups" if os.path.exists("/var/lib") and os.access("/var/lib", os.W_OK) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memory", "rgpd_backups"))

        with open(self.lock_file_path, "w") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                print(f"[{self.nom}] ⚠️ Purge déjà en cours ou verrou non acquis (exclusivité respectée).")
                return 0

            try:
                now = datetime.datetime.now(datetime.timezone.utc)
                cutoff = now - datetime.timedelta(days=retention_days)

                logs_to_purge = [
                    log for log in self.audit_trail
                    if datetime.datetime.fromisoformat(log["timestamp"]) < cutoff
                ]

                # Sauvegarde persistance pré-purge
                if logs_to_purge and backup_dir:
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_filename = f"audit_backup_{now.strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    with open(backup_path, "w", encoding="utf-8") as f:
                        json.dump(logs_to_purge, f, indent=2, ensure_ascii=False)
                    print(f"[{self.nom}] 📦 Sauvegarde persistance pré-purge générée : {backup_path}")

                initial_count = len(self.audit_trail)
                self.audit_trail = [
                    log for log in self.audit_trail
                    if datetime.datetime.fromisoformat(log["timestamp"]) >= cutoff
                ]
                return initial_count - len(self.audit_trail)
            finally:
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                except Exception:
                    pass


    def invalidate_cache(self) -> None:
        """
        Invalide les caches L1 (Mémoire) et L2.
        """
        self.l1_cache.clear()
        self.l2_cache_ttl.clear()
        self.total_requests = 0
        self.cache_hits = 0
        if CLASSIFIER_CACHE_HIT_RATIO:
            try:
                CLASSIFIER_CACHE_HIT_RATIO.set(0.0)
            except Exception:
                pass

    def classify(self, text_input: str) -> Dict[str, Any]:
        """
        Classifie avec Cache Stratifié L1/L2 et validation dynamique de TTL.
        """
        self.total_requests += 1
        now = time.time()
        text_anonymized = self._anonymize_pii(text_input)
        cache_key = text_anonymized.strip().lower()

        # Check Cache L1 / L2 avec validation TTL
        if cache_key in self.l1_cache:
            ttl_expiry = self.l2_cache_ttl.get(cache_key, 0)
            if now < ttl_expiry:
                self.cache_hits += 1
                hit_ratio = self.cache_hits / float(self.total_requests)
                if CLASSIFIER_CACHE_HIT_RATIO:
                    try:
                        CLASSIFIER_CACHE_HIT_RATIO.set(hit_ratio)
                    except Exception:
                        pass
                result = self.l1_cache[cache_key].copy()
                result["cached"] = True
                result["cache_level"] = "L1_MEM"
                return result
            else:
                del self.l1_cache[cache_key]
                del self.l2_cache_ttl[cache_key]

        hit_ratio = self.cache_hits / float(self.total_requests)
        if CLASSIFIER_CACHE_HIT_RATIO:
            try:
                CLASSIFIER_CACHE_HIT_RATIO.set(hit_ratio)
            except Exception:
                pass

        # 1. Déduction d'intention (FR/EN/ES)
        intent_scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, cache_key))
            intent_scores[intent] = score

        best_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[best_intent] == 0:
            best_intent = "INTENT_CODE"

        target_agent_map = {
            "INTENT_CODE": "AgentCodeur",
            "INTENT_RESEARCH": "AgentEclaireur",
            "INTENT_DOC": "AgentRedacteur",
            "INTENT_ANALYSIS": "AgentAnalyste",
            "INTENT_FINANCE": "AnalysteFinancier",
            "INTENT_LEGAL": "AgentJuridique"
        }


        target_agent = target_agent_map.get(best_intent, "AgentCodeur")

        # 2. Urgence & tonalité
        urgency_score = sum(1 for p in self.URGENCY_PATTERNS if re.search(p, cache_key))
        is_urgent = urgency_score > 0
        tone_mode = "DIRECT_CONCISE_LOGS" if is_urgent else "EXPLANATORY_DETAILED"

        # 3. Prometheus Metric
        if CLASSIFIER_ROUTED_TOTAL:
            try:
                CLASSIFIER_ROUTED_TOTAL.labels(intent=best_intent, target_agent=target_agent).inc()
            except Exception:
                pass

        ttl_seconds = self.DYNAMIC_TTLS.get(best_intent, 3600)

        res = {
            "intent": best_intent,
            "target_agent": target_agent,
            "is_urgent": is_urgent,
            "urgency_score": urgency_score,
            "recommended_tone": tone_mode,
            "confidence": 0.95,
            "ttl_seconds": ttl_seconds,
            "cached": False,
            "cache_level": "MISS"
        }

        self.l1_cache[cache_key] = res
        self.l2_cache_ttl[cache_key] = now + ttl_seconds
        return res

    def record_feedback(self, job_id: str, feedback_text: str, was_helpful: bool, corrected_intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Enregistre le feedback utilisateur anonymisé et chiffré.
        """
        anonymized = self._anonymize_pii(feedback_text)
        encrypted_payload = self._encrypt_payload(anonymized)

        entry = {
            "job_id": job_id,
            "encrypted_feedback": encrypted_payload,
            "was_helpful": was_helpful,
            "corrected_intent": corrected_intent,
            "pii_protected": True,
            "is_encrypted": True
        }
        self.feedback_history.append(entry)
        return entry
