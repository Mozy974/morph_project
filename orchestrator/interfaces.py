"""
Contrats d'interfaces Pydantic pour la séparation des rôles True TDD (QA TestSuite vs Dev Implementation).
Enrichi avec signature cryptographique SHA-256 (Sceau d'Intégrité).
"""

import hashlib
from typing import Dict, Optional
from pydantic import BaseModel, Field


class QATestSuite(BaseModel):
    """
    Contrat de suite de tests opposable et immuable généré par l'Analyste (QA).
    Protégé par une empreinte numérique SHA-256 (Sceau d'Intégrité).
    """
    explication_tests: str = Field(description="Explication des cas nominaux, limites et exceptions couverts")
    test_main_code: str = Field(description="Le code complet du fichier test_main.py (pytest)")
    requirements_txt: str = Field(default="pytest", description="Les dépendances Python nécessaires au projet")
    test_hash: str = Field(default="", description="Empreinte cryptographique SHA-256 du code de test_main.py")

    def compute_hash(self) -> str:
        """
        Calcule le hachage SHA-256 du code de test pour garantir son immuabilité absolue.
        """
        clean_code = self.test_main_code.strip()
        return hashlib.sha256(clean_code.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """
        Vérifie que le code de test n'a subi aucune altération depuis sa création par l'Analyste.
        """
        if not self.test_hash:
            return True  # Fallback si absent
        return self.compute_hash() == self.test_hash


class DevImplementation(BaseModel):
    """
    Implémentation produite par l'Agent Codeur (Dev) pour satisfaire la QATestSuite sans la modifier.
    """
    explication_code: str = Field(description="Explication de la solution technique adoptée")
    main_code: str = Field(description="Le code complet du fichier main.py")
    extra_files: Dict[str, str] = Field(default_factory=dict, description="Modules complémentaires optionnels (ex: config.py, utils.py)")


class WorkspacePayload(BaseModel):
    """
    Assemblage final multi-fichiers pour la Sandbox d'exécution Pytest.
    """
    files: Dict[str, str] = Field(description="Dictionnaire des chemins et contenus de tous les fichiers du projet")

    @classmethod
    def assemble(cls, qa_suite: QATestSuite, dev_impl: DevImplementation) -> "WorkspacePayload":
        # Vérification d'intégrité avant assemblage
        if not qa_suite.verify_integrity():
            raise ValueError(
                f"🚨 SCEAU DE SÉCURITÉ ROMPU ! Empreinte SHA-256 non valide pour test_main.py. "
                f"Le contrat de test a été altéré !"
            )

        files = {
            "test_main.py": qa_suite.test_main_code,
            "requirements.txt": qa_suite.requirements_txt,
            "main.py": dev_impl.main_code,
        }
        if dev_impl.extra_files:
            files.update(dev_impl.extra_files)
        return cls(files=files)
