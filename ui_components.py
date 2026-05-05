# ui_components.py
import streamlit as st

def render_metric_row(meteo_data, park_hours, show_info):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(80, 114, 255, 0.3); text-align: center;">
                <p style="color: #64748b; margin-bottom: 5px; font-size: 0.9rem;">🌤️ Météo</p>
                <h2 style="margin: 0; color: #ffffff;">{meteo_data['temp']}°C</h2>
                <p style="color: #5072ff; margin: 0; font-size: 0.8rem;">{meteo_data['status']}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(80, 114, 255, 0.3); text-align: center;">
                <p style="color: #64748b; margin-bottom: 5px; font-size: 0.9rem;">🏰 Horaires</p>
                <h2 style="margin: 0; color: #ffffff;">{park_hours}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(80, 114, 255, 0.3); text-align: center;">
                <p style="color: #64748b; margin-bottom: 5px; font-size: 0.9rem;">🎭 Prochain Show</p>
                <h2 style="margin: 0; color: #ffffff; font-size: 1.2rem;">{show_info['name']}</h2>
                <p style="color: #5072ff; margin: 0; font-size: 0.9rem;">🕒 {show_info['time']}</p>
            </div>
        """, unsafe_allow_html=True)

def render_activity_item(time, event, ride, style):
    # Un flux d'activité plus "Neon"[cite: 1]
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 12px; 
                    border-left: 4px solid {style}; margin-bottom: 12px; transition: 0.3s;">
            <span style="color: #64748b; font-weight: bold;">{time}</span> | 
            <span style="color: {style}; font-weight: bold;">{event}</span> : 
            <span style="color: #ffffff;">{ride}</span>
        </div>
    """, unsafe_allow_html=True)