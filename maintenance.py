import streamlit as st

def show_maintenance():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Mulish:wght@300;400;500&display=swap');

        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 20% -10%, rgba(120,80,255,0.15) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,100,150,0.1) 0%, transparent 55%),
                radial-gradient(ellipse 100% 80% at 50% 50%, #090d1a 0%, #060910 100%);
        }

        .maint-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 75vh;
            font-family: 'Mulish', sans-serif;
        }

        .maint-card {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255,255,255,0.07);
            box-shadow:
                0 40px 80px rgba(0,0,0,0.6),
                0 1px 0 rgba(255,255,255,0.06) inset;
            padding: 3rem 3.5rem;
            border-radius: 28px;
            max-width: 480px;
            width: 100%;
            text-align: center;
        }

        .maint-emoji {
            font-size: 72px;
            line-height: 1;
            margin-bottom: 24px;
            filter: drop-shadow(0 0 30px rgba(196,181,253,0.4));
            animation: float 4s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50%       { transform: translateY(-10px); }
        }

        .maint-title {
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffd6e7 0%, #c4b5fd 40%, #7dd3fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }

        .maint-sub {
            color: #334155;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.7;
            margin-bottom: 32px;
        }

        .maint-divider {
            height: 1px;
            background: rgba(255,255,255,0.05);
            margin: 24px 0;
        }

        .maint-hint {
            color: #1e293b;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
            font-family: 'Outfit', sans-serif;
        }

        /* Champ password discret */
        div[data-baseweb="input"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 14px !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: rgba(196,181,253,0.3) !important;
            box-shadow: 0 0 0 3px rgba(196,181,253,0.08) !important;
        }

        input {
            text-align: center !important;
            color: rgba(255,255,255,0.25) !important;
            font-family: 'Outfit', sans-serif !important;
            letter-spacing: 4px !important;
        }

        input::placeholder { color: rgba(255,255,255,0.1) !important; }
    </style>

    <div class="maint-wrap">
        <div class="maint-card">
            <div class="maint-emoji">🏰</div>
            <div class="maint-title">Mise à jour en cours</div>
            <div class="maint-sub">
                Le Disney Tracker se refait une beauté.<br>
                Revenez dans quelques instants.
            </div>
            <div class="maint-divider"></div>
            <div class="maint-hint">Accès restreint</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        code = st.text_input(
            "Accès",
            type="password",
            label_visibility="collapsed",
            placeholder="· · · · · · ·",
            key="maint_password"
        )

    if code == "123456789":
        st.session_state.bypass_maintenance = True
        st.rerun()

    st.stop()