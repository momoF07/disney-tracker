import streamlit as st
import streamlit.components.v1 as components
from datetime import time
from modules.emojis import get_rides_by_zone, RIDES_DLP, RIDES_DAW
from modules.special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE
from config import DLP_CLOSING, DAW_CLOSING

def render_quick_filters(options, all_pannes, heure_actuelle):
    """Affiche les boutons de raccourcis avec séparateurs de parcs"""
    
    # Injection du style pour les séparateurs textuels
    st.markdown("""
        <style>
            .park-divider {
                display: flex;
                align-items: center;
                text-align: center;
                margin: 25px 0 15px 0;
                color: #64748b;
            }
            .park-divider::before, .park-divider::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .park-divider:not(:empty)::before { margin-right: .75em; }
            .park-divider:not(:empty)::after { margin-left: .75em; }
            
            .park-name {
                font-size: 10px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #94a3b8;
            }
            .class-divider {
                display: flex;
                align-items: center;
                text-align: center;
                margin: 30px 0 15px 0;
                color: #64748b;
            }
            .class-divider::before, .park-divider::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .class-divider:not(:empty)::before { margin-right: .75em; }
            .class-divider:not(:empty)::after { margin-left: .75em; }
            
            .class-name {
                font-size: 13px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #94a3b8;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- SÉPARATEUR : ACCÈS RAPIDE ---
    st.markdown('<div class="class-divider"><span class="class-name">Accès Rapide</span></div>', unsafe_allow_html=True)

    st.write("")
    st.write("")

    # --- LIGNE 1 : FILTRES GLOBAUX & ÉTATS ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        if st.button("🌐 TOUT", key="btn_tout", use_container_width=True):
            st.query_params["fav"] = options
            st.rerun()
    with c2:
        if st.button("🏰 DLP", key="btn_dlp", use_container_width=True):
            st.query_params["fav"] = [r for r in options if r in RIDES_DLP]
            st.rerun()
    with c3:
        if st.button("🎬 DAW", key="btn_daw", use_container_width=True):
            st.query_params["fav"] = [r for r in options if r in RIDES_DAW]
            st.rerun()
    with c4:
        if st.button("⚠️ 101", key="btn_101", use_container_width=True):
            st.query_params["fav"] = [p['ride'] for p in all_pannes if p['statut'] == "EN_COURS"]
            st.rerun()
    with c5:
        if st.button("⏪ 102", key="btn_102", use_container_width=True):
            rides_with_incidents = list(set([p['ride'] for p in all_pannes]))
            st.query_params["fav"] = rides_with_incidents
            st.rerun()
    with c6:
        if st.button("🏁 FERMÉ", key="btn_ferme", use_container_width=True):
            closed_rides = []
            for r in options:
                is_daw_check = any(a.lower() in r.lower() for a in RIDES_DAW)
                if r in ANTICIPATED_CLOSINGS: h_f_check = ANTICIPATED_CLOSINGS[r]
                elif r in FANTASYLAND_EARLY_CLOSE: h_f_check = time(DLP_CLOSING.hour - 1, DLP_CLOSING.minute)
                else: h_f_check = DAW_CLOSING if is_daw_check else DLP_CLOSING
                if heure_actuelle >= h_f_check: closed_rides.append(r)
            st.query_params["fav"] = closed_rides
            st.rerun()

    # --- SÉPARATEUR : DISNEYLAND PARK ---
    st.markdown('<div class="park-divider"><span class="park-name">Disneyland Park</span></div>', unsafe_allow_html=True)

    c7, c8, c9, c10, c11 = st.columns(5)
    with c7:
        if st.button("🇺🇸 MS", key="btn_ms", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*MS", options, all_pannes)
            st.rerun()
    with c8:
        if st.button("🤠 FRONTIER", key="btn_frontier", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FRONTIER", options, all_pannes)
            st.rerun()
    with c9:
        if st.button("🏴‍☠️ ADVENTURE", key="btn_adventure", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*ADVENTURE", options, all_pannes)
            st.rerun()
    with c10:
        if st.button("🧚 FANTASY", key="btn_fantasy", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FANTASY", options, all_pannes)
            st.rerun()
    with c11:
        if st.button("🚀 DISCO", key="btn_disco", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*DISCO", options, all_pannes)
            st.rerun()

    # --- SÉPARATEUR : ADVENTURE WORLD ---
    st.markdown('<div class="park-divider"><span class="park-name">Disney Adventure World</span></div>', unsafe_allow_html=True)

    c12, c13, c14, c15, c16 = st.columns(5)
    with c12:
        if st.button("💥 CAMPUS", key="btn_campus", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*CAMPUS", options, all_pannes)
            st.rerun()
    with c13:
        if st.button("🧸 PIXAR", key="btn_pixar", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*PIXAR", options, all_pannes)
            st.rerun()
    with c14:
        if st.button("🎥 COURTYARD", key="btn_courtyard", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*COURTYARD", options, all_pannes)
            st.rerun()
    with c15:
        if st.button("❄️ FROZEN", key="btn_frozen", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FROZEN", options, all_pannes)
            st.rerun()
    with c16:
        if st.button("🌳 WAY", key="btn_way", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*WAY", options, all_pannes)
            st.rerun()

# --- SÉPARATEUR : Reset ---
    st.markdown('<div class="park-divider"><span class="park-name">Reset</span></div>', unsafe_allow_html=True)

    # --- BOUTON DE NETTOYAGE ---
    if st.button("🧹 VIDER LA SÉLECTION", key="btn_vider", use_container_width=True):
        st.query_params["fav"] = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    components.html("""
<script>
    function styleFilterButtons() {
        const colorMap = {
            // --- Disneyland Park global ---
            'DLP':       { border: '#a78bfa', glow: '#a78bfa' }, // Violet château

            // --- DAW global ---
            'DAW':       { border: '#fb923c', glow: '#fb923c' }, // Orange DAW général

            // --- Status ---
            '101':       { border: '#f87171', glow: '#f87171' },
            '102':       { border: '#f87171', glow: '#f87171' },
            'FERMÉ':     { border: '#f87171', glow: '#f87171' },

            // --- Disneyland Park : lands ---
            'MS':        { border: '#fcd34d', glow: '#fcd34d' }, // Jaune/crème Main Street USA années 1900
            'FRONTIER':  { border: '#c17f3a', glow: '#c17f3a' }, // Ocre terre Far West / Big Thunder
            'ADVENTURE': { border: '#4ade80', glow: '#4ade80' }, // Vert jungle tropicale
            'FANTASY':   { border: '#e879f9', glow: '#e879f9' }, // Rose/mauve château Sleeping Beauty
            'DISCO':     { border: '#fbbf24', glow: '#fbbf24' }, // Or bronze Jules Verne / rétro-futuriste

            // --- Disney Adventure World : zones ---
            'CAMPUS':    { border: '#f87171', glow: '#f87171' }, // Rouge Marvel Avengers
            'PIXAR':     { border: '#38bdf8', glow: '#38bdf8' }, // Bleu ciel Pixar / Nemo / Finding
            'COURTYARD': { border: '#d4ac0d', glow: '#d4ac0d' }, // Or Art Déco World Premiere Plaza
            'FROZEN':    { border: '#bae6fd', glow: '#bae6fd' }, // Bleu glacé Arendelle
            'WAY':       { border: '#86efac', glow: '#86efac' }, // Vert art nouveau Adventure Way
        };

        const doc = window.parent.document;
        doc.querySelectorAll('button').forEach(btn => {
            if (btn._styledV2) return;
            const text = btn.innerText.trim().toUpperCase();
            for (const [key, colors] of Object.entries(colorMap)) {
                if (text.includes(key)) {
                    btn._styledV2 = true;

                    // État normal : border subtil + teinte de fond légère
                    btn.style.setProperty('border', `1px solid ${colors.border}50`, 'important');
                    btn.style.setProperty('color', colors.border, 'important');
                    btn.style.setProperty('background', `${colors.border}0d`, 'important');
                    btn.style.setProperty('transition', 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)', 'important');

                    btn.addEventListener('mouseenter', () => {
                        btn.style.setProperty('border', `1px solid ${colors.border}cc`, 'important');
                        btn.style.setProperty('color', '#ffffff', 'important');
                        btn.style.setProperty('background', `${colors.border}25`, 'important');
                        btn.style.setProperty('box-shadow', 
                            `0 0 16px ${colors.border}40, 0 0 4px ${colors.border}30, inset 0 1px 0 ${colors.border}30`, 
                            'important');
                        btn.style.setProperty('transform', 'translateY(-2px) scale(1.02)', 'important');
                    });
                    btn.addEventListener('mouseleave', () => {
                        btn.style.setProperty('border', `1px solid ${colors.border}50`, 'important');
                        btn.style.setProperty('color', colors.border, 'important');
                        btn.style.setProperty('background', `${colors.border}0d`, 'important');
                        btn.style.setProperty('box-shadow', 'none', 'important');
                        btn.style.setProperty('transform', 'translateY(0) scale(1)', 'important');
                    });
                    break;
                }
            }
        });
    }

    setTimeout(styleFilterButtons, 500);
    setTimeout(styleFilterButtons, 1500);

    const observer = new MutationObserver(() => styleFilterButtons());
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
</script>
""", height=0)