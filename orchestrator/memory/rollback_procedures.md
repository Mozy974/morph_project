# 🔄 Procédures de Rollback d'Urgence — SuperAgent Morph

Ce guide documente les étapes pas à pas pour réverser un déploiement ou restaurer l'état précédent du système en cas d'anomalie critique en production.

---

## 1. Rollback du Code Frontend & Streamlit Community Cloud

### Option A : Annulation Git du dernier commit
```bash
# Rétablir le commit précédent sur la branche main
git reset --hard HEAD~1
git push --force origin main
```
*Streamlit Community Cloud détectera la force push et redéploiera instantanément la révision précédente.*

### Option B : Déploiement d'un tag de version stable
```bash
git checkout v13.0-stable
git push --force origin main
```

---

## 2. Rollback des Checkpoints Redis & De l'Orchestrateur

En cas d'échec d'une mise à jour de schéma d'état :
```bash
# Reprise forcée d'un job sur son dernier checkpoint sain
POST /resume_task/{job_id}?force_previous_checkpoint=true
```

---

## 3. Rollback de la Base Vectorielle RAG (ChromaDB)

En cas de corruption d'embeddings :
```python
import chromadb
client = chromadb.Client()
client.delete_collection("base_personnelle")
# Ré-indexation propre
```

---

## 4. Matrice de Décision Rollback vs Hotfix

| Symptôme | Gravité | Décision Recommandée |
| :--- | :---: | :--- |
| **Baisse du Cache Hit Ratio < 50%** | Majeure | Nettoyage cache L1 (`lru_cache.clear()`) |
| **Échec Invariant Sécurité** | Bloquante | **ROLLBACK IMMÉDIAT (Git reset)** |
| **Timeout API Tavily** | Mineure | Automatique (Fallback RAG local) |
