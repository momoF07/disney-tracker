import streamlit as st

def show_maintenance():
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
            /* Style pour rendre le champ très discret */
            div[data-baseweb="input"] {
                background: transparent !important;
                border: none !important;
            }
            input {
                text-align: center !important;
                color: rgba(255,255,255,0.2) !important;
            }
        </style>
        
        <div class="maint-container">
            <div class="maint-card">
                <div style="font-size: 60px; margin-bottom: 20px;">🏰</div>
                <h1>Mise à jour en cours</h1>
                <p>Le Disney Tracker se refait une beauté technique.<br>Revenez dans quelques heures.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        # Utilisation d'une clé spécifique pour Streamlit
        code = st.text_input("Accès", type="password", label_visibility="collapsed", placeholder="...", key="maint_password")
        
    if code == "AdminPass": # Ton code secret
        st.session_state.bypass_maintenance = True
        st.rerun() 
    
    st.stop()