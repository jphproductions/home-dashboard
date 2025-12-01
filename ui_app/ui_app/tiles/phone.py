"""Phone tile for ringing Jamie's phone."""

import streamlit as st
import httpx


def render_tile(api_base_url: str):
    """
    Render phone tile with button to ring Jamie.
    
    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    
    if st.button("☎️ Ring Jamie's Phone", key="ring_phone", use_container_width=True):
        try:
            response = httpx.post(
                f"{api_base_url}/api/phone/ring",
                json={"message": "Ring from dashboard"},
                timeout=5.0,
            )
            response.raise_for_status()
            st.success("Ring request sent! 📱")
        except Exception as e:
            st.error(f"Failed to ring phone: {str(e)}")
