"""Spotify tile for playback control."""

import streamlit as st
import httpx


def render_tile(api_base_url: str):
    """
    Render Spotify tile with playback controls and current track.

    Shows authentication button if not authenticated, otherwise shows playback controls.

    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    # Check authentication status
    try:
        # Use trust_env=False to bypass proxy for localhost
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            auth_response = client.get(f"{api_base_url}/api/spotify/auth/status")
            is_authenticated = auth_response.json().get("authenticated", False)
    except Exception:
        is_authenticated = False

    if not is_authenticated:
        # Show authentication button
        st.write("**Spotify Not Connected**")
        st.write("Connect your Spotify account to control playback.")

        auth_url = f"{api_base_url}/api/spotify/auth/login"

        # Direct link (will redirect in same window)
        st.markdown(
            f"""
            <a href="{auth_url}" style="text-decoration: none;">
                <button style="
                    width: 100%;
                    padding: 0.5rem 1rem;
                    background-color: #1DB954;
                    color: white;
                    border: none;
                    border-radius: 0.5rem;
                    font-size: 1rem;
                    cursor: pointer;
                ">
                    🔗 Authenticate Spotify
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.caption("You'll be redirected to Spotify, then automatically back to this dashboard.")

        return

    # Show playback controls if authenticated
    try:
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            response = client.get(f"{api_base_url}/api/spotify/status")
            response.raise_for_status()
            data = response.json()

        # Current track info
        if data.get("track_name"):
            st.write("**Now Playing:**")
            st.write(f"🎵 {data['track_name']}")
            if data.get("artist_name"):
                st.write(f"👤 {data['artist_name']}")
            if data.get("device_name"):
                st.write(f"📱 {data['device_name']}")
        else:
            st.write("Nothing currently playing")

        # Playback controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("⏮️ Previous", key="spotify_prev", use_container_width=True):
                with httpx.Client(timeout=5.0, trust_env=False) as client:
                    client.post(f"{api_base_url}/api/spotify/previous")
                st.rerun()

        with col2:
            if data.get("is_playing"):
                if st.button("⏸️ Pause", key="spotify_pause", use_container_width=True):
                    with httpx.Client(timeout=5.0, trust_env=False) as client:
                        client.post(f"{api_base_url}/api/spotify/pause")
                    st.rerun()
            else:
                if st.button("▶️ Play", key="spotify_play", use_container_width=True):
                    with httpx.Client(timeout=5.0, trust_env=False) as client:
                        client.post(f"{api_base_url}/api/spotify/play")
                    st.rerun()

        with col3:
            if st.button("⏭️ Next", key="spotify_next", use_container_width=True):
                with httpx.Client(timeout=5.0, trust_env=False) as client:
                    client.post(f"{api_base_url}/api/spotify/next")
                st.rerun()

        with col4:
            if st.button("🔇 Mute", key="spotify_mute", use_container_width=True):
                st.info("Mute feature coming soon")

        # Wake TV & Play button
        if st.button("📺 Wake TV & Play", key="wake_tv_play", use_container_width=True):
            try:
                with httpx.Client(timeout=10.0, trust_env=False) as client:
                    client.post(f"{api_base_url}/api/spotify/wake-and-play")
                st.success("TV woken and playback transferred!")
            except Exception as e:
                st.error(f"Failed to wake TV: {str(e)}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 500 and "No refresh token" in e.response.text:
            st.error("Authentication expired. Please re-authenticate.")
            if st.button("🔗 Re-authenticate", key="spotify_reauth", use_container_width=True):
                auth_url = f"{api_base_url}/api/spotify/auth/login"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        else:
            st.error(f"Failed to load Spotify: {str(e)}")
    except Exception as e:
        st.error(f"Failed to load Spotify: {str(e)}")
