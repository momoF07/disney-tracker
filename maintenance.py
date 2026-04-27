import streamlit as st

def show_maintenance():
    # On utilise le query_params pour un accès ultra-rapide via l'URL (ex: ?admin=1)
    # Ou un simple champ texte discret
    
    st.markdown("""
        <style>
            .maint-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 70vh;
                text-align: center;
                font-family: 'Inter', sans-serif;
            }
            .maint-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 3rem;
                border-radius: 24px;
                max-width: 500px;
            }
            h1 {
                background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p { color: #94a3b8; }
            .stTextInput { width: 150px !important; margin: 0 auto; opacity: 0.3; transition: 0.3s; }
            .stTextInput:hover { opacity: 1; }
        </style>
        
        <div class="maint-container">
            <div class="maint-card">
                <div style="font-size: 60px; margin-bottom: 20px;">🏰</div>
                <h1>Mise à jour en cours</h1>
                <p>Le Disney Tracker se refait une beauté technique.<br>Revenez dans quelques heures.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Petit champ de mot de passe discret en bas de page
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        code = st.text_input("Accès restreint", type="password", label_visibility="collapsed", placeholder="Code...")
        
    # VERIFICATION DU CODE
    # Remplace 'MICKEY2026' par le code de ton choix
    if code == "MICKEY2026":
        st.success("Accès autorisé")
        st.session_state.bypass_maintenance = True
        st.rerun()
    else:
        st.stop() # Bloque le reste de l'app si le code est mauvais