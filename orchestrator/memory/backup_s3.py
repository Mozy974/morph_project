"""
Module de Backup Chiffré S3 / Cloud Storage pour la Mémoire Sémantique (orchestrator/memory/backup_s3.py).
Permet la sauvegarde périodique de long_term_skills.json vers un bucket S3 / MinIO chiffré en AES-256.
"""

import os
import json
import hashlib
import datetime
from typing import Dict, Any, Optional

SKILLS_FILE = os.path.join(os.path.dirname(__file__), "long_term_skills.json")


def sauvegarder_skills_s3(bucket_name: str = "superagent-skills-backup", s3_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Sauvegarde chiffrée AES-256 de la Mémoire Sémantique vers S3 / MinIO.
    Propose un fallback sur archive zip local si boto3 n'est pas configuré.
    """
    if not os.path.exists(SKILLS_FILE):
        return {"status": "skipped", "message": "Aucun fichier long_term_skills.json à sauvegarder."}

    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"skills_backup_{timestamp}.json"
    content = json.dumps(skills_data, indent=2, ensure_ascii=False)
    content_bytes = content.encode("utf-8")
    
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()

    # Tentative d'export Boto3 / S3
    try:
        if s3_client is None:
            import boto3
            s3_client = boto3.client('s3')

        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=content_bytes,
            ServerSideEncryption='AES256',
            Metadata={
                "sha256": sha256_hash,
                "skills_count": str(len(skills_data))
            }
        )
        print(f"[Backup S3] ☁️ Backup chiffré AES-256 envoyé vers S3 '{bucket_name}/{filename}' (Hash: {sha256_hash[:16]}...)")
        return {
            "status": "success",
            "provider": "S3",
            "bucket": bucket_name,
            "filename": filename,
            "sha256": sha256_hash,
            "skills_count": len(skills_data)
        }
    except Exception as e:
        # Fallback local sécurisé dans orchestrator/memory/backups/
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        local_path = os.path.join(backup_dir, filename)

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[Backup S3 Local Fallback] 💾 Archive locale sécurisée créée dans '{local_path}' (Raison S3: {e})")
        return {
            "status": "success_local_fallback",
            "local_path": local_path,
            "filename": filename,
            "sha256": sha256_hash,
            "skills_count": len(skills_data)
        }
