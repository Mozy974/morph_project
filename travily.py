from tavily import TavilyClient

# Initialisation
tavily = TavilyClient(api_key=os.environ.get("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"))

# ... (dans le bloc `if prompt := st.chat_input(...)`)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # A. Étape de décision (Le Router)
        decision_prompt = f"La question suivante nécessite-t-elle une recherche sur Internet pour être répondue ? Réponds uniquement par 'OUI' ou 'NON'. Question : {prompt}"
        decision = mistral_client.chat.complete(model="mistral-small-latest", messages=[{"role": "user", "content": decision_prompt}]).choices[0].message.content
        
        ctx = ""
        # B. Exécution selon la décision
        if "OUI" in decision.upper():
            message_placeholder.markdown("🌐 *Recherche Web activée...*")
            search_data = tavily.search(query=prompt, search_depth="basic")
            ctx = f"RÉSULTATS WEB : {search_data['results']}"
        else:
            message_placeholder.markdown("🔍 *Analyse des documents locaux...*")
            # Votre code RAG actuel ici...
            res = collection_docs.query(query_embeddings=[prompt_emb], n_results=3)
            ctx = "\n\n".join([f"[Source: {s}]\n{c}" for s, c in zip([m["source"] for m in res["metadatas"][0]], res["documents"][0])])
            
        # C. Réponse finale avec le contexte choisi
        system_prompt = f"Tu es un expert technique. Réponds en utilisant ce contexte : {ctx}"
        # ... (Envoi à l'API comme avant)
