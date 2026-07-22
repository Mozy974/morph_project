# 🛡️ Runbook Général de Disaster Recovery (PRA) — SuperAgent Morph

Ce guide synthétise l'ensemble des procédures d'urgence et de restauration après sinistre pour l'infrastructure multi-agents SuperAgent Morph.

---

## 1. Matrice des Sinistres & Temps d'Intervention (RTO / RPO)

| Incident | RTO (Temps de Restauration) | RPO (Perte de Données Max) | Procédure de Récupération |
| :--- | :---: | :---: | :--- |
| **Crash Pod Streamlit Cloud** | < 1 min | 0s | Redéploiement automatique via Git Push / Webhook |
| **Deadlock Purge RGPD** | < 2 min | 0s | Exécution `./scripts/clean_purge_lock.sh` |
| **Panne Cluster Loki / Logs** | < 5 min | < 1h | Restauration depuis `/var/lib/rgpd_backups/` |
| **Erreur Invariant Sécurité** | Immédiat (0s) | 0s | Blocage unilatéral automatique & Rollback Git |

---

## 2. Procédures de Restauration des Agents & RAG

```bash
# 1. Vérification de l'intégrité de la suite Pytest (56 tests)
PYTHONPATH=. pytest tests/

# 2. Ré-indexation forcée du vector store ChromaDB
python -c "import streamlit as st; st.cache_resource.clear()"

# 3. Synchronisation des sauvegardes S3
python scripts/backup_loki_to_s3.py
```
