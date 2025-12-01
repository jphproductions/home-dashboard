"""Spotify tile for playback control."""

import streamlit as st
import httpx


@st.cache_data(ttl=5)  # Cache for 5 seconds to reduce API calls
def fetch_spotify_status(api_base_url: str) -> dict:
    """Fetch Spotify playback status from API with caching.

    Args:
        api_base_url: Base URL of FastAPI backend.

    Returns:
        Spotify status dictionary.

    Raises:
        Exception: If API call fails.
    """
    response = httpx.get(f"{api_base_url}/api/spotify/status", timeout=5.0)
    response.raise_for_status()
    return response.json()


def spotify_action(api_base_url: str, action: str):
    """Execute Spotify action (play, pause, next, previous).

    Args:
        api_base_url: Base URL of FastAPI backend.
        action: Action to perform (play, pause, next, previous).
    """
    try:
        httpx.post(f"{api_base_url}/api/spotify/{action}", timeout=5.0)
        # Clear cache to refresh status
        fetch_spotify_status.clear()
    except Exception as e:
        st.error(f"Action failed: {str(e)}")


def render_tile(api_base_url: str):
    """
    Render Spotify tile with playback controls and current track.

    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    try:
        data = fetch_spotify_status(api_base_url)

        # Current track info
        if data.get("track_name"):
            st.write(f"**Now Playing:**")
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
            st.button(
                "⏮️ Previous",
                key="spotify_prev",
                use_container_width=True,
                on_click=spotify_action,
                args=(api_base_url, "previous"),
            )

        with col2:
            if data.get("is_playing"):
                st.button(
                    "⏸️ Pause",
                    key="spotify_pause",
                    use_container_width=True,
                    on_click=spotify_action,
                    args=(api_base_url, "pause"),
                )
            else:
                st.button(
                    "▶️ Play",
                    key="spotify_play",
                    use_container_width=True,
                    on_click=spotify_action,
                    args=(api_base_url, "play"),
                )

        with col3:
            st.button(
                "⏭️ Next",
                key="spotify_next",
                use_container_width=True,
                on_click=spotify_action,
                args=(api_base_url, "next"),
            )

        with col4:
            if st.button("🔇 Mute", key="spotify_mute", use_container_width=True):
                st.info("Mute feature coming soon")

        # Wake TV & Play button
        if st.button("📺 Wake TV & Play", key="wake_tv_play", use_container_width=True):
            with st.status("Waking TV...", expanded=True) as status:
                try:
                    httpx.post(f"{api_base_url}/api/spotify/wake-and-play", timeout=10.0)
                    status.update(label="TV woken successfully!", state="complete")
                    fetch_spotify_status.clear()  # Clear cache to refresh
                except Exception as e:
                    status.update(label="Failed to wake TV", state="error")
                    st.error(f"Error: {str(e)}")

    except Exception as e:
        st.error(f"Failed to load Spotify: {str(e)}")
