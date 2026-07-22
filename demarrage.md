---

## 💡 Guide : Comment rédiger un bon "Premier Prompt"

Pour que l'orchestrateur (et surtout les sous-agents WarpGrep et Fast Apply) fonctionne de manière optimale, votre instruction initiale doit être claire, orientée sur l'action, et facile à lier à un mot-clé technique.

### La structure idéale
Un bon prompt pour Morph répond à deux questions : **Quoi faire ?** et **Où le faire ?**

### Exemples de requêtes performantes

**Exemple 1 : Ajout de logique (Recommandé)**
> **Vous :** *Ajoute une vérification du format de l'email avec une regex dans la fonction de création d'utilisateur.*
> **Mot-clé technique :** `email` ou `def create_user`
> **Pourquoi ça marche :** L'agent sait exactement quelle technologie utiliser (regex) et dans quel bloc de code l'insérer.

**Exemple 2 : Modification d'interface / Menu**
> **Vous :** *Ajoute une option "3. Exporter les données" dans la fonction draw_menu, qui appelle la fonction export_csv().*
> **Mot-clé technique :** `draw_menu`
> **Pourquoi ça marche :** Le mot-clé est extrêmement précis, WarpGrep trouvera le fichier instantanément.

**Exemple 3 : Refactoring ou Sécurité**
> **Vous :** *Modifie la fonction de connexion à la DB pour qu'elle lève une erreur si le mot de passe est vide.*
> **Mot-clé technique :** `connect_db` ou `password`

### ❌ Ce qu'il faut éviter (Les mauvais prompts)

- **Trop vague :** *"Améliore la sécurité du fichier."* (L'IA ne saura pas quoi modifier exactement et risque de réécrire des choses inattendues).
- **Trop large :** *"Refais tout le système d'authentification."* (Fast Apply est un outil d'édition chirurgicale, pas de réécriture complète. Procédez par petites étapes).
- **Mot-clé mal choisi :** Utiliser `import` ou `return` comme mot-clé technique va renvoyer beaucoup trop de résultats depuis WarpGrep, ce qui noiera l'agent. Préférez le nom exact de la fonction ou de la variable cible.