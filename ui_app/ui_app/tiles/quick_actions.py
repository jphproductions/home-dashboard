"""Quick actions tile for links and shortcuts."""

import streamlit as st


def render_tile():
    """Render quick actions tile with placeholder links."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🍳 Recipes", key="recipes", use_container_width=True):
            st.info("Recipes link coming soon")
    
    with col2:
        if st.button("🚌 Transit", key="transit", use_container_width=True):
            st.info("Transit link coming soon")
    
    with col3:
        if st.button("📅 Calendar", key="calendar", use_container_width=True):
            st.info("Calendar link coming soon")

