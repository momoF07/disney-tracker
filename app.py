with col_help:
    with st.popover("❓"):
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
        st.markdown('<span class="cat-badge bg-blue">🎡 PARCS</span>', unsafe_allow_html=True)
        
        with st.container():
            c1, c2, c3 = st.columns(3)
            c1.code("*ALL"); c2.code("*DLP"); c3.code("*DAW")
            
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
            cl1, cl2 = st.columns(2); cl1.code(codes[0]); cl2.code(codes[1])
            st.markdown('</div>', unsafe_allow_html=True)
            
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
            for idx, code in enumerate(codes): cols_z[idx].code(code)
            st.markdown('</div>', unsafe_allow_html=True)

with col_sc:
    sc = st.text_input("Raccourci...", placeholder="ex: *FANTASY", label_visibility="collapsed")