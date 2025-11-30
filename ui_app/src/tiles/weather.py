"""Weather tile for displaying current conditions."""

import streamlit as st
import httpx


def render_tile(api_base_url: str):
    """
    Render weather tile with current conditions and recommendation.
    
    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    try:
        response = httpx.get(f"{api_base_url}/api/weather/current", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Temperature", f"{data['temp']:.1f}°C", f"Feels like {data['feels_like']:.1f}°C")
        
        with col2:
            st.write(f"**Condition:** {data['condition']}")
            st.write(f"**Location:** {data['location']}")
            st.info(f"💡 {data['recommendation']}")
            
    except Exception as e:
        st.error(f"Failed to load weather: {str(e)}")
