# ui_components.py
import streamlit as st

def render_metric_row(meteo_data, park_hours, show_info):
    col1, col2, col3 = st.columns(3)
    col1.metric("Météo", f"{meteo_data['temp']}°C", delta=meteo_data['status'])
    col2.metric("Horaires", park_hours)
    col3.metric("Prochain Show", show_info['name'], delta=show_info['time'])

def render_activity_item(time, event, ride, style):
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; 
                    border-left: 15px solid {style}; margin-bottom: 10px;">
            <small style="color: #64748b;">{time}</small> | <b>{event}</b> : {ride}
        </div>
    """, unsafe_allow_html=True)