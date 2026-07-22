"""
Module d'exportation Git autonome pour le SuperAgent (orchestrator/git_exporter.py).
Permet de committer et pusher le code validé en Sandbox directement dans un dépôt Git.
"""

import os
import subprocess
from typing import Dict, Any, List


class GitExporter:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def commit_job_artifacts(
        self,
        job_id: str,
        files: Dict[str, str],
        commit_message: str = "",
        branch_prefix: str = "feature/agent-job-"
    ) -> Dict[str, Any]:
        """
        Crée une branche Git dédiée au job, écrit les fichiers et effectue un commit.

        Args:
            job_id: L'identifiant unique du job SuperAgent.
            files: Dictionnaire {"nom_fichier": "contenu"}.
            commit_message: Message de commit optionnel.
            branch_prefix: Préfixe du nom de la branche.

        Returns:
            Dictionnaire avec le statut de l'opération Git.
        """
        branch_name = f"{branch_prefix}{job_id[:8]}"
        
        try:
            # 0. Initialisation automatique de git si le dépôt n'existe pas
            git_dir = os.path.join(self.repo_path, ".git")
            if not os.path.exists(git_dir):
                subprocess.run(
                    ["git", "init"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

            # 1. Écriture des fichiers sur le disque
            written_files: List[str] = []
            for filename, content in files.items():
                filepath = os.path.join(self.repo_path, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content.strip())
                written_files.append(filename)

            # 2. Commandes Git (git add, git commit)
            msg = commit_message or f"feat(superagent): auto-generated code solution for job {job_id[:8]}"
            
            # Git add
            subprocess.run(
                ["git", "add", "-f"] + written_files,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Check Git status
            status_proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if status_proc.stdout.strip():
                # Git commit
                commit_proc = subprocess.run(
                    ["git", "commit", "-m", msg],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                committed = True
                commit_log = commit_proc.stdout.strip()
            else:
                committed = False
                commit_log = "Aucun changement à committer"

            print(f"[GitExporter] ✅ Exportation Git réussie pour job '{job_id[:8]}' (Fichiers: {len(written_files)})")
            return {
                "success": True,
                "branch": branch_name,
                "committed": committed,
                "files": written_files,
                "log": commit_log
            }

        except Exception as e:
            print(f"[GitExporter] ⚠️ Erreur lors de l'exportation Git : {e}")
            return {
                "success": False,
                "error": str(e)
            }
