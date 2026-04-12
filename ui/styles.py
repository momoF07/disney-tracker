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

        /* Label de l'ordre plus élégant */
        .order-label {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin: 15px 0 8px 5px;
        }

        /* --- BOUTONS D'ORDRE HARMONISÉS --- */

        /* 1. Base commune (Taille et Forme) */
        .btn-active div[data-testid="stButton"] button, 
        .btn-inactive div[data-testid="stButton"] button {
            height: 32px !important;
            min-height: 32px !important;
            border-radius: 10px !important;
            transition: all 0.3s ease !important;
        }

        /* --- OPTIMISATION DU LAYOUT (ANTI-SAUT) --- */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }
        /* Style pour les étiquettes (chips) du Multiselect */
        span[data-baseweb="tag"] {
            background-color: rgba(79, 172, 254, 0.1) !important;
            border: 1px solid rgba(79, 172, 254, 0.4) !important;
            border-radius: 8px !important;
            padding: 2px 8px !important;
            transition: all 0.2s ease !important;
        }

        span[data-baseweb="tag"]:hover {
            border-color: #4facfe !important;
            background-color: rgba(79, 172, 254, 0.2) !important;
            box-shadow: 0 0 10px rgba(79, 172, 254, 0.2) !important;
        }

        /* Couleur du texte et de l'icône de suppression (X) */
        span[data-baseweb="tag"] span {
            color: #e0e0e0 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        span[data-baseweb="tag"] svg {
            fill: #4facfe !important;
        }

        /* Supprimer le label standard pour mettre le nôtre en plus beau */
        [data-testid="stWidgetLabel"] p {
            font-size: 11px !important;
            color: #94a3b8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            font-weight: 700 !important;
            margin-bottom: 8px !important;
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
        
        /* --- BOUTONS DE RACCOURCIS RAPIDES (GRID) --- */
        div[data-testid="stColumn"] button {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #94a3b8 !important;
            border-radius: 10px !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            height: 32px !important;
            padding: 0px !important;
            text-transform: uppercase !important;
            transition: all 0.2s ease-in-out !important;
        }

        div[data-testid="stColumn"] button:hover {
            border-color: #4facfe !important;
            color: #4facfe !important;
            background-color: rgba(79, 172, 254, 0.1) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 172, 254, 0.1);
        }

        /* --- MULTISELECT MAGIQUE --- */
        span[data-baseweb="tag"] {
            background-color: rgba(79, 172, 254, 0.1) !important;
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
        }

        span[data-baseweb="tag"] span {
            color: #e0e0e0 !important;
            font-size: 12px !important;
        }

        span[data-baseweb="tag"] svg {
            fill: #4facfe !important;
        }

        /* --- LABELS DES SECTIONS --- */
        .order-label, .sort-label {
            font-size: 10px !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.15em !important;
            font-weight: 700 !important;
            margin-top: 15px !important;
            margin-bottom: 8px !important;
            display: block;
        }

        /* --- CONTENEUR DE TRI --- */
        .sort-container {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
        }
        /* --- CONTENEUR DES BOUTONS D'ACTION (HAUT DE PAGE) --- */
        .action-buttons-container {
            margin-bottom: 25px;
            padding: 5px;
        }

        /* Style de base pour les deux boutons */
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 50px !important;
            border-radius: 14px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            text-transform: none !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        }

        /* Bouton "Actualiser" (Style Glass bleu) */
        .action-buttons-container div[data-testid="column"]:nth-child(1) button {
            background: rgba(79, 172, 254, 0.1) !important;
            color: #4facfe !important;
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
        }

        .action-buttons-container div[data-testid="column"]:nth-child(1) button:hover {
            background: rgba(79, 172, 254, 0.2) !important;
            border-color: #4facfe !important;
            box-shadow: 0 0 20px rgba(79, 172, 254, 0.3) !important;
            transform: translateY(-2px) !important;
        }

        /* Bouton "Relevé manuel" (Style Danger Red Premium) */
        .action-buttons-container div[data-testid="column"]:nth-child(2) button {
            background: linear-gradient(135deg, #ff4b4b 0%, #c0392b 100%) !important;
            color: white !important;
            border: none !important;
        }

        .action-buttons-container div[data-testid="column"]:nth-child(2) button:hover {
            filter: brightness(1.2) !important;
            box-shadow: 0 0 25px rgba(255, 75, 75, 0.4) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }

        /* Effet au clic (Active) */
        .action-buttons-container button:active {
            transform: translateY(1px) scale(0.98) !important;
        }
    </style>
    """, unsafe_allow_html=True)