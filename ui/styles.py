import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
        /* --- 0. FONT & GLOBAL --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        * { box-sizing: border-box; }

        .stApp {
            background: radial-gradient(ellipse at top right, #1a2744 0%, #0f172a 50%, #0a0f1e 100%) !important;
            font-family: 'Inter', sans-serif;
        }

        /* --- 1. LAYOUT --- */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        /* --- 2. TITRE PRINCIPAL --- */
        h1 {
            background: linear-gradient(120deg, #4facfe 0%, #a78bfa 50%, #00f2fe 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            letter-spacing: -1.5px;
            text-align: center;
            padding-bottom: 0.5rem;
            animation: shimmer 4s linear infinite;
        }

        @keyframes shimmer {
            0%   { background-position: 0% center; }
            100% { background-position: 200% center; }
        }

        /* Sous-titres (subheader) */
        h2 {
            color: rgba(255,255,255,0.85) !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            letter-spacing: -0.3px;
        }

        /* --- 3. CONTAINERS SORT / SELECTION --- */
        .sort-container, .selection-container {
            background: rgba(255,255,255,0.03) !important;
            backdrop-filter: blur(16px);
            padding: 20px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
            margin-bottom: 20px;
        }

        .sort-label, .order-label {
            color: #64748b;
            font-size: 0.7rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            margin-bottom: 10px;
            margin-top: 5px;
            display: block;
        }

        /* --- 4. SEGMENTED CONTROL --- */
        div[data-baseweb="segmented-control"] {
            background-color: rgba(0,0,0,0.25) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
        }

        div[data-baseweb="segmented-control"] button {
            border: none !important;
            background: transparent !important;
            color: #64748b !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            transition: all 0.25s ease !important;
        }

        div[data-baseweb="segmented-control"] button[aria-selected="true"] {
            background: rgba(255,255,255,0.1) !important;
            color: white !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
        }

        /* --- 5. MULTISELECT CHIPS --- */
        span[data-baseweb="tag"] {
            background: rgba(79,172,254,0.12) !important;
            border: 1px solid rgba(79,172,254,0.35) !important;
            border-radius: 10px !important;
            padding: 2px 10px !important;
        }

        span[data-baseweb="tag"] span {
            color: #e2e8f0 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        /* --- 6. CARTES D'ATTRACTIONS --- */
        .ride-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            width: 100%;
            gap: 10px;
            transition: transform 0.25s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease;
        }

        .ride-row:hover {
            transform: translateY(-3px) scale(1.005);
        }

        .ride-left-card {
            background: rgba(255,255,255,0.03) !important;
            backdrop-filter: blur(16px);
            border-radius: 20px;
            padding: 12px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-grow: 1;
            height: 70px;
            border: 1px solid rgba(255,255,255,0.08) !important;
            transition: border-color 0.25s ease, background 0.25s ease;
        }

        .ride-left-card:hover {
            border-color: rgba(255,255,255,0.15) !important;
            background: rgba(255,255,255,0.05) !important;
        }

        .ride-info-meta { display: flex; align-items: center; gap: 14px; }
        .ride-titles { display: flex; flex-direction: column; }
        .ride-main-name {
            color: white;
            font-size: 14px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        }
        .ride-sub-status {
            color: rgba(255,255,255,0.5);
            font-size: 11px;
            margin: 2px 0 0 0;
            font-weight: 500;
        }

        .state-pill {
            background: rgba(0,0,0,0.35);
            color: rgba(255,255,255,0.8);
            font-size: 8px;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            border: 1px solid rgba(255,255,255,0.1);
            letter-spacing: 1.2px;
            white-space: nowrap;
        }

        .ride-right-wait {
            min-width: 76px;
            height: 70px;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }

        .wait-val { font-size: 22px; font-weight: 900; line-height: 1; }
        .wait-unit { font-size: 9px; font-weight: 700; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.5px; }

        /* --- 7. COULEURS CARTES --- */
        .card-green   { border-left: 4px solid #10b981 !important; background: rgba(16,185,129,0.06) !important; }
        .card-orange  { border-left: 4px solid #f59e0b !important; background: rgba(245,158,11,0.06) !important; }
        .card-blue    { border-left: 4px solid #3b82f6 !important; background: rgba(59,130,246,0.06) !important; }
        .card-grey    { border-left: 4px solid #64748b !important; background: rgba(100,116,139,0.06) !important; }
        .card-bordeaux{ border-left: 4px solid #ef4444 !important; background: rgba(239,68,68,0.06) !important; }
        .card-purple  { border-left: 4px solid #a78bfa !important; background: rgba(167,139,250,0.06) !important; }

        .bg-green    { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        .bg-orange   { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
        .bg-blue     { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
        .bg-grey     { background: linear-gradient(135deg, #64748b 0%, #475569 100%); }
        .bg-bordeaux { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%); }
        .bg-purple   { background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%); }

        /* --- 8. BOUTONS D'ACTION --- */
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 52px !important;
            border-radius: 16px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }

        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.35) !important;
        }

        /* --- 9. FILTRES RAPIDES --- */
        .filter-container div[data-testid="stColumn"] button {
            background: rgba(255,255,255,0.04) !important;
            color: #94a3b8 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.07) !important;
            font-size: 10px !important;
            height: 36px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px;
            font-weight: 700 !important;
        }

        /* --- 10. DIVIDERS PARCS --- */
        .park-divider {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 14px 0 10px 0;
        }

        .park-divider::before, .park-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.07);
        }

        .park-name {
            color: #475569;
            font-size: 9px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            white-space: nowrap;
        }

        /* --- 11. EXPANDER --- */
        div[data-testid="stExpander"] {
            background: rgba(255,255,255,0.02) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 16px !important;
            margin-bottom: 4px;
        }

        div[data-testid="stExpander"] summary {
            color: rgba(255,255,255,0.5) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }

        /* --- 12. INFO / CAPTION --- */
        div[data-testid="stCaptionContainer"] p {
            color: #64748b !important;
            font-size: 11px !important;
        }

        div[data-testid="stInfo"] {
            background: rgba(59,130,246,0.08) !important;
            border: 1px solid rgba(59,130,246,0.2) !important;
            border-radius: 14px !important;
            color: #93c5fd !important;
        }

        /* --- 13. SCROLLBAR --- */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

        /* --- 14. RESPONSIVE --- */
        @media (max-width: 768px) {
            .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
            .ride-left-card, .ride-right-wait { height: 62px; }
            .ride-main-name { font-size: 12px; }
            .wait-val { font-size: 18px; }
            .ride-row { gap: 8px; }
        }
    </style>
    """, unsafe_allow_html=True)