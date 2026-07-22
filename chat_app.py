import streamlit as st
import os
import json
import time
from datetime import datetime

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key_name):
    """Récupère une clé d'API depuis st.secrets (Streamlit Cloud) ou os.environ (Local)."""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.environ.get(key_name)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SuperChat AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PERSONAS & MODÈLES ---
PERSONAS = {
    "🧠 Assistant Général": "Tu es un assistant virtuel polyvalent, courtois, précis et efficace.",
    "💻 Codeur Expert": "Tu es un expert en ingénierie logicielle, Python, architectures et clean code. Réponds avec des explications concises et des exemples de code parfaitement formatés.",
    "📝 Rédacteur Pédagogue": "Tu es un spécialiste de la rédaction, du synthétisme et de la pédagogie. Explique les concepts clairement avec une structure structurée.",
    "📊 Analyste Data": "Tu es un analyste de données spécialisé en statistiques, visualisation et interprétation pragmatique."
}

MODELS = {
    "Mistral Small": "mistral-small-latest",
    "Mistral Medium": "mistral-medium-latest",
    "Mistral Large": "mistral-large-latest"
}

# --- INITIALISATION SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = PERSONAS["🧠 Assistant Général"]

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # 1. Sélection du Persona
    persona_choice = st.selectbox(
        "Persona de l'assistant",
        options=list(PERSONAS.keys()),
        index=0
    )
    st.session_state.system_prompt = PERSONAS[persona_choice]
    
    # 2. Sélection du Modèle
    model_choice = st.selectbox(
        "Modèle LLM",
        options=list(MODELS.keys()),
        index=0
    )
    target_model = MODELS[model_choice]

    # 3. Paramètres d'inférence
    st.subheader("🎛️ Paramètres")
    temperature = st.slider("Température (Créativité)", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    st.markdown("---")
    
    # 4. Actions sur l'historique
    st.subheader("🧹 Gestion du Chat")
    
    if st.button("Vider la conversation", icon=":material/delete:", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    if st.session_state.messages:
        chat_transcript = json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)
        st.download_button(
            label="Télécharger l'historique (JSON)",
            data=chat_transcript,
            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            icon=":material/download:",
            use_container_width=True
        )

# --- CLÉ API & MISTRAL CLIENT ---
api_key = get_secret("MISTRAL_API_KEY")

# --- HEADER PRINCIPAL ---
st.title("💬 SuperChat AI")
st.caption("Application de Chat IA moderne propulsée par **Mistral AI** et **Streamlit**.")

if not api_key:
    st.warning("⚠️ Clé `MISTRAL_API_KEY` non détectée. Veuillez l'ajouter dans vos secrets Streamlit Cloud ou exporter la variable d'environnement.")
    st.info("Pour tester l'interface en mode simulation sans clé API, saisissez votre message ci-dessous.")

# --- AFFICHAGE DE L'HISTORIQUE ---
for msg in st.session_state.messages:
    avatar_icon = ":material/person:" if msg["role"] == "user" else ":material/smart_toy:"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# --- ENTREE UTILISATEUR & GENERATION DE REPONSE ---
if prompt := st.chat_input("Posez votre question..."):
    # 1. Ajout du message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    # 2. Génération de la réponse
    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        message_placeholder = st.empty()
        
        if api_key and Mistral:
            try:
                client = Mistral(api_key=api_key)
                api_messages = [{"role": "system", "content": st.session_state.system_prompt}] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ]
                
                with st.spinner("Réflexion en cours..."):
                    response = client.chat.complete(
                        model=target_model,
                        messages=api_messages,
                        temperature=temperature
                    )
                    full_response = response.choices[0].message.content
                    
                # Effet de streaming textuel
                displayed_text = ""
                for char in full_response:
                    displayed_text += char
                    message_placeholder.markdown(displayed_text + "▌")
                    time.sleep(0.002)
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"❌ Erreur lors de la génération : {e}"
                message_placeholder.error(full_response)
        else:
            # Mode de démonstration / simulation si la clé n'est pas disponible
            full_response = f"🤖 **[Mode Démo]** J'ai bien reçu votre message : *\"{prompt}\"*\n\n*(Pour activer les réponses réelles du modèle Mistral, configurez `MISTRAL_API_KEY` dans vos secrets Streamlit Cloud).* "
            displayed_text = ""
            for char in full_response:
                displayed_text += char
                message_placeholder.markdown(displayed_text + "▌")
                time.sleep(0.005)
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
