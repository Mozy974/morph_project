# 🛠️ Scripts SRE & PRA — Morph Project

Ce répertoire regroupe les scripts d'automatisation pour l'exploitation SRE, la résolution d'incidents et la gestion des sauvegardes d'archivage RGPD.

---

## 📋 Table des Scripts

### 1. `clean_purge_lock.sh`
Déblocage sécurisé du verrou d'exclusivité du classifieur d'intentions (`IntentSentimentClassifier`).

**Usage** :
```bash
./scripts/clean_purge_lock.sh
```

---

### 2. `restore_rgpd_archives.sh`
Inspection et vérification de l'intégrité des archives JSON d'audit RGPD.

**Usage** :
```bash
./scripts/restore_rgpd_archives.sh /var/lib/rgpd_backups
```

---

## 🎯 Intégration CI/CD & Production

- **Validation Pytest** : Les scripts sont validés automatiquement lors des pipelines d'intégration continue.
- **Monitoring & SRE** : À utiliser conjointement avec le [Runbook SRE](file:///home/mozy/Bureau/morph_project/orchestrator/memory/sre_runbook_rgpd.md).
