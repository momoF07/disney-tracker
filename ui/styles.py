import streamlit as st


def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Mulish:wght@300;400;500;600&display=swap');

        /* === BASE === */
        * { box-sizing: border-box; margin: 0; padding: 0; }

        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 20% -10%, rgba(120,80,255,0.15) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,100,150,0.1) 0%, transparent 55%),
                radial-gradient(ellipse 100% 80% at 50% 50%, #090d1a 0%, #060910 100%);
            font-family: 'Mulish', sans-serif;
        }

        .stApp::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 0;
            opacity: 0.4;
        }

        /* === LAYOUT === */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }

        /* === TITRE === */
        h1 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            font-size: 2rem !important;
            letter-spacing: -2px !important;
            text-align: center;
            padding-bottom: 0.75rem;
            background: linear-gradient(135deg, #ffd6e7 0%, #c4b5fd 35%, #7dd3fc 65%, #ffd6e7 100%);
            background-size: 300% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: titleFlow 6s ease infinite;
        }

        @keyframes titleFlow {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        h2 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            color: rgba(255,255,255,0.7) !important;
            letter-spacing: 0.5px !important;
        }

        /* === CONTAINERS SORT / SELECTION === */
        .sort-container, .selection-container {
            background: rgba(255,255,255,0.025) !important;
            backdrop-filter: blur(20px) saturate(180%);
            padding: 16px 18px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.07);
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.03) inset,
                0 20px 40px rgba(0,0,0,0.4),
                0 1px 0 rgba(255,255,255,0.06) inset;
            margin-bottom: 14px;
        }

        .sort-label, .order-label {
            font-family: 'Outfit', sans-serif;
            color: #475569;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.25em;
            margin-bottom: 10px;
            margin-top: 4px;
            display: block;
        }

        /* === SEGMENTED CONTROL === */
        div[data-baseweb="segmented-control"] {
            background: rgba(0,0,0,0.3) !important;
            border-radius: 14px !important;
            padding: 3px !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
        }

        div[data-baseweb="segmented-control"] button {
            border: none !important;
            background: transparent !important;
            color: #475569 !important;
            font-family: 'Mulish', sans-serif !important;
            font-weight: 600 !important;
            font-size: 11px !important;
            transition: all 0.2s ease !important;
        }

        div[data-baseweb="segmented-control"] button[aria-selected="true"] {
            background: linear-gradient(135deg, rgba(196,181,253,0.2), rgba(125,211,252,0.15)) !important;
            color: white !important;
            border-radius: 11px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.08) inset;
        }

        /* === MULTISELECT === */
        span[data-baseweb="tag"] {
            background: linear-gradient(135deg, rgba(196,181,253,0.15), rgba(125,211,252,0.1)) !important;
            border: 1px solid rgba(196,181,253,0.3) !important;
            border-radius: 10px !important;
            padding: 1px 8px !important;
        }

        span[data-baseweb="tag"] span {
            color: #e2e8f0 !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            font-family: 'Mulish', sans-serif !important;
        }

        /* === CARTES ATTRACTIONS === */
        .ride-row {
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            margin-bottom: 7px;
            width: 100%;
            gap: 7px;
            transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1);
        }

        .ride-row:hover { transform: translateY(-2px) scale(1.002); }

        .ride-left-card {
            background: rgba(255,255,255,0.025) !important;
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-grow: 1;
            min-height: 58px;
            height: auto;
            border: 1px solid rgba(255,255,255,0.07) !important;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }

        .ride-left-card::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(105deg, rgba(255,255,255,0.03) 0%, transparent 60%);
            pointer-events: none;
        }

        .ride-left-card:hover {
            border-color: rgba(255,255,255,0.12) !important;
            background: rgba(255,255,255,0.04) !important;
        }

        .ride-info-meta {
            display: flex;
            align-items: center;
            gap: 11px;
            z-index: 1;
            flex: 1;
            min-width: 0;
        }

        .ride-titles {
            display: flex;
            flex-direction: column;
            min-width: 0;
            flex: 1;
        }

        .ride-main-name {
            font-family: 'Mulish', sans-serif;
            color: rgba(255,255,255,0.92);
            font-size: 11.5px;
            font-weight: 600;
            margin: 0;
            line-height: 1.3;
            white-space: normal;
            word-break: break-word;
        }

        .ride-sub-status {
            font-family: 'Mulish', sans-serif;
            color: rgba(255,255,255,0.38);
            font-size: 10px;
            margin: 2px 0 0 0;
            font-weight: 400;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .state-pill {
            font-family: 'Outfit', sans-serif;
            background: rgba(0,0,0,0.4);
            color: rgba(255,255,255,0.65);
            font-size: 7px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 20px;
            text-transform: uppercase;
            border: 1px solid rgba(255,255,255,0.08);
            letter-spacing: 1.2px;
            white-space: nowrap;
            z-index: 1;
            flex-shrink: 0;
        }

        .ride-right-wait {
            min-width: 62px;
            width: 62px;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 8px 20px rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.08);
            position: relative;
            overflow: hidden;
            align-self: stretch;
            min-height: 58px;
        }

        .ride-right-wait::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 50%;
            background: rgba(255,255,255,0.06);
            pointer-events: none;
        }

        .wait-val {
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 800;
            line-height: 1;
            z-index: 1;
        }

        .wait-unit {
            font-size: 7px;
            font-weight: 600;
            opacity: 0.6;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            z-index: 1;
        }

        /* === COULEURS CARTES === */
        .card-green    { border-left: 3px solid #34d399 !important; background: rgba(52,211,153,0.04) !important; }
        .card-orange   { border-left: 3px solid #fbbf24 !important; background: rgba(251,191,36,0.04) !important; }
        .card-blue     { border-left: 3px solid #60a5fa !important; background: rgba(96,165,250,0.04) !important; }
        .card-grey     { border-left: 3px solid #64748b !important; background: rgba(100,116,139,0.04) !important; }
        .card-bordeaux { border-left: 3px solid #f87171 !important; background: rgba(248,113,113,0.04) !important; }
        .card-purple   { border-left: 3px solid #a78bfa !important; background: rgba(167,139,250,0.04) !important; }

        .bg-green    { background: linear-gradient(135deg, #059669, #047857); }
        .bg-orange   { background: linear-gradient(135deg, #d97706, #b45309); }
        .bg-blue     { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
        .bg-grey     { background: linear-gradient(135deg, #475569, #334155); }
        .bg-bordeaux { background: linear-gradient(135deg, #dc2626, #991b1b); }
        .bg-purple   { background: linear-gradient(135deg, #7c3aed, #6d28d9); }

        /* === FILTRES RAPIDES === */
        .filter-container div[data-testid="stColumn"] button {
            background: rgba(255,255,255,0.03) !important;
            color: #64748b !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 9px !important;
            height: 28px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            font-weight: 700 !important;
            padding: 0 8px !important;
        }

        /* === BOUTONS D'ACTION === */
        .action-buttons-container div[data-testid="stColumn"] button {
            height: 44px !important;
            border-radius: 13px !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
        }

        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important;
        }

        /* === DIVIDERS PARCS === */
        .park-divider {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 14px 0 8px 0;
        }

        .park-divider::before, .park-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.05);
        }

        .park-name, .class-name {
            font-family: 'Outfit', sans-serif;
            color: #334155;
            font-size: 8px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            white-space: nowrap;
        }

        /* === EXPANDER === */
        div[data-testid="stExpander"] {
            background: rgba(255,255,255,0.015) !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            border-radius: 14px !important;
            margin-bottom: 3px !important;
        }

        div[data-testid="stExpander"] summary {
            color: rgba(255,255,255,0.35) !important;
            font-size: 10px !important;
            font-weight: 500 !important;
            font-family: 'Mulish', sans-serif !important;
        }

        div[data-testid="stExpander"] summary:hover {
            color: rgba(255,255,255,0.6) !important;
        }

        /* === INFO / CAPTION === */
        div[data-testid="stCaptionContainer"] p {
            color: #475569 !important;
            font-size: 10px !important;
            font-family: 'Mulish', sans-serif !important;
        }

        div[data-testid="stInfo"] {
            background: rgba(96,165,250,0.06) !important;
            border: 1px solid rgba(96,165,250,0.15) !important;
            border-radius: 14px !important;
        }

        /* === DIVIDER ST === */
        hr {
            border-color: rgba(255,255,255,0.05) !important;
            margin: 2rem 0 !important;
        }

        /* === SCROLLBAR === */
        ::-webkit-scrollbar { width: 3px; height: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.15); }

        /* === TOAST === */
        div[data-testid="stToast"] {
            background: rgba(15,20,40,0.95) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 14px !important;
            backdrop-filter: blur(20px) !important;
        }

        /* === RESPONSIVE MOBILE === */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.6rem !important;
                padding-right: 0.6rem !important;
            }
            .ride-main-name { font-size: 11px; }
            .ride-sub-status { font-size: 9.5px; }
            .wait-val { font-size: 16px; }
            .ride-row { gap: 5px; }
            .ride-left-card { padding: 9px 11px; border-radius: 14px; }
            .ride-right-wait { min-width: 56px; width: 56px; border-radius: 14px; }
            h1 { font-size: 1.5rem !important; }
            .state-pill { font-size: 6.5px; padding: 2px 6px; }
        }
    </style>
    """, unsafe_allow_html=True)
