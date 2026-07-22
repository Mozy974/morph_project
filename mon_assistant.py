# Fix pour ChromaDB sqlite3 sur Streamlit Cloud
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

import streamlit as st
import os
import glob
import chromadb
from mistralai import Mistral
import datetime
from tavily import TavilyClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key_name):
    """Récupère une clé depuis st.secrets (Streamlit Cloud) ou os.environ (Local)."""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.environ.get(key_name)

# Initialisation du client Tavily avec vérification robuste
tavily_key = get_secret("TAVILY_API_KEY") or get_secret("SEARCH_API_KEY")
tavily = None
if tavily_key:
    try:
        tavily = TavilyClient(api_key=tavily_key)
    except Exception as e:
        print(f"⚠️ Initialisation Tavily impossible : {e}")
        tavily = None

# --- FONCTION JOURNAL ---
def consigner_dans_journal(probleme, solution):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entree = f"\n[{date_str}] - PROBLÈME : {probleme}\nSOLUTION : {solution}\n"
    with open("historique_resolutions.md", "a", encoding="utf-8") as f:
        f.write(entree)

# --- CONFIGURATION ---
st.set_page_config(page_title="Mon Assistant Personnel", page_icon="🧠")

# Chargement forcé de la clé
API_KEY = get_secret("MISTRAL_API_KEY")

if not API_KEY:
    st.error("❌ La clé API MISTRAL n'est pas détectée. Veuillez l'ajouter dans 'Settings > Secrets' de Streamlit Cloud ou exporter MISTRAL_API_KEY.")
    st.stop()

mistral_client = Mistral(api_key=API_KEY)
DOCS_FOLDER = "mes_documents"

# --- FONCTIONS RAG ---
def lire_fichiers_locaux(dossier):
    documents, sources = [], []
    if not os.path.exists(dossier): os.makedirs(dossier)
    fichiers = glob.glob(f"{dossier}/*.txt") + glob.glob(f"{dossier}/*.md")
    for fichier in fichiers:
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
            paragraphes = [p.strip() for p in contenu.split("\n\n") if len(p.strip()) > 50]
            for i, para in enumerate(paragraphes):
                documents.append(para)
                sources.append(f"{os.path.basename(fichier)} - bloc {i}")
    return documents, sources

@st.cache_resource
def initialiser_base_vectorielle():
    db_client = chromadb.Client()
    try: db_client.delete_collection("base_personnelle")
    except: pass
    collection = db_client.create_collection(name="base_personnelle")
    documents, sources = lire_fichiers_locaux(DOCS_FOLDER)
    if not documents: return collection, False
    embeddings_response = mistral_client.embeddings.create(model="mistral-embed", inputs=documents)
    collection.add(
        embeddings=[e.embedding for e in embeddings_response.data],
        documents=documents,
        metadatas=[{"source": s} for s in sources],
        ids=[f"id_{i}" for i in range(len(documents))]
    )
    return collection, True

collection_docs, base_prete = initialiser_base_vectorielle()

# --- BARRE LATÉRALE : TÉLÉVERSEMENT DE DOCUMENTS ---
with st.sidebar:
    st.header("📂 Gestion des connaissances")
    st.write("Ajoutez de nouvelles notes pour enrichir l'assistant.")
    
    fichiers_uploades = st.file_uploader(
        "Choisir des fichiers", 
        type=["txt", "md"], 
        accept_multiple_files=True
    )
    
    if fichiers_uploades:
        nouveaux_fichiers = False
        for fichier in fichiers_uploades:
            chemin_destination = os.path.join(DOCS_FOLDER, fichier.name)
            if not os.path.exists(chemin_destination):
                with open(chemin_destination, "wb") as f:
                    f.write(fichier.getbuffer())
                st.sidebar.success(f"💾 {fichier.name} enregistré !")
                nouveaux_fichiers = True
        
        if nouveaux_fichiers:
            st.sidebar.info("🔄 Mise à jour de la base de connaissances...")
            st.cache_resource.clear()
            st.rerun()

# --- INTERFACE ---
st.title("🧠 Mon Assistant Personnel")
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- LOGIQUE CONVERSATION ---
if prompt := st.chat_input("Posez une question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Réflexion...*")
        
        # 1. Étape de décision
        decision_prompt = f"La question suivante nécessite-t-elle une recherche sur Internet ? Réponds uniquement par 'OUI' ou 'NON'. Question : {prompt}"
        response_decision = mistral_client.chat.complete(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": decision_prompt}]
        )
        decision = response_decision.choices[0].message.content
        
        # 2. Exécution selon la décision
        ctx = ""
        if "OUI" in decision.upper():
            if tavily:
                try:
                    message_placeholder.markdown("🌐 *Recherche Web activée...*")
                    search_data = tavily.search(query=prompt, search_depth="basic")
                    ctx = f"RÉSULTATS WEB : {search_data.get('results', [])}"
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors de la recherche Web Tavily : {e}. Basculement en mode local.")
                    ctx = ""
            else:
                st.warning("⚠️ Recherche Web demandée mais TAVILY_API_KEY non configurée dans Secrets. Basculement sur les documents locaux.")

        if not ctx:
            message_placeholder.markdown("🔍 *Analyse des documents locaux...*")
            if base_prete:
                prompt_emb = mistral_client.embeddings.create(model="mistral-embed", inputs=[prompt]).data[0].embedding
                res = collection_docs.query(query_embeddings=[prompt_emb], n_results=3)
                if res and res.get("documents") and res["documents"][0]:
                    ctx = "\n\n".join([f"[Source: {s}]\n{c}" for s, c in zip([m["source"] for m in res["metadatas"][0]], res["documents"][0])])
            
            if not ctx:
                ctx = "Aucun document spécifique trouvé dans la base locale."

        # 3. Réponse finale avec sources intégrées
        system_prompt = f"""Tu es un expert technique. Réponds à la question en utilisant ce contexte : {ctx}
        
        IMPORTANT : À la fin de ta réponse, liste toujours les sources utilisées sous forme de puces.
        """
        
        api_messages = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = mistral_client.chat.complete(model="mistral-small-latest", messages=api_messages)
        reponse_finale = response.choices[0].message.content
        
        message_placeholder.markdown(reponse_finale)
        st.session_state.messages.append({"role": "assistant", "content": reponse_finale})

        # Bouton sauvegarde
        if st.button("✅ Consigner dans le journal"):
            consigner_dans_journal(prompt, reponse_finale)
            st.success("Résolution sauvegardée !")
