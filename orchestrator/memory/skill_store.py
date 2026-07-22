"""
Gestionnaire de la Mémoire Sémantique Long Terme avec gouvernance Human-in-the-Loop (HITL) et Dédoublonnage IA.
Persiste et modère les directives correctives apprises lors des itérations du SuperAgent.

Utilise PostgreSQL (via SkillRepository) comme source de vérité principale,
avec fallback automatique sur le fichier JSON si la base est inaccessible.
"""
import os
import json
import re
import uuid
import datetime
from typing import List, Dict, Any, Optional

SKILLS_FILE = os.path.join(os.path.dirname(__file__), "long_term_skills.json")

# --- Connexion PostgreSQL (lazy, avec fallback) ---
_skill_repo = None
_db_session = None


def _get_db_session():
    """Retourne une session DB ou None si PostgreSQL est inaccessible."""
    global _db_session
    if _db_session is not None:
        return _db_session
    try:
        from orchestrator.database import SessionLocal
        _db_session = SessionLocal()
        return _db_session
    except Exception:
        return None


def _get_skill_repo():
    """Retourne le SkillRepository ou None si PostgreSQL est inaccessible."""
    global _skill_repo
    if _skill_repo is not None:
        return _skill_repo
    db = _get_db_session()
    if db is not None:
        from orchestrator.repositories import SkillRepository
        _skill_repo = SkillRepository(db)
        return _skill_repo
    return None


def _has_postgres() -> bool:
    """Vérifie si PostgreSQL est disponible."""
    return _get_skill_repo() is not None


class SkillStatus:
    PENDING = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# =============================================================================
# HELPERS : Conversion entre format dict (legacy) et modèles SQLAlchemy
# =============================================================================

def _skill_to_dict(skill) -> Dict[str, Any]:
    """Convertit un objet Skill SQLAlchemy en dict (format legacy)."""
    return {
        "id": skill.skill_id.hex if hasattr(skill.skill_id, 'hex') else str(skill.skill_id),
        "status": skill.status,
        "sujet_cle": skill.subject_key,
        "contexte_erreur": skill.error_context or "",
        "directive_corrective": skill.directive_text,
        "mots_cles": skill.keywords_json or [],
        "created_at": skill.created_at.isoformat() if skill.created_at else "",
        "approved_at": skill.approved_at.isoformat() if skill.approved_at else None,
        "sha256_hash": skill.sha256_hash or "",
    }


# =============================================================================
# FALLBACK JSON
# =============================================================================

def _charger_json(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(SKILLS_FILE):
        return []
    try:
        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            all_skills = json.load(f)
        if status_filter:
            return [s for s in all_skills if s.get("status", SkillStatus.APPROVED) == status_filter]
        return all_skills
    except Exception as e:
        print(f"[SkillStore] ⚠️ Erreur lecture JSON : {e}")
        return []


def _sauvegarder_json(skills: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(SKILLS_FILE), exist_ok=True)
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)


# =============================================================================
# API PUBLIQUE (interface inchangée pour les appelants)
# =============================================================================

