import json
import datetime

from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_REDACTEUR


class AgentRedacteur:
    def __init__(self):
        self.nom = "Rédacteur Gamma"

    def rediger_rapport(self, verdict: dict, code_results: dict = None) -> dict:
        """
        Rédige un rapport final structuré en Markdown à partir du verdict de l'Analyste et du Codeur.
        """
        print(f"[{self.nom}] Réception du verdict. Rédaction du rapport final...")

        sujet = verdict.get("sujet_etudie", "Sujet inconnu")
        rapport_eclaireur = verdict.get("rapport_eclaireur", {})
        conclusion = verdict.get("conclusion_analyste", {})
        sources_web = rapport_eclaireur.get("sources_web", [])

        system_prompt = """Tu es un rédacteur professionnel. Tu reçois les résultats d'une analyse réalisée par des agents IA (Éclaireur, Analyste, Codeur) et tu dois produire un rapport final élégant en Markdown.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après.
Le JSON doit avoir exactement cette structure :
{
    "titre": "Un titre accrocheur et professionnel pour le rapport",
    "rapport_markdown": "Le contenu complet du rapport en Markdown"
}

RÈGLES POUR LE RAPPORT MARKDOWN :
- Commence par un titre principal (# Titre)
- Ajoute un résumé exécutif de 3-4 lignes (## 📌 Résumé Exécutif)
- Liste les points clés reformulés clairement (## 🔑 Points Clés)
- Si du code a été généré et validé en Sandbox, inclus une section (## 💻 Code Source Validé) avec le bloc ```python et le résultat d'exécution stdout.
- Inclus la décision de l'Analyste avec son score et commentaire (## 📊 Évaluation par l'Analyste)
- Termine par des recommandations concrètes (## 🚀 Recommandations)
- Si des sources Web sont fournies, inclus une section (## 🌐 Sources Web Consultées)
- Utilise des emojis pour rendre le rapport vivant
- Sois professionnel mais accessible
- Le rapport doit être autonome"""

        sources_str = ""
        if sources_web:
            sources_list = [f"- [{src.get('title', 'Lien')}]({src.get('url', '#')})" for src in sources_web if src.get("url")]
            if sources_list:
                sources_str = "\n".join(sources_list)

        code_str = ""
        if code_results and code_results.get("code"):
            code = code_results.get("code")
            sandbox = code_results.get("sandbox_results", {})
            attempts = code_results.get("attempts_count", 1)
            stdout = sandbox.get("stdout", "Aucune sortie stdout")
            code_str = f"CODE VALIDE (Tentatives: {attempts}, Exit Code: {sandbox.get('exit_code', 0)}) :\n```python\n{code}\n```\n\nSORTIE STDOUT EN SANDBOX :\n```\n{stdout}\n```"

        sources_context = f"Sources Web disponibles :\n{sources_str}" if sources_str else "Aucune source web externe"
        code_context = f"CODE ÉCRIT ET VALIDÉ EN SANDBOX :\n{code_str}" if code_str else ""

        user_prompt = f"""Voici les données à transformer en rapport final :

SUJET : {sujet}

RAPPORT DE L'ÉCLAIREUR :
- Points clés : {json.dumps(rapport_eclaireur.get('points_cles', []), ensure_ascii=False)}
- Fiabilité estimée : {rapport_eclaireur.get('fiabilite', 'N/A')}
- {sources_context}

CONCLUSION DE L'ANALYSTE :
- Décision : {conclusion.get('decision', 'N/A')}
- Score de confiance : {conclusion.get('score_confiance', 'N/A')}/100
- Commentaire : {conclusion.get('commentaire', 'N/A')}

{code_context}"""

        try:
            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_REDACTEUR,
                json_mode=True,
            )

            resultat = json.loads(raw_response)

            # Garantie post-traitement : si des sources web existent et ne sont pas dans le markdown, les ajouter à la fin
            markdown_content = resultat.get("rapport_markdown", "")
            if sources_str and "Sources Web" not in markdown_content and "[http" not in markdown_content:
                markdown_content += f"\n\n---\n\n## 🌐 Sources Web Consultées\n{sources_str}\n"
                resultat["rapport_markdown"] = markdown_content

            # Ajout des métadonnées
            resultat["metadata"] = {
                "sujet": sujet,
                "decision_analyste": conclusion.get("decision", "N/A"),
                "score_confiance": conclusion.get("score_confiance", 0),
                "sources_nombre": len(sources_web),
                "code_genere": bool(code_results and code_results.get("code")),
                "date_generation": datetime.datetime.now().isoformat(),
                "pipeline": "Éclaireur (Tavily Web) → Analyste → Codeur (Sandbox) → Rédacteur",
            }

            print(f"[{self.nom}] Rapport final rédigé avec succès !")
            return resultat

        except json.JSONDecodeError:
            print(f"[{self.nom}] ⚠️ Réponse non-JSON, construction d'un rapport de secours.")
            return {
                "titre": f"Rapport : {sujet}",
                "rapport_markdown": f"# Rapport : {sujet}\n\n{raw_response[:2000]}",
                "metadata": {
                    "sujet": sujet,
                    "decision_analyste": conclusion.get("decision", "N/A"),
                    "score_confiance": conclusion.get("score_confiance", 0),
                    "date_generation": datetime.datetime.now().isoformat(),
                    "pipeline": "Éclaireur → Analyste → Codeur → Rédacteur",
                    "erreur": "Réponse non structurée du modèle",
                },
            }
        except RuntimeError as e:
            print(f"[{self.nom}] ❌ Erreur API : {e}")
            return {
                "titre": f"Erreur — {sujet}",
                "rapport_markdown": f"# ❌ Erreur de rédaction\n\nImpossible de générer le rapport : {str(e)}",
                "metadata": {
                    "sujet": sujet,
                    "date_generation": datetime.datetime.now().isoformat(),
                    "erreur": str(e),
                },
            }
