import os
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import re

# Set default download folder to the user's Downloads directory
DOWNLOAD_FOLDER = str(Path.home() / "Downloads")

# Custom CSS for a dynamic and modern look
st.markdown("""
    <style>
    .main {
        background-color: #f0f0f5;
        font-family: "Segoe UI", Tahoma, Geneva, sans-serif;
        padding: 1rem;
    }
    .title {
        color: #4a90e2;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .subtitle {
        color: #444444;
        font-size: 16px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .info-box {
        background-color: #e6f7ff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #b3d9ff;
        margin-bottom: 1.5rem;
    }
    .thumbnail {
        border-radius: 8px;
        margin-bottom: 1rem;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    .button {
        background-color: #4a90e2;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown('<div class="title">YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Download videos and audio effortlessly!</div>', unsafe_allow_html=True)

# Input URL and browser selection in a compact layout
col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input("🔗 Enter YouTube URL:")
with col2:
    browser_choice = st.selectbox(
        "🌐 Browser for Cookies:",
        ["chrome", "firefox", "chromium", "msedge", "opera", "safari", "yandex"],
        index=0,
        key="browser_select"
    )

video_info = None

if url:
    # Fetch video details
    with st.spinner("Fetching video details..."):
        try:
            with YoutubeDL({"quiet": True}) as ydl:
                video_info = ydl.extract_info(url, download=False)
        except Exception as e:
            st.error(f"❌ Error fetching video details: {e}")

    if video_info:
        # Display thumbnail and video details in columns
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(
                video_info.get("thumbnail"),
                caption="Thumbnail",
                use_container_width=True
            )

        with col2:
            st.markdown(f"**Title:** {video_info.get('title', 'N/A')}")
            st.markdown(f"**Uploader:** {video_info.get('uploader', 'N/A')}")
            st.markdown(f"**Duration:** {video_info.get('duration', 'N/A')} seconds")
            st.markdown(f"**Views:** {video_info.get('view_count', 'N/A'):,}")
            st.markdown(f"**Likes:** {video_info.get('like_count', 'N/A'):,}")

        # Format selection
        format_options = st.radio(
            "📁 Choose Format:",
            ["Video (Best Quality)", "Video (Smallest File)", "Audio Only"],
            horizontal=True,
            key="format_select"
        )

        # Start Download button
        download_button = st.button("💾 Start Download", key="download_button")

        if download_button:
            with st.spinner("🚀 Downloading..."):
                # Set up download options
                progress_bar = st.progress(0)

                ydl_opts = {
                    "cookiesfrombrowser": (browser_choice,),
                    "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
                }

                if format_options == "Video (Best Quality)":
                    ydl_opts.update({"format": "bestvideo+bestaudio/best"})
                elif format_options == "Video (Smallest File)":
                    ydl_opts.update({"format": "worst"})
                elif format_options == "Audio Only":
                    ydl_opts.update({
                        "format": "bestaudio",
                        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                    })

                def progress_hook(d):
                    if d["status"] == "downloading":
                        percent_str = re.sub(r'\x1b\[.*?m', '', d.get("_percent_str", "0.0%"))
                        try:
                            percent = float(percent_str.strip('%'))
                            progress_bar.progress(min(int(percent), 100))
                        except ValueError:
                            pass

                ydl_opts["progress_hooks"] = [progress_hook]

                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                        st.success("✅ Download complete! Your file is in the Downloads folder.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