def charger_tous_les_skills(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Charge les skills depuis PostgreSQL (ou JSON en fallback).
    """
    repo = _get_skill_repo()
    if repo is not None:
        try:
            org_id = _get_default_org_id()
            if org_id is None:
                return _charger_json(status_filter)

            if status_filter == SkillStatus.PENDING:
                skills = repo.get_pending(org_id)
            elif status_filter == SkillStatus.APPROVED:
                skills = repo.get_approved(org_id)
            else:
                skills = repo.list_all(org_id, limit=1000)

            return [_skill_to_dict(s) for s in skills]
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur PostgreSQL, fallback JSON : {e}")

    return _charger_json(status_filter)


def sauvegarder_liste_skills(skills: List[Dict[str, Any]]) -> None:
    """Écriture miroir : PostgreSQL + JSON."""
    repo = _get_skill_repo()
    if repo is not None:
        try:
            org_id = _get_default_org_id()
            if org_id is not None:
                for s in skills:
                    if s.get("status") == SkillStatus.APPROVED:
                        repo.approve(uuid.UUID(s["id"]), _get_admin_user_id())
                    elif s.get("status") == SkillStatus.REJECTED:
                        repo.reject(uuid.UUID(s["id"]), _get_admin_user_id(), s.get("rejection_reason", ""))
                repo.db.commit()
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur sauvegarde PostgreSQL : {e}")

    _sauvegarder_json(skills)


def ajouter_skill_pending(skill_data: Dict[str, Any]) -> str:
    """
    Enregistre un nouveau skill distillé avec le statut PENDING_APPROVAL.
    Retourne le skill_id généré.
    """
    repo = _get_skill_repo()
    if repo is not None:
        try:
            org_id = _get_default_org_id()
            if org_id is not None:
                skill = repo.create_pending(
                    org_id=org_id,
                    subject_key=skill_data.get("sujet_cle", "Skill Sans Nom"),
                    directive_text=skill_data.get("directive_corrective", ""),
                    error_context=skill_data.get("contexte_erreur", ""),
                    keywords=skill_data.get("mots_cles", []),
                )
                repo.db.commit()
                skill_id = str(skill.skill_id)
                print(f"[SkillStore] ⏳ Nouveau skill soumis à modération HITL (ID: '{skill_id}') pour : '{skill.subject_key}'")
                return skill_id
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur PostgreSQL, fallback JSON : {e}")

    # Fallback JSON
    skill_id = f"sk_{uuid.uuid4().hex[:8]}"
    skill_entry = {
        "id": skill_id,
        "status": SkillStatus.PENDING,
        "created_at": datetime.datetime.now().isoformat(),
        "sujet_cle": skill_data.get("sujet_cle", "Skill Sans Nom"),
        "contexte_erreur": skill_data.get("contexte_erreur", ""),
        "directive_corrective": skill_data.get("directive_corrective", ""),
        "mots_cles": skill_data.get("mots_cles", []),
    }
    all_skills = _charger_json()
    all_skills.append(skill_entry)
    _sauvegarder_json(all_skills)
    print(f"[SkillStore] ⏳ Nouveau skill soumis à modération HITL (ID: '{skill_id}') pour : '{skill_entry['sujet_cle']}'")
    return skill_id


def approuver_skill(skill_id: str) -> bool:
    """Approuve un skill en attente."""
    repo = _get_skill_repo()
    if repo is not None:
        try:
            skill_uuid = uuid.UUID(skill_id)
            skill = repo.approve(skill_uuid, _get_admin_user_id())
            if skill:
                repo.db.commit()
                print(f"[SkillStore] ✅ Skill '{skill_id}' APPROUVÉ et activé dans la mémoire active !")
                return True
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur approbation PostgreSQL : {e}")

    # Fallback JSON
    all_skills = _charger_json()
    found = False
    for skill in all_skills:
        if skill.get("id") == skill_id:
            skill["status"] = SkillStatus.APPROVED
            skill["approved_at"] = datetime.datetime.now().isoformat()
            found = True
            print(f"[SkillStore] ✅ Skill '{skill_id}' APPROUVÉ (fallback JSON) !")
            break
    if found:
        _sauvegarder_json(all_skills)
    return found


def rejeter_skill(skill_id: str) -> bool:
    """Rejette un skill en attente."""
    repo = _get_skill_repo()
    if repo is not None:
        try:
            skill_uuid = uuid.UUID(skill_id)
            skill = repo.reject(skill_uuid, _get_admin_user_id())
            if skill:
                repo.db.commit()
                print(f"[SkillStore] ❌ Skill '{skill_id}' REJETÉ.")
                return True
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur rejet PostgreSQL : {e}")

    # Fallback JSON
    all_skills = _charger_json()
    found = False
    for skill in all_skills:
        if skill.get("id") == skill_id:
            skill["status"] = SkillStatus.REJECTED
            skill["rejected_at"] = datetime.datetime.now().isoformat()
            found = True
            print(f"[SkillStore] ❌ Skill '{skill_id}' REJETÉ (fallback JSON).")
            break
    if found:
        _sauvegarder_json(all_skills)
    return found


def lister_skills_pending() -> List[Dict[str, Any]]:
    """Retourne la liste des skills en attente de modération HITL."""
    return charger_tous_les_skills(status_filter=SkillStatus.PENDING)


def rechercher_skills_pertinents(query: str) -> List[Dict[str, Any]]:
    """
    Recherche les skills pertinents par full-text search PostgreSQL
    ou fallback mots-clés sur JSON.
    """
    repo = _get_skill_repo()
    if repo is not None:
        try:
            org_id = _get_default_org_id()
            if org_id is not None:
                skills = repo.search_by_keywords(org_id, query)
                return [_skill_to_dict(s) for s in skills]
        except Exception as e:
            print(f"[SkillStore] ⚠️ Erreur recherche PostgreSQL, fallback JSON : {e}")

    # Fallback : recherche par mots-clés dans le JSON
    approved_skills = _charger_json(status_filter=SkillStatus.APPROVED)
    if not approved_skills:
        return []

    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    stopwords = {"les", "des", "pour", "dans", "une", "avec", "sur", "par", "qui", "que", "est", "comment", "quel", "quelle"}
    meaningful_words = {w for w in query_words if len(w) > 2 and w not in stopwords}

    relevant_skills = []
    for skill in approved_skills:
        sujet_cle = skill.get("sujet_cle", "").lower()
        mots_cles = [m.lower() for m in skill.get("mots_cles", [])]
        match_sujet = any(w in sujet_cle for w in meaningful_words)
        match_mots_cles = any(w in " ".join(mots_cles) for w in meaningful_words)
        if match_sujet or match_mots_cles:
            relevant_skills.append(skill)

    return relevant_skills


def nettoyer_et_dedoublonner_skills() -> Dict[str, Any]:
    """
    Agent Nettoyeur local : Scanne la base de skills approuvés, fusionne les doublons
    et élimine les directives contradictoires.
    Utilise TF-IDF + similarité cosinus (scikit-learn) — 100% gratuit, zéro API.
    """
    print("[SkillStore Nettoyeur] 🧹 Analyse et dédoublonnage de la mémoire sémantique...")
    all_skills = charger_tous_les_skills()
    approved_skills = [s for s in all_skills if s.get("status", SkillStatus.APPROVED) == SkillStatus.APPROVED]

    if len(approved_skills) <= 1:
        print("[SkillStore Nettoyeur] ℹ️ Moins de 2 skills approuvés. Dédoublonnage ignoré.")
        return {"status": "skipped", "message": "Nombre de skills insuffisant pour le dédoublonnage.", "count": len(approved_skills)}

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        HAS_SKLEARN = True
    except ImportError:
        HAS_SKLEARN = False
        print("[SkillStore Nettoyeur] ℹ️ scikit-learn non installé. Utilisation du fallback mots-clés.")

    merged_indices = set()
    cleaned_skills = []
    n = len(approved_skills)

    if HAS_SKLEARN:
        texts = [f"{s.get('sujet_cle', '')} {s.get('directive_corrective', '')}" for s in approved_skills]
        vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=500, stop_words="french")
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        SIMILARITY_THRESHOLD = 0.75

        for i in range(n):
            if i in merged_indices:
                continue
            current = approved_skills[i]
            duplicates = [current]
            for j in range(i + 1, n):
                if j in merged_indices:
                    continue
                if similarity_matrix[i][j] >= SIMILARITY_THRESHOLD:
                    duplicates.append(approved_skills[j])
                    merged_indices.add(j)
            if len(duplicates) > 1:
                best = max(duplicates, key=lambda x: len(x.get("directive_corrective", "")))
                all_keywords = []
                for d in duplicates:
                    all_keywords.extend(d.get("mots_cles", []))
                seen = set()
                merged_keywords = []
                for kw in all_keywords:
                    if kw.lower() not in seen:
                        seen.add(kw.lower())
                        merged_keywords.append(kw)
                merged = {
                    "id": best.get("id", f"sk_{uuid.uuid4().hex[:8]}"),
                    "status": SkillStatus.APPROVED,
                    "sujet_cle": best.get("sujet_cle", "Fusionné"),
                    "contexte_erreur": " | ".join(sorted(set(d.get("contexte_erreur", "") for d in duplicates if d.get("contexte_erreur")))),
                    "directive_corrective": best.get("directive_corrective", ""),
                    "mots_cles": merged_keywords,
                    "last_cleaned_at": datetime.datetime.now().isoformat(),
                    "fusionne_depuis": [d.get("id") for d in duplicates],
                }
                cleaned_skills.append(merged)
                print(f"  🔗 Fusion : {', '.join(d.get('sujet_cle', '?')[:40] for d in duplicates)}")
            else:
                current["last_cleaned_at"] = datetime.datetime.now().isoformat()
                cleaned_skills.append(current)
    else:
        for i in range(n):
            if i in merged_indices:
                continue
            current = approved_skills[i]
            current_keywords = set(k.lower() for k in current.get("mots_cles", []))
            duplicates = [current]
            for j in range(i + 1, n):
                if j in merged_indices:
                    continue
                other = approved_skills[j]
                other_keywords = set(k.lower() for k in other.get("mots_cles", []))
                if current_keywords and other_keywords:
                    overlap = len(current_keywords & other_keywords)
                    min_len = min(len(current_keywords), len(other_keywords))
                    if min_len > 0 and overlap / min_len >= 0.5:
                        duplicates.append(other)
                        merged_indices.add(j)
            if len(duplicates) > 1:
                best = max(duplicates, key=lambda x: len(x.get("directive_corrective", "")))
                all_keywords = []
                seen = set()
                for d in duplicates:
                    for kw in d.get("mots_cles", []):
                        if kw.lower() not in seen:
                            seen.add(kw.lower())
                            all_keywords.append(kw)
                merged = {
                    "id": best.get("id", f"sk_{uuid.uuid4().hex[:8]}"),
                    "status": SkillStatus.APPROVED,
                    "sujet_cle": best.get("sujet_cle", "Fusionné"),
                    "contexte_erreur": " | ".join(sorted(set(d.get("contexte_erreur", "") for d in duplicates if d.get("contexte_erreur")))),
                    "directive_corrective": best.get("directive_corrective", ""),
                    "mots_cles": all_keywords,
                    "last_cleaned_at": datetime.datetime.now().isoformat(),
                    "fusionne_depuis": [d.get("id") for d in duplicates],
                }
                cleaned_skills.append(merged)
                print(f"  🔗 Fusion (fallback) : {', '.join(d.get('sujet_cle', '?')[:40] for d in duplicates)}")
            else:
                current["last_cleaned_at"] = datetime.datetime.now().isoformat()
                cleaned_skills.append(current)

    other_skills = [s for s in all_skills if s.get("status") in [SkillStatus.PENDING, SkillStatus.REJECTED]]
    final_list = other_skills + cleaned_skills
    sauvegarder_liste_skills(final_list)

    print(f"[SkillStore Nettoyeur] 🎉 Nettoyage terminé ! {len(approved_skills)} ➔ {len(cleaned_skills)} skills approuvés.")
    return {
        "status": "success",
        "message": f"Dédoublonnage local terminé : {len(approved_skills)} → {len(cleaned_skills)} skills (seuil: 0.75 cosinus)",
        "skills_before": len(approved_skills),
        "skills_after": len(cleaned_skills),
    }


# =============================================================================
# HELPERS INTERNES
# =============================================================================

def _get_default_org_id() -> Optional[uuid.UUID]:
    """Récupère l'ID de l'organisation par défaut."""
    try:
        from orchestrator.database import SessionLocal
        db = SessionLocal()
        from orchestrator.models import Organization
        org = db.query(Organization).filter_by(slug="default").first()
        db.close()
        return org.org_id if org else None
    except Exception:
        return None


def _get_admin_user_id() -> uuid.UUID:
    """Récupère l'ID de l'utilisateur admin."""
    try:
        from orchestrator.database import SessionLocal
        db = SessionLocal()
        from orchestrator.models import User
        user = db.query(User).filter_by(email="admin@morph.local").first()
        db.close()
        return user.user_id if user else uuid.UUID(int=0)
    except Exception:
        return uuid.UUID(int=0)
