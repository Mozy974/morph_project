import streamlit as st
import os
import datetime
from rag_pipeline import HybridRAGPipeline, load_documents

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

# --- FONCTION JOURNAL ---
def consigner_dans_journal(probleme, solution):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entree = f"\n[{date_str}] - PROBLÈME : {probleme}\nSOLUTION : {solution}\n"
    with open("historique_resolutions.md", "a", encoding="utf-8") as f:
        f.write(entree)

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Mon Assistant Personnel RAG", page_icon="🧠")

API_KEY = get_secret("MISTRAL_API_KEY")
TAVILY_KEY = get_secret("TAVILY_API_KEY") or get_secret("SEARCH_API_KEY")

if not API_KEY:
    st.error("❌ La clé API MISTRAL n'est pas détectée. Veuillez l'ajouter dans 'Settings > Secrets' de Streamlit Cloud ou exporter MISTRAL_API_KEY.")
    st.stop()

DOCS_FOLDER = "mes_documents"

@st.cache_resource
def initialiser_pipeline_rag():
    pipeline = HybridRAGPipeline(
        mistral_api_key=API_KEY,
        tavily_api_key=TAVILY_KEY,
        docs_folder=DOCS_FOLDER
    )
    is_indexed = pipeline.init_vector_store()
    return pipeline, is_indexed

rag_pipeline, base_prete = initialiser_pipeline_rag()

# --- BARRE LATÉRALE : TÉLÉVERSEMENT DE DOCUMENTS & CONFIGURATION ---
with st.sidebar:
    st.header("📂 Base de connaissances RAG")
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
            st.sidebar.info("🔄 Re-indexation de la base vectorielle...")
            st.cache_resource.clear()
            st.rerun()

    st.markdown("---")
    st.header("⚙️ Mode de recherche")
    mode_recherche = st.selectbox(
        "Mode RAG",
        options=["AUTO", "HYBRID", "WEB", "LOCAL"],
        index=0,
        help="AUTO: Détection automatique par l'IA | HYBRID: Local + Web | WEB: DuckDuckGo/Tavily | LOCAL: ChromaDB"
    )

# --- INTERFACE PRINCIPALE ---
st.title("🧠 Mon Assistant Personnel (RAG Hybride)")
if "messages" not in st.session_state: 
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

# --- LOGIQUE CONVERSATION ---
if prompt := st.chat_input("Posez une question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Recherche et analyse en cours...*")
        
        # Exécution du requêtage hybride via rag_pipeline
        rag_result = rag_pipeline.hybrid_query(
            query=prompt,
            search_mode=mode_recherche,
            max_web_results=3,
            n_local_results=3
        )

        mode_used = rag_result["mode_used"]
        context = rag_result["context"]

        if mode_used == "WEB":
            st.caption("🌐 *Recherche Web effectuée (DuckDuckGo / Tavily)*")
        elif mode_used == "LOCAL":
            st.caption("📄 *Consultation des documents locaux (ChromaDB)*")
        else:
            st.caption("🌐📄 *Recherche Hybride effectuée (Local + Web)*")

        # Formatage de l'historique de conversation
        history_formatted = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        # Génération de la réponse
        reponse_finale = rag_pipeline.generate_response(
            query=prompt,
            context=context,
            history=history_formatted
        )
        
        message_placeholder.markdown(reponse_finale)
        st.session_state.messages.append({"role": "assistant", "content": reponse_finale})

        # Bouton sauvegarde journal
        if st.button("✅ Consigner dans le journal"):
            consigner_dans_journal(prompt, reponse_finale)
            st.success("Résolution sauvegardée !")
