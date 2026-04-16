import streamlit as st

def show_maintenance():
    st.set_page_config(page_title="Maintenance | Disney Tracker", page_icon="🏰")
    
    st.markdown("""
        <style>
            /* Fond animé */
            .main {
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
            }
            
            .maint-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 80vh;
                text-align: center;
                font-family: 'Inter', sans-serif;
            }

            .maint-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 3rem;
                border-radius: 24px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                max-width: 500px;
            }

            .glow-icon {
                font-size: 60px;
                margin-bottom: 20px;
                filter: drop-shadow(0 0 15px #4facfe);
                animation: pulse 2s infinite;
            }

            h1 {
                color: white;
                font-weight: 800;
                margin-bottom: 10px;
                background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            p {
                color: #94a3b8;
                font-size: 1.1rem;
                line-height: 1.6;
            }

            .loader {
                border: 3px solid rgba(255,255,255,0.1);
                border-top: 3px solid #4facfe;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }

            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        </style>

        <div class="maint-container">
            <div class="maint-card">
                <div class="glow-icon">🏰</div>
                <h1>Mise à jour en cours</h1>
                <p>Le Disney Tracker se refait une beauté technique. <br>Nous revenons dans quelques minutes avec des données encore plus fraîches.</p>
                <div class="loader"></div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 20px;">
                    STATUS: PCOps Connection Update
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop() # Arrête l'exécution du reste de l'app