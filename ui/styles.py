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

        /* --- LAYOUT & CONTAINERS --- */
        .block-container { padding: 1rem 2rem; max-width: 100% !important; }
        
        .sort-container {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 15px; padding: 15px; margin-bottom: 20px;
        }

        /* --- BOUTONS D'ACTION (HAUT DE PAGE) --- */
        /* On cible uniquement les boutons dans ce conteneur spécifique */
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 50px !important;
            border-radius: 14px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            transition: all 0.3s ease !important;
        }

        /* Bouton Actualiser (Glass Bleu) */
        .action-buttons-container div[data-testid="column"]:nth-child(1) button {
            background: rgba(79, 172, 254, 0.1) !important;
            color: #4facfe !important;
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
        }

        /* Bouton Relevé (Gradiant Rouge) */
        .action-buttons-container div[data-testid="column"]:nth-child(2) button {
            background: linear-gradient(135deg, #ff4b4b 0%, #c0392b 100%) !important;
            color: white !important;
            border: none !important;
        }

        .action-buttons-container button:hover { transform: translateY(-2px); filter: brightness(1.1); }

        /* --- BOUTONS DE RACCOURCIS (DANS FILTER-CONTAINER) --- */
.filter-container div[data-testid="stColumn"] button {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #94a3b8 !important;
    border-radius: 10px !important;
    font-size: 10px !important;
    height: 32px !important;
    text-transform: uppercase !important;
}

    /* --- LIGNE 1 : 6 boutons globaux --- */
    .filter-container > div:nth-of-type(1) div[data-testid="stColumn"]:nth-child(2) button { border-left: 3px solid #4ade80 !important; } /* DLP */
    .filter-container > div:nth-of-type(1) div[data-testid="stColumn"]:nth-child(3) button { border-left: 3px solid #fb923c !important; } /* DAW */
    .filter-container > div:nth-of-type(1) div[data-testid="stColumn"]:nth-child(4) button { border-left: 3px solid #ff4b4b !important; } /* 101 */
    .filter-container > div:nth-of-type(1) div[data-testid="stColumn"]:nth-child(5) button { border-left: 3px solid #ff4b4b !important; } /* 102 */
    .filter-container > div:nth-of-type(1) div[data-testid="stColumn"]:nth-child(6) button { border-left: 3px solid #ff4b4b !important; } /* FERMÉ */

    /* --- LIGNE 2 : 5 boutons Disneyland Park --- */
    .filter-container > div:nth-of-type(2) div[data-testid="stColumn"]:nth-child(1) button { border-left: 3px solid #f472b6 !important; } /* MS */
    .filter-container > div:nth-of-type(2) div[data-testid="stColumn"]:nth-child(2) button { border-left: 3px solid #fbbf24 !important; } /* FRONTIER */
    .filter-container > div:nth-of-type(2) div[data-testid="stColumn"]:nth-child(3) button { border-left: 3px solid #10b981 !important; } /* ADVENTURE */
    .filter-container > div:nth-of-type(2) div[data-testid="stColumn"]:nth-child(4) button { border-left: 3px solid #60a5fa !important; } /* FANTASY */
    .filter-container > div:nth-of-type(2) div[data-testid="stColumn"]:nth-child(5) button { border-left: 3px solid #a78bfa !important; } /* DISCO */

    /* --- LIGNE 3 : 5 boutons Adventure World --- */
    .filter-container > div:nth-of-type(3) div[data-testid="stColumn"]:nth-child(1) button { border-left: 3px solid #ef4444 !important; } /* CAMPUS */
    .filter-container > div:nth-of-type(3) div[data-testid="stColumn"]:nth-child(2) button { border-left: 3px solid #34d399 !important; } /* PIXAR */
    .filter-container > div:nth-of-type(3) div[data-testid="stColumn"]:nth-child(3) button { border-left: 3px solid #6366f1 !important; } /* COURTYARD */
    .filter-container > div:nth-of-type(3) div[data-testid="stColumn"]:nth-child(4) button { border-left: 3px solid #00f2fe !important; } /* FROZEN */
    .filter-container > div:nth-of-type(3) div[data-testid="stColumn"]:nth-child(5) button { border-left: 3px solid #84cc16 !important; } /* WAY */

        /* Status & Reset */
        .filter-container .status-btn button { border-left: 3px solid #ff4b4b !important; }

        /* Style des cartes d'attractions (inchangé) */
        .card-green { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); }
        .card-orange { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); }
        .card-bordeaux { background: rgba(153, 27, 27, 0.12); border: 1px solid rgba(153, 27, 27, 0.3); }

        
    </style>
    """, unsafe_allow_html=True)
    