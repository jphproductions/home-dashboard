"""Main Streamlit application."""

import streamlit as st
from datetime import datetime
from ui_app.config import ui_settings
from ui_app.tiles import weather, spotify, quick_actions, phone, status

# Constants
API_BASE_URL = ui_settings.api_base_url

# Page configuration
st.set_page_config(
    page_title="Home Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Debug: Show API URL being used
print(f"[DEBUG] Using API_BASE_URL: {API_BASE_URL}")

# Initialize session state
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "fullscreen_mode" not in st.session_state:
    st.session_state.fullscreen_mode = None


def main():
    """Main dashboard layout."""

    st.title("🏠 Home Dashboard")
    st.markdown("---")

    # Create columns for tiles
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Weather")
        try:
            weather.render_tile(API_BASE_URL)
        except Exception as e:
            st.error(f"Weather tile error: {str(e)}")

    with col2:
        st.subheader("Spotify")
        try:
            spotify.render_tile(API_BASE_URL)
        except Exception as e:
            st.error(f"Spotify tile error: {str(e)}")

    # Second row
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Phone")
        try:
            phone.render_tile(API_BASE_URL)
        except Exception as e:
            st.error(f"Phone tile error: {str(e)}")

    with col4:
        st.subheader("Quick Actions")
        try:
            quick_actions.render_tile()
        except Exception as e:
            st.error(f"Quick actions error: {str(e)}")

    st.markdown("---")
    status.render_status_bar()


if __name__ == "__main__":
    main()
