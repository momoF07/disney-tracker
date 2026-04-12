import streamlit as st

def apply_custom_style():
    """Injecte le CSS personnalisé dans l'application Streamlit"""
    st.markdown("""
    <style>
/* --- 1. LAYOUT GLOBAL --- */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        /* --- 2. BARRE DE TRI (CONTAINER) --- */
        .sort-container {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            padding: 15px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .sort-label {
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 8px;
        }

        .order-label {
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 700;
            margin-top: 10px;
            margin-bottom: 4px;
            letter-spacing: 0.05em;
        }

        /* --- 3. WIDGETS DE TRI (SEGMENTED CONTROL) --- */
        div[data-baseweb="segmented-control"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
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
        }

        /* --- 4. PETITS BOUTONS D'ORDRE (ASC / DESC) --- */
        /* On cible les boutons par leur clé spécifiée dans app.py */
        .btn-inactive > div > button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            color: #475569 !important;
            height: 32px !important;
            min-height: 32px !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }

        .btn-active > div > button {
            background: rgba(79, 172, 254, 0.15) !important;
            border: 1px solid #4facfe !important;
            color: #4facfe !important;
            height: 32px !important;
            min-height: 32px !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            box-shadow: 0 0 12px rgba(79, 172, 254, 0.2) !important;
        }

        /* --- OPTIMISATION DU LAYOUT (ANTI-SAUT) --- */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        /* --- RESPONSIVE : CARTES ET COLONNES --- */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            .ride-left-card {
                padding: 8px 10px;
                height: 60px;
            }
            .ride-right-wait {
                min-width: 65px;
                height: 60px;
            }
            .ride-main-name { font-size: 12px; }
            .wait-val { font-size: 18px; }
        }

        /* --- DESIGN DES BADGES ET CARTES --- */
        .ride-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; width: 100%; gap: 10px; }
        .ride-left-card { border-radius: 16px; padding: 10px 15px; display: flex; align-items: center; justify-content: space-between; flex-grow: 1; height: 68px; }
        .ride-info-meta { display: flex; align-items: center; gap: 12px; }
        .ride-titles { display: flex; flex-direction: column; }
        .ride-main-name { color: white; font-size: 14px; font-weight: 600; margin: 0; line-height: 1.2; }
        .ride-sub-status { color: rgba(255,255,255,0.7); font-size: 11px; margin: 0; }
        .state-pill { background: rgba(0,0,0,0.3); color: white; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.1); }
        .ride-right-wait { min-width: 75px; height: 68px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .wait-val { font-size: 20px; font-weight: 800; line-height: 1; }
        .wait-unit { font-size: 10px; font-weight: 400; opacity: 0.8; }

        /* --- COULEURS DES CARTES --- */
        .card-green { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); }
        .card-orange { background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
        .card-blue { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); }
        .card-grey { background: rgba(107, 114, 128, 0.15); border: 1px solid rgba(107, 114, 128, 0.3); }
        .card-bordeaux { background: rgba(153, 27, 27, 0.15); border: 1px solid rgba(153, 27, 27, 0.3); }
        .bg-green { background: #10b981; }
        .bg-orange { background: #f59e0b; }
        .bg-blue { background: #3b82f6; }
        .bg-grey { background: #6b7280; }
        .bg-bordeaux { background: #991b1b; }

        /* --- ANIMATIONS ET POPOVER --- */
        @keyframes shine { to { background-position: 200% center; } }
        .magic-title {
            text-align: center;
            background: linear-gradient(120deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800; font-size: 28px; margin-bottom: 25px;
            animation: shine 3s linear infinite;
        }
        .cat-badge-magic {
            padding: 8px 20px; border-radius: 50px; font-size: 14px; font-weight: 700;
            display: block; text-align: center; margin: 20px 0 10px 0; text-transform: uppercase;
        }
        .bg-blue-magic { background: linear-gradient(45deg, #4facfe, #00f2fe); color: white; }
        .bg-green-magic { background: linear-gradient(45deg, #43e97b, #38f9d7); color: white; }
        .bg-orange-magic { background: linear-gradient(45deg, #f9d423, #ff4e50); color: white; }
        .shortcut-card {
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px); border-radius: 15px; padding: 12px; margin-bottom: 10px; transition: 0.3s;
        }
        .shortcut-card:hover { transform: translateY(-3px); background: rgba(255, 255, 255, 0.08); }
        
        /* Harmonisation des codes dans le popover */
        code { color: #4facfe !important; background: rgba(79, 172, 254, 0.1) !important; }
    </style>
    """, unsafe_allow_html=True)