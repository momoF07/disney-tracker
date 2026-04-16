import streamlit as st

def render_shortcuts_popover():
    """Affiche le bouton popover avec l'index des codes magiques précis"""
    with st.popover("✨", help="Index des raccourcis magiques"):
        st.markdown("""
        <style>
            /* Titre avec animation de dégradé */
            .main-title { 
                text-align: center; 
                background: linear-gradient(120deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%);
                background-size: 200% auto;
                -webkit-background-clip: text; 
                -webkit-text-fill-color: transparent; 
                font-weight: 900; 
                font-size: 30px; 
                margin-bottom: 20px;
                animation: shine 3s linear infinite;
            }
            @keyframes shine { to { background-position: 200% center; } }

            /* Badges de Catégories avec Glassmorphism */
            .cat-badge { 
                padding: 8px; 
                border-radius: 15px; 
                font-size: 14px; 
                font-weight: 800; 
                letter-spacing: 2px; 
                text-align: center; 
                margin: 25px 0 15px 0;
                text-transform: uppercase;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .bg-blue { background: rgba(79, 172, 254, 0.1); color: #4facfe; border: 1px solid #4facfe; }
            .bg-green { background: rgba(74, 222, 128, 0.1); color: #4ade80; border: 1px solid #4ade80; }
            .bg-orange { background: rgba(251, 191, 36, 0.1); color: #fbbf24; border: 1px solid #fbbf24; }

            /* Boîtes de raccourcis */
            .shortcut-box { 
                background: rgba(255, 255, 255, 0.02); 
                border-left: 3px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px; 
                padding: 12px; 
                margin-bottom: 12px;
                transition: transform 0.2s ease;
            }
            .shortcut-box:hover { transform: translateX(5px); background: rgba(255, 255, 255, 0.05); }
            .shortcut-label { font-size: 13px; color: #ffffff; font-weight: 600; margin-bottom: 8px; display: block; opacity: 0.8; }
            
            /* On override le style des blocs code de Streamlit dans la popup */
            div[data-testid="stMarkdownContainer"] code {
                color: #ffffff !important;
                background-color: rgba(255,255,255,0.1) !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
                font-family: 'Courier New', monospace !important;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<p class="main-title">MAGICAL INDEX</p>', unsafe_allow_html=True)
        
        # --- SECTION PARCS ---
        st.markdown('<div class="cat-badge bg-blue">🌐 GLOBAL SCOPE</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.code("*ALL"); c2.code("*DLP"); c3.code("*DAW")
            
        # --- SECTION DISNEYLAND PARK ---
        st.markdown('<div class="cat-badge bg-green">🏰 DISNEYLAND PARK</div>', unsafe_allow_html=True)
        lands_dlp_map = {
            "Main Street U.S.A": ["*MS", "*MAINSTREET"], 
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
        st.markdown('<div class="cat-badge bg-orange">🎬 ADVENTURE WORLD</div>', unsafe_allow_html=True)
        shortcut_zones_daw = {
            "Avengers Campus": ["*CAMPUS", "*AVENGERS"], 
            "Production Courtyard": ["*COURTYARD", "*PROD3"], 
            "Worlds of Pixar": ["*PIXAR", "*PROD4"], 
            "World of Frozen": ["*FROZEN", "*WOF"], 
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
    """Gère le contenu du menu déroulant Historique avec détection intelligente des retards"""
    
    marge_ouverture = 3 # Marge de tolérance en minutes
    
    if rehab: 
        st.write("• 🛠️ :grey[**Maintenance en cours**]")
        
    elif h_p_clean or est_en_retard_live:
        # --- 1. CAS DU RETARD EN COURS (LIVE) ---
        if est_en_retard_live:
            st.write(f"• 🟣 :violet[**Ouverture retardée**] (Prévue à {h_o.strftime('%H:%M')})")
            st.caption("&nbsp;&nbsp;&nbsp;&nbsp;└ 🕒 En attente de mise en service")
            
        # --- 2. ANALYSE DE L'HISTORIQUE ---
        elif pannes_triees:
            # On traite l'incident le plus récent (index 0)
            p_actuelle = pannes_triees[0]
            h_d_act = p_actuelle['debut'].strftime('%H:%M')
            
            # Calcul pour savoir si c'est un vrai retard (Ouverture après h_o + marge)
            # On utilise .replace pour ajouter la marge à h_o
            h_limite = (datetime.combine(datetime.today(), h_o) + timedelta(minutes=marge_ouverture)).time()
            
            if not data_is_open:
                # Si l'attraction est fermée actuellement
                st.write(f"• 🟠 :orange[**En cours** depuis {h_d_act}]")
            else: 
                # Si elle est ouverte, on vérifie si l'ouverture était un retard ou une panne
                st.write(f"• 🟢 :green[**Opérationnel** à {p_actuelle['fin'].strftime('%H:%M')}]")
                
                # C'est un retard si : début avant l'heure prévue ET fin après l'heure limite
                vrai_retard = (p_actuelle['debut'].time() <= h_o) and (p_actuelle['fin'].time() > h_limite)
                
                if vrai_retard:
                    st.caption("&nbsp;&nbsp;&nbsp;&nbsp;└ 🟣 :violet[**Ouverture retardée**]")
                elif p_actuelle['debut'].time() > h_o:
                    # C'est une panne classique car elle a eu lieu après l'heure d'ouverture
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;└ 🔴 :red[**Panne** à {h_d_act}] ({p_actuelle['duree']} min)")

            # --- 3. AFFICHAGE DU RESTE DE L'HISTORIQUE ---
            if len(pannes_triees) > 1:
                for p in pannes_triees[1:]:
                    if p['statut'] == "TERMINEE":
                        h_d = p['debut'].strftime('%H:%M')
                        h_f_p = p['fin'].strftime('%H:%M')
                        
                        # Vérification retard pour les lignes précédentes
                        vrai_retard_hist = (p['debut'].time() <= h_o) and (p['fin'].time() > h_limite)
                        
                        if vrai_retard_hist:
                            status_txt = "🟣 :violet[**Retard d'ouverture**]"
                        else:
                            status_txt = f"🔴 :red[**Panne à {h_d}**] ({p['duree']} min)"
                            
                        st.caption(f"• 🟢 :green[**Ope à {h_f_p}**] | {status_txt}")
    else: 
        st.write("✅ Aucun incident aujourd'hui.")