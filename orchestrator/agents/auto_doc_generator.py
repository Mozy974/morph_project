"""
AutoDocGeneratorAgent : Agent d'Auto-Documentation (Niveau 7.0 Meta-Learning).
Inspecte la base de code et génère automatiquement la documentation technique et les diagrammes Mermaid.
"""

import json
import os
import ast
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_REDACTEUR


class AutoDocGeneratorAgent:
    """
    Agent d'Auto-Documentation (Niveau 7.0).
    Analyse le code source Python (AST) et génère des guides techniques Markdown et schémas Mermaid.
    """

    def __init__(self):
        self.nom = "Auto-Doc Generator"

    def inspect_module_ast(self, code: str) -> Dict[str, Any]:
        """Extrait la structure AST d'un fichier Python (classes, fonctions, docstrings)."""
        summary = {"classes": [], "functions": [], "imports": []}
        try:
            tree = ast.parse(code)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    summary["classes"].append({"name": node.name, "methods": methods, "docstring": ast.get_docstring(node) or ""})
                elif isinstance(node, ast.FunctionDef):
                    summary["functions"].append({"name": node.name, "docstring": ast.get_docstring(node) or ""})
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        summary["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    summary["imports"].append(node.module or "")
        except Exception as e:
            print(f"[{self.nom}] ⚠️ AST Parsing warning: {e}")

        return summary

    def generate_documentation(self, module_name: str, code: str) -> Dict[str, str]:
        """
        Génère une documentation complète au format Markdown avec diagramme Mermaid.
        """
        print(f"[{self.nom}] 📖 Génération automatique de la documentation pour '{module_name}'...")
        ast_info = self.inspect_module_ast(code)

        system_prompt = """Tu es un expert en Rédaction de Documentation Technique et Diagrammes Mermaid.
Ta mission est de générer un guide technique clair, concis et visuel pour le module Python fourni.

STRUCTURE ATTENDUE :
1. Titre & Résumé du Module
2. Diagramme d'Architecture Mermaid (`mermaid ...`)
3. Description des Classes & Méthodes Clés
4. Exemple d'utilisation

Réponds UNIQUEMENT en Markdown de haute qualité."""

        user_prompt = f"""MODULE : {module_name}

STRUCTURE AST EXTRAITE :
{json.dumps(ast_info, ensure_ascii=False, indent=2)}

CODE SOURCE PARTIEL :
```python
{code[:2000]}
```

Génère la documentation Markdown complète."""

        doc_md = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=DEFAULT_MODEL,
            temperature=TEMP_REDACTEUR
        )

        return {
            "module_name": module_name,
            "documentation_md": doc_md,
            "ast_summary": ast_info
        }
