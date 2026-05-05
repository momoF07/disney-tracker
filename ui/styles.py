import streamlit as st

def apply_custom_style():
    """Injecte le CSS personnalisé premium (Glassmorphism & Magic Design)"""
    st.markdown("""
    <style>
        /* --- 0. IMPORT FONT & SETUP GLOBAL --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        .stApp {
            background: radial-gradient(circle at top right, #1e293b, #0f172a) !important;
            font-family: 'Inter', sans-serif;
        }

        /* --- 1. LAYOUT GLOBAL --- */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        /* --- 2. TITRES ET TEXTES --- */
        h1 {
            background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
            letter-spacing: -1px;
            text-align: center;
            padding-bottom: 1rem;
        }

        /* --- 3. BARRE DE SÉLECTION & TRI (CONTAINER) --- */
        .sort-container, .selection-container {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            margin-bottom: 20px;
        }

        .sort-label, .order-label {
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 10px;
            margin-top: 5px;
            display: block;
        }

        /* --- 4. WIDGETS (SEGMENTED CONTROL & MULTISELECT) --- */
        div[data-baseweb="segmented-control"] {
            background-color: rgba(0, 0, 0, 0.2) !important;
            border-radius: 12px !important;
            padding: 4px !important;
        }
        
        div[data-baseweb="segmented-control"] button {
            border: none !important;
            background: transparent !important;
            color: #94a3b8 !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-baseweb="segmented-control"] button[aria-selected="true"] {
            background: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        /* Style pour les étiquettes (chips) du Multiselect */
        span[data-baseweb="tag"] {
            background-color: rgba(79, 172, 254, 0.15) !important;
            border: 1px solid rgba(79, 172, 254, 0.4) !important;
            border-radius: 8px !important;
            padding: 2px 8px !important;
        }

        span[data-baseweb="tag"] span {
            color: #e0e0e0 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        /* --- 5. CARTES D'ATTRACTIONS (DESIGN MAGIQUE) --- */
        .ride-row { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 12px; 
            width: 100%; 
            gap: 12px;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .ride-row:hover {
            transform: translateY(-4px) scale(1.01);
        }

        .ride-left-card { 
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(12px);
            border-radius: 20px; 
            padding: 12px 18px; 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            flex-grow: 1; 
            height: 72px; 
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        .ride-info-meta { display: flex; align-items: center; gap: 15px; }
        .ride-titles { display: flex; flex-direction: column; }
        .ride-main-name { color: white; font-size: 15px; font-weight: 700; margin: 0; line-height: 1.2; }
        .ride-sub-status { color: rgba(255,255,255,0.6); font-size: 11px; margin: 0; font-weight: 500; }
        
        .state-pill { 
            background: rgba(0,0,0,0.4); 
            color: white; 
            font-size: 9px; 
            font-weight: 800; 
            padding: 3px 10px; 
            border-radius: 20px; 
            text-transform: uppercase; 
            border: 1px solid rgba(255,255,255,0.15); 
            letter-spacing: 1px;
        }

        .ride-right-wait { 
            min-width: 80px; 
            height: 72px; 
            border-radius: 20px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            color: white; 
            box-shadow: 0 8px 16px rgba(0,0,0,0.2); 
            border: 1px solid rgba(255,255,255,0.1);
        }

        .wait-val { font-size: 24px; font-weight: 800; line-height: 1; }
        .wait-unit { font-size: 10px; font-weight: 600; opacity: 0.7; text-transform: uppercase; }

        /* --- 6. COULEURS THÉMATIQUES DES CARTES --- */
        .card-green { border-left: 5px solid #10b981 !important; background: rgba(16, 185, 129, 0.08) !important; }
        .card-orange { border-left: 5px solid #f59e0b !important; background: rgba(245, 158, 11, 0.08) !important; }
        .card-blue { border-left: 5px solid #3b82f6 !important; background: rgba(59, 130, 246, 0.08) !important; }
        .card-grey { border-left: 5px solid #64748b !important; background: rgba(100, 116, 139, 0.08) !important; }
        .card-bordeaux { border-left: 5px solid #ef4444 !important; background: rgba(239, 68, 68, 0.08) !important; }
        .card-purple { border-left: 5px solid #a78bfa !important; background: rgba(167, 139, 250, 0.08) !important; }

        .bg-green { background: linear-gradient(135deg, #10b981, #059669); }
        .bg-orange { background: linear-gradient(135deg, #f59e0b, #d97706); }
        .bg-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .bg-grey { background: linear-gradient(135deg, #64748b, #475569); }
        .bg-bordeaux { background: linear-gradient(135deg, #ef4444, #991b1b); }
        .bg-purple { background: linear-gradient(135deg, #a78bfa, #7c3aed); }

        /* --- 7. BOUTONS D'ACTION & FILTRES --- */
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 54px !important;
            border-radius: 18px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        /* Hover dynamique boutons */
        div[data-testid="stButton"] button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3) !important;
        }

        /* Grilles de Filtres (Raccourcis) */
        .filter-container div[data-testid="stColumn"] button {
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: #94a3b8 !important;
            border-radius: 12px !important;
            font-size: 11px !important;
            height: 38px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px;
        }

        /* --- 8. RESPONSIVE OPTIMIZATIONS --- */
        @media (max-width: 768px) {
            .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
            .ride-left-card, .ride-right-wait { height: 64px; }
            .ride-main-name { font-size: 13px; }
            .wait-val { font-size: 20px; }
            .ride-row { gap: 8px; }
        }
    </style>
    """, unsafe_allow_html=True)