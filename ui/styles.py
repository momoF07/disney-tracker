import streamlit as st

def apply_custom_style():
    """Injecte le CSS personnalisé optimisé (V4.0)"""
    st.markdown("""
    <style>
        /* --- 1. LAYOUT GLOBAL --- */
        .block-container {
            padding-top: 1rem; padding-bottom: 1rem;
            padding-left: 2rem; padding-right: 2rem;
            max-width: 100% !important;
        }

        /* --- 2. BOUTONS D'ACTION (HAUT DE PAGE) --- */
        .action-buttons-container { margin-bottom: 25px; padding: 5px; }
        
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 50px !important;
            border-radius: 14px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        /* Actualiser (Glass Bleu) */
        .action-buttons-container div[data-testid="column"]:nth-child(1) button {
            background: rgba(79, 172, 254, 0.1) !important;
            color: #4facfe !important;
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
        }

        /* Relevé (Gradiant Rouge) */
        .action-buttons-container div[data-testid="column"]:nth-child(2) button {
            background: linear-gradient(135deg, #ff4b4b 0%, #c0392b 100%) !important;
            color: white !important;
            border: none !important;
        }

        .action-buttons-container button:hover { transform: translateY(-2px) !important; filter: brightness(1.1); }

        /* --- 3. FILTRES RAPIDES (ISOLÉS) --- */
        .filter-container div[data-testid="stColumn"] button {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #94a3b8 !important;
            border-radius: 10px !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            height: 32px !important;
            text-transform: uppercase !important;
        }

        /* Séparateurs de Parcs */
        .park-divider {
            display: flex; align-items: center; text-align: center;
            margin: 25px 0 15px 0; color: #64748b;
        }
        .park-divider::before, .park-divider::after {
            content: ''; flex: 1; border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .park-divider:not(:empty)::before { margin-right: .75em; }
        .park-divider:not(:empty)::after { margin-left: .75em; }
        
        .park-name {
            font-size: 10px; font-weight: 800; text-transform: uppercase;
            letter-spacing: 2px; color: #94a3b8;
        }

        /* Couleurs Latérales Raccourcis */
        .filter-container div[data-testid="column"]:nth-child(2) button, 
        .filter-container div[data-testid="column"]:nth-child(7) button, 
        .filter-container div[data-testid="column"]:nth-child(8) button,
        .filter-container div[data-testid="column"]:nth-child(9) button,
        .filter-container div[data-testid="column"]:nth-child(10) button,
        .filter-container div[data-testid="column"]:nth-child(11) button {
            border-left: 3px solid #4ade80 !important;
        }

        .filter-container div[data-testid="column"]:nth-child(3) button,
        .filter-container div[data-testid="column"]:nth-child(12) button,
        .filter-container div[data-testid="column"]:nth-child(13) button,
        .filter-container div[data-testid="column"]:nth-child(14) button,
        .filter-container div[data-testid="column"]:nth-child(15) button,
        .filter-container div[data-testid="column"]:nth-child(16) button {
            border-left: 3px solid #fbbf24 !important;
        }

        /* --- 4. CARTES D'ATTRACTIONS --- */
        .ride-left-card { border-radius: 16px; padding: 10px 15px; display: flex; align-items: center; height: 68px; }
        .card-green { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); }
        .card-orange { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); }
        .card-blue { background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); }
        .card-bordeaux { background: rgba(153, 27, 27, 0.12); border: 1px solid rgba(153, 27, 27, 0.3); }
        
        /* --- 5. MULTISELECT ET CHIPS --- */
        span[data-baseweb="tag"] {
            background-color: rgba(79, 172, 254, 0.1) !important;
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
            border-radius: 6px !important;
        }

        /* Animation Shine pour les Titres Popover */
        .magic-title {
            background: linear-gradient(120deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%);
            background-size: 200% auto;
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: shine 3s linear infinite;
        }
        @keyframes shine { to { background-position: 200% center; } }
    </style>
    """, unsafe_allow_html=True)