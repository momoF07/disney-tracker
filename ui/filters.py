import streamlit as st
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
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sort-container">', unsafe_allow_html=True)
    st.markdown('<p class="order-label">Accès Rapide</p>', unsafe_allow_html=True)

    # --- LIGNE 1 : FILTRES GLOBAUX & ÉTATS ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        if st.button("🌐 TOUT", use_container_width=True):
            st.query_params["fav"] = options
            st.rerun()
    with c2:
        if st.button("🏰 DLP", use_container_width=True):
            st.query_params["fav"] = [r for r in options if r in RIDES_DLP]
            st.rerun()
    with c3:
        if st.button("🎬 DAW", use_container_width=True):
            st.query_params["fav"] = [r for r in options if r in RIDES_DAW]
            st.rerun()
    with c4:
        if st.button("⚠️ 101", use_container_width=True, help="En panne actuellement"):
            st.query_params["fav"] = [p['ride'] for p in all_pannes if p['statut'] == "EN_COURS"]
            st.rerun()
    with c5:
        if st.button("⏪ 102", use_container_width=True, help="Historique des pannes"):
            rides_with_incidents = list(set([p['ride'] for p in all_pannes]))
            st.query_params["fav"] = rides_with_incidents
            st.rerun()
    with c6:
        if st.button("🏁 FERMÉ", use_container_width=True):
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
        if st.button("🇺🇸 MS", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*MS", options, all_pannes)
            st.rerun()
    with c8:
        if st.button("🤠 FRONTIER", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FRONTIER", options, all_pannes)
            st.rerun()
    with c9:
        if st.button("🏴‍☠️ ADVENTURE", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*ADVENTURE", options, all_pannes)
            st.rerun()
    with c10:
        if st.button("🧚 FANTASY", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FANTASY", options, all_pannes)
            st.rerun()
    with c11:
        if st.button("🚀 DISCO", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*DISCO", options, all_pannes)
            st.rerun()

    # --- SÉPARATEUR : ADVENTURE WORLD ---
    st.markdown('<div class="park-divider"><span class="park-name">Disney Adventure World</span></div>', unsafe_allow_html=True)

    c12, c13, c14, c15, c16 = st.columns(5)
    with c12:
        if st.button("💥 CAMPUS", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*CAMPUS", options, all_pannes)
            st.rerun()
    with c13:
        if st.button("🧸 PIXAR", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*PIXAR", options, all_pannes)
            st.rerun()
    with c14:
        if st.button("🎥 COURTYARD", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*COURTYARD", options, all_pannes)
            st.rerun()
    with c15:
        if st.button("❄️ FROZEN", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*FROZEN", options, all_pannes)
            st.rerun()
    with c16:
        if st.button("🌳 WAY", use_container_width=True):
            st.query_params["fav"] = get_rides_by_zone("*WAY", options, all_pannes)
            st.rerun()

    # --- BOUTON DE NETTOYAGE ---
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    if st.button("🧹 VIDER LA SÉLECTION", use_container_width=True):
        st.query_params["fav"] = []
        st.rerun()