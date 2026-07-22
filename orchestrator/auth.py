"""
Module d'Authentification & Gestion des Accès Temporaires JIT (Just-In-Time) (orchestrator/auth.py).
Génère des jetons éphémères sécurisés avec expiration dynamique et détection des tentatives suspectes.
"""

import os
import time
import hmac
import hashlib
import json
import base64
from typing import Dict, Any, Optional

try:
    from orchestrator.metrics import Counter
    SUSPICIOUS_ACCESS_COUNTER = Counter(
        "superagent_suspicious_access_attempts_total",
        "Nombre total de tentatives d'accès suspectes ou non autorisées",
        ["reason"]
    )
except Exception:
    SUSPICIOUS_ACCESS_COUNTER = None

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "superagent-secret-jit-key-2026")


def generate_ephemeral_token(user_id: str, role: str = "operator", ttl_seconds: int = 900) -> str:
    """Génère un jeton d'accès temporaire éphémère (TTL par défaut: 15 minutes)."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_ephemeral_token(token: str) -> Dict[str, Any]:
    """Vérifie la validité d'un jeton éphémère et enregistre les tentatives suspectes."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            if SUSPICIOUS_ACCESS_COUNTER:
                SUSPICIOUS_ACCESS_COUNTER.labels(reason="malformed_token").inc()
            return {"valid": False, "reason": "Jeton malformé"}

        header_b64, payload_b64, sig_b64 = parts
        signature_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
        ).decode().rstrip("=")

        if not hmac.compare_digest(sig_b64, expected_sig):
            if SUSPICIOUS_ACCESS_COUNTER:
                SUSPICIOUS_ACCESS_COUNTER.labels(reason="invalid_signature").inc()
            return {"valid": False, "reason": "Signature invalide / tentative d'usurpation"}

        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "==")
        payload = json.loads(payload_bytes.decode())

        if time.time() > payload.get("exp", 0):
            if SUSPICIOUS_ACCESS_COUNTER:
                SUSPICIOUS_ACCESS_COUNTER.labels(reason="expired_token").inc()
            return {"valid": False, "reason": "Jeton éphémère expiré"}

        return {"valid": True, "payload": payload}

    except Exception as e:
        if SUSPICIOUS_ACCESS_COUNTER:
            SUSPICIOUS_ACCESS_COUNTER.labels(reason="exception").inc()
        return {"valid": False, "reason": f"Erreur de vérification: {e}"}
