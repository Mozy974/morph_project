import json
from typing import Optional

from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_ECLAIREUR
from orchestrator.search import search_web
from orchestrator.memory.skill_store import rechercher_skills_pertinents


class AgentEclaireur:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.nom = "Éclaireur Alpha"

    def analyser_sujet(self, sujet: str, feedback: Optional[str] = None) -> dict:
        """
        Analyse un sujet en profondeur via recherche Web Tavily + API Mistral.
        Interroge d'abord la Mémoire Sémantique Long Terme (Skill Store) pour appliquer
        immédiatement toute règle corrective apprise lors de runs précédents.

        Args:
            sujet: Le sujet initial.
            feedback: La consigne de correction de l'Analyste (si itération en cours).

        Returns:
            Rapport structuré incluant les sources Web réelles.
        """
        # 0. Interrogation de la Mémoire Sémantique Long Terme (Skill Store)
        skills_appris = rechercher_skills_pertinents(sujet)
        directives_memoire = []
        if skills_appris:
            print(f"[{self.nom}] 🧠 {len(skills_appris)} directive(s) sémantique(s) trouvée(s) dans la Mémoire Long Terme !")
            for s in skills_appris:
                directives_memoire.append(f"📌 [Règle apprise : {s.get('sujet_cle')}] : {s.get('directive_corrective')}")

        if feedback:
            print(f"[{self.nom}] 🔄 BOUCLE DE RÉTROACTION ACTIVÉE ! Consigne : '{feedback[:100]}...'")
            search_query = f"{sujet} {feedback}"[:150]
        else:
            print(f"[{self.nom}] Début de l'analyse pour le sujet : '{sujet}'...")
            search_query = sujet

        # 1. Recherche Web en temps réel via Tavily
        web_search = search_web(search_query, max_results=5)
        web_context = ""
        sources_web = []

        if web_search["success"] and web_search["results"]:
            print(f"[{self.nom}] 🌐 {len(web_search['results'])} résultats Web récupérés via Tavily !")
            context_blocks = []
            for item in web_search["results"]:
                context_blocks.append(f"- [{item['title']}]({item['url']})\n  {item['content']}")
                sources_web.append({"title": item["title"], "url": item["url"]})
            web_context = "RÉSULTATS DE RECHERCHE WEB EN TEMPS RÉEL :\n" + "\n\n".join(context_blocks)
        else:
            if web_search.get("error"):
                print(f"[{self.nom}] ⚠️ Recherche Web ignorée ({web_search['error']}). Mode LLM pur.")
            else:
                print(f"[{self.nom}] ℹ️ Aucun résultat Web trouvé. Mode LLM pur.")

        system_prompt = """Tu es un agent de recherche et d'analyse expert. 
Ta mission est d'analyser un sujet donné et de produire un rapport structuré basé sur les recherches fournies.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après.
Le JSON doit avoir exactement cette structure :
{
    "sujet_analyse": "le sujet analysé",
    "points_cles": ["point 1", "point 2", "point 3"],
    "fiabilite": "un pourcentage estimé (ex: 90%)",
    "recommandation": "une recommandation courte et actionnable",
    "sources_web": [{"title": "titre", "url": "url"}]
}

RÈGLES :
- Identifie 3 à 5 points clés pertinents et approfondis sur le sujet.
- Si des RÈGLES MÉTIER APPRISES sont transmises, applique-les OBLIGATOIREMENT pour couvrir dès à présent tous les éléments d'exigence.
- Si une consigne de feedback/correction est fournie, concentre-toi spécifiquement sur la résolution des manques indiqués.
- Appuie-toi sur les recherches Web fournies pour donner des détails concrets, chiffrés et factuels.
- Estime la fiabilité globale.
- Remplis "sources_web" avec la liste des sources Web pertinentes utilisées.
- Sois factuel, précis et rigoureux."""

        user_prompt = f"Sujet à analyser : {sujet}\n\n"
        
        if directives_memoire:
            user_prompt += "🧠 DIRECTIVES CORRECTIVES APPRISES DE LA MÉMOIRE LONG TERME :\n" + "\n".join(directives_memoire) + "\n\n"

        if feedback:
            user_prompt += f"CRITIQUE / CONSIGNE D'APPROFONDISSEMENT DE L'ANALYSTE EN COURS :\n{feedback}\n\n"
        
        if web_context:
            user_prompt += web_context

        try:
            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ECLAIREUR,
                json_mode=True,
            )

            rapport = json.loads(raw_response)

            # Sécurité : s'assurer que sources_web est présent
            if "sources_web" not in rapport or not rapport["sources_web"]:
                rapport["sources_web"] = sources_web

            print(f"[{self.nom}] Analyse terminée avec succès !")
            return rapport

        except json.JSONDecodeError:
            print(f"[{self.nom}] ⚠️ Réponse non-JSON reçue, construction d'un rapport de secours.")
            return {
                "sujet_analyse": sujet,
                "points_cles": [raw_response[:500]],
                "fiabilite": "N/A (réponse non structurée)",
                "recommandation": "Relancer l'analyse avec un sujet plus précis",
                "sources_web": sources_web,
            }
        except RuntimeError as e:
            print(f"[{self.nom}] ❌ Erreur API : {e}")
            return {
                "sujet_analyse": sujet,
                "points_cles": [f"Erreur lors de l'analyse : {str(e)}"],
                "fiabilite": "0%",
                "recommandation": "Vérifier la clé API et la connexion réseau",
                "sources_web": sources_web,
            }
