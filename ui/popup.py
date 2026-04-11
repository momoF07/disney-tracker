import streamlit as st

def render_shortcuts_popover():
    """Affiche le bouton popover avec l'index des codes magiques précis"""
    with st.popover("❓", help="Index des raccourcis"):
        # Injection du CSS spécifique pour les badges et boîtes
        st.markdown("""
        <style>
            .main-title { text-align: center; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 28px; margin-bottom: 25px; }
            .cat-badge { padding: 5px 15px; border-radius: 12px; font-size: 18px; font-weight: 600; letter-spacing: 1px; display: block; text-align: center; margin: 20px 0 10px 0; }
            .bg-blue { background: rgba(79, 172, 254, 0.15); color: #4facfe; border: 1px solid rgba(79, 172, 254, 0.3); }
            .bg-green { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
            .bg-orange { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
            .shortcut-box { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 10px; margin-bottom: 8px; }
            .shortcut-label { font-size: 15px; color: #94a3b8; text-transform: uppercase; margin-bottom: 5px; display: block; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<p class="main-title">🔍 INDEX DES CODES</p>', unsafe_allow_html=True)
        
        # --- SECTION PARCS ---
        st.markdown('<span class="cat-badge bg-blue">🎡 PARCS</span>', unsafe_allow_html=True)
        with st.container():
            c1, c2, c3 = st.columns(3)
            c1.code("*ALL"); c2.code("*DLP"); c3.code("*DAW")
            
        # --- SECTION DISNEYLAND PARK ---
        st.markdown('<span class="cat-badge bg-green">🏰 DISNEYLAND PARK</span>', unsafe_allow_html=True)
        lands_dlp_map = {
            "Main Street": ["*MS", "*MAINSTREET"], 
            "Frontierland": ["*FRONTIER", "*FRONTIERLAND"], 
            "Adventureland": ["*ADVENTURE", "*ADVENTURELAND"], 
            "Fantasyland": ["*FANTASY", "*FANTASYLAND"], 
            "Discoveryland": ["*DISCO", "*DISCOVERYLAND"]
        }
        
        for land, codes in lands_dlp_map.items():
            st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{land}</span>', unsafe_allow_html=True)
            cl1, cl2 = st.columns(2)
            cl1.code(codes[0])
            cl2.code(codes[1])
            st.markdown('</div>', unsafe_allow_html=True)
            
        # --- SECTION ADVENTURE WORLD ---
        st.markdown('<span class="cat-badge bg-orange">🎬 ADVENTURE WORLD</span>', unsafe_allow_html=True)
        shortcut_zones_daw = {
            "Avengers Campus": ["*CAMPUS", "*AVENGERS", "*AVENGERS-CAMPUS"], 
            "Production Courtyard": ["*COURTYARD", "PRODUCTION3", "*PROD3"], 
            "Worlds of Pixar": ["*WORLD-OF-PIXAR", "*PIXAR", "PRODUCTION4", "*PROD4"], 
            "World of Frozen": ["*WORLD-OF-FROZEN", "*FROZEN", "*WOF"], 
            "Adventure Way": ["*WAY", "*ADVENTURE-WAY"]
        }
        
        for zone, codes in shortcut_zones_daw.items():
            st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{zone}</span>', unsafe_allow_html=True)
            cols_z = st.columns(len(codes))
            for idx, code in enumerate(codes):
                cols_z[idx].code(code)
            st.markdown('</div>', unsafe_allow_html=True)

# ---
def render_history_expander(ride, rehab, h_p_clean, pannes_triees, est_en_retard_live, h_o, h_f, data_is_open):
    """Gère le contenu du menu déroulant Historique"""
    if rehab: 
        st.write("• 🛠️ :grey[**Maintenance en cours**]")
    elif h_p_clean or est_en_retard_live:
        if est_en_retard_live:
            st.write(f"• 🟣 :violet[**Ouverture retardée**] (Prévue à {h_o.strftime('%H:%M')})")
            st.caption("&nbsp;&nbsp;&nbsp;&nbsp;└ 🕒 En attente de mise en service")
        elif pannes_triees:
            p_actuelle = pannes_triees[0]
            h_d_act = p_actuelle['debut'].strftime('%H:%M')
            if not data_is_open:
                st.write(f"• 🟠 :orange[**En cours** depuis {h_d_act}]")
            else: 
                st.write(f"• 🟢 :green[**Opérationnel** à {p_actuelle['fin'].strftime('%H:%M')}]")
                if p_actuelle['debut'].time() <= h_o:
                    st.caption("&nbsp;&nbsp;&nbsp;&nbsp;└ 🟣 :violet[**Ouverture retardée**]")
                else:
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;└ 🔴 :red[**Panne** à {h_d_act}] ({p_actuelle['duree']} min)")

        if len(pannes_triees) > 1:
            for p in pannes_triees[1:]:
                h_d = p['debut'].strftime('%H:%M')
                if p['statut'] == "TERMINEE":
                    status_txt = "🟣 :violet[**Retard d'ouverture**]" if p['debut'].time() <= h_o else f"🔴 :red[**Panne à {h_d}**] ({p['duree']} min)"
                    st.caption(f"• 🟢 :green[**Ope à {p['fin'].strftime('%H:%M')}**] | {status_txt}")
    else: 
        st.write("✅ Aucun incident aujourd'hui.")