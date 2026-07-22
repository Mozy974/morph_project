# 🔌 Spécification Technique — Extension VS Code Morph SuperAgent (Q2 2024)

## 1. Présentation & Objectifs

L'extension VS Code pour **Morph / SuperAgent Enterprise** permet aux développeurs d'exécuter, superviser et valider des tâches d'ingénierie autonome directement depuis leur environnement de développement.

---

## 2. Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│ 💻 Extension VS Code (TypeScript / Extension API)          │
│ ├── 📌 Activity Bar Sidebar (Panneau de contrôle)          │
│ ├── 🌐 Webview SSE Dashboard (Flux d'événements live)        │
│ └── ⚡ Code Action Provider (Fix & TDD Quick-Fixes)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST & SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Backend FastAPI Orchestrator (http://localhost:8000)     │
│ ├── POST /run_graph, /resume_task/{job_id}                  │
│ ├── GET /stream/{job_id} (Server-Sent Events)                │
│ └── POST /skills/approve/{id}, /skills/reject/{id}         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Fonctionnalités Clés

### A. Panneau Lateral Activity Bar (`Morph Dashboard`)
- **Lancement de Tâche** : Champ d'instruction avec sélection de la stratégie (True TDD, Self-Healing Auto-Fix, Refactoring).
- **Monitoring Temps Réel** : Visualisation du graphe des agents (Éclaireur ➔ Analyste ➔ Codeur ➔ Redacteur) via SSE.
- **Human-in-the-Loop (HITL)** : Notification toast dès qu'une compétence/skill est en attente d'approbation (`PENDING_APPROVAL`), avec boutons *Approuver* ou *Rejeter* en 1-click.

### B. Commandes VS Code (`package.json`)
- `morph.startTask` : Démarrer un nouveau job à partir de la sélection de code active.
- `morph.autoFix` : Déclencher le protocole de Self-Healing sur les erreurs de diagnostic du workspace.
- `morph.openDashboard` : Ouvrir le tableau de bord Webview intégré.
- `morph.cleanSkills` : Déclencher la déduplication IA de la mémoire long terme (`POST /skills/clean`).

### C. Intégration Diagnostics & Quick-Fix (CodeActionProvider)
- Lorsqu'une erreur Pytest/Linter est présente sur une ligne, une ampoule `⚡ Fix avec Morph SuperAgent` apparaît.
- Le clic envoie l'extrait de code défaillant et la trace d'erreur à l'API `/run_graph`.

---

## 4. Endpoints API Utilisés

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/run_graph` | `POST` | Démarre un nouveau job d'ingénierie autonome |
| `/stream/{job_id}` | `GET` | Flux SSE temps réel des étapes et événements d'agents |
| `/skills/pending` | `GET` | Récupère la liste des compétences en attente de modération |
| `/skills/approve/{id}` | `POST` | Valide une compétence par le superviseur humain |
| `/skills/clean` | `POST` | Exécute la déduplication IA de la mémoire |
| `/metrics` | `GET` | Récupère les métriques Prometheus du système |

---

## 5. Structure du Projet Extension

```
vscode-extension/
├── src/
│   ├── extension.ts             # Entry point, enregistrement des commandes
│   ├── client/
│   │   └── api_client.ts        # Interface HTTP REST & SSE EventSource
│   ├── providers/
│   │   ├── code_action.ts       # Diagnostic Quick-Fix Provider
│   │   └── sidebar_provider.ts  # Webview View Provider
│   └── webview/
│       └── main.ts              # Dashboard frontend (Vue.js / Vanilla JS)
├── package.json                 # Manifeste VS Code (contributions, commands)
└── tsconfig.json
```
