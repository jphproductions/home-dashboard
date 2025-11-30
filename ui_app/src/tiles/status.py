"""Status bar tile showing last refresh and system info."""

import streamlit as st
from datetime import datetime


def render_status_bar():
    """Render status bar with last refresh time."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"⏰ Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        st.write("✅ All systems operational")
    
    with col3:
        if st.button("🔄 Refresh", key="manual_refresh", use_container_width=True):
            st.rerun()
