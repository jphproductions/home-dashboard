"""Spotify tile for playback control."""

import streamlit as st
import httpx


def render_tile(api_base_url: str):
    """
    Render Spotify tile with playback controls and current track.

    Args:
        api_base_url: Base URL of FastAPI backend.
    """
    try:
        response = httpx.get(f"{api_base_url}/api/spotify/status", timeout=5.0)
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
                httpx.post(f"{api_base_url}/api/spotify/previous", timeout=5.0)
                st.rerun()

        with col2:
            if data.get("is_playing"):
                if st.button("⏸️ Pause", key="spotify_pause", use_container_width=True):
                    httpx.post(f"{api_base_url}/api/spotify/pause", timeout=5.0)
                    st.rerun()
            else:
                if st.button("▶️ Play", key="spotify_play", use_container_width=True):
                    httpx.post(f"{api_base_url}/api/spotify/play", timeout=5.0)
                    st.rerun()

        with col3:
            if st.button("⏭️ Next", key="spotify_next", use_container_width=True):
                httpx.post(f"{api_base_url}/api/spotify/next", timeout=5.0)
                st.rerun()

        with col4:
            if st.button("🔇 Mute", key="spotify_mute", use_container_width=True):
                st.info("Mute feature coming soon")

        # Wake TV & Play button
        if st.button("📺 Wake TV & Play", key="wake_tv_play", use_container_width=True):
            try:
                httpx.post(f"{api_base_url}/api/tv/wake-and-play", timeout=10.0)
                st.success("TV woken and playback transferred!")
            except Exception as e:
                st.error(f"Failed to wake TV: {str(e)}")

    except Exception as e:
        st.error(f"Failed to load Spotify: {str(e)}")
