import os
import re
import json
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64

# Temporary download directory for server-side processing
TEMP_DOWNLOAD_DIR = "downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

# Custom CSS for a modern and responsive layout
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
        font-family: "Segoe UI", Tahoma, Geneva, sans-serif;
        margin: 0 auto;
        padding: 1rem;
    }
    .title {
        color: #007BFF;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #555555;
        font-size: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .btn-primary {
        background-color: #007BFF;
        color: white;
        padding: 10px 20px;
        font-size: 14px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 10px;
    }
    .btn-primary:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Quickly download YouTube videos and audio with ease.</div>', unsafe_allow_html=True)

# Input fields in a card layout
st.markdown('<div class="card">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    url = st.text_input("🔗 Enter YouTube URL:", placeholder="Paste YouTube video link here")

with col2:
    fetch_cookies = st.button("Fetch Cookies")

st.markdown('</div>', unsafe_allow_html=True)

# Fetch cookies dynamically
if fetch_cookies:
    def fetch_youtube_cookies():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.youtube.com")
            cookies = context.cookies()
            browser.close()
            return cookies

    try:
        cookies = fetch_youtube_cookies()
        with open("youtube_cookies.json", "w") as f:
            json.dump(cookies, f)
        st.success("Cookies fetched successfully.")
    except Exception as e:
        st.error(f"Failed to fetch cookies: {e}")

# Function to create a downloadable link
def generate_download_link(file_path, file_name):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" class="btn-primary">📥 Download {file_name}</a>'
    return href

if url:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Fetching video details...")

    try:
        ydl_opts = {
            "outtmpl": os.path.join(TEMP_DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "cookiefile": "youtube_cookies.json" if os.path.exists("youtube_cookies.json") else None,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            st.image(info_dict.get("thumbnail"), width=300)
            st.markdown(f"**Title:** {info_dict.get('title')}")
            st.markdown(f"**Uploader:** {info_dict.get('uploader')}")
            st.markdown(f"**Views:** {info_dict.get('view_count'):,}")

        # Download customization options
        format_options = st.radio("Choose Format:", ["Video", "Audio"], horizontal=True)

        if format_options == "Video":
            quality = st.selectbox("Quality:", ["Best", "Worst", "Custom"])
            if quality == "Custom":
                custom_format = st.text_input("Custom Format:", "bestvideo+bestaudio")
        else:
            audio_format = st.selectbox("Audio Format:", ["MP3", "AAC", "WAV", "FLAC"])
            audio_bitrate = st.slider("Bitrate (kbps):", 64, 320, 128)

        download_button = st.button("Download")

        if download_button:
            with st.spinner("Downloading..."):
                progress_bar = st.progress(0)

                if format_options == "Video":
                    if quality == "Custom":
                        ydl_opts["format"] = custom_format
                    else:
                        ydl_opts["format"] = "best" if quality == "Best" else "worst"
                else:
                    ydl_opts["format"] = "bestaudio"
                    ydl_opts["postprocessors"] = [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format.lower(),
                        "preferredquality": str(audio_bitrate),
                    }]

                def progress_hook(d):
                    if d["status"] == "downloading":
                        percent = re.sub(r'[^\d.]', '', d.get("_percent_str", "0"))
                        progress_bar.progress(min(int(float(percent)), 100))

                ydl_opts["progress_hooks"] = [progress_hook]

                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                        file_path = ydl.prepare_filename(info_dict)
                        file_name = os.path.basename(file_path)
                        st.success("Download complete!")
                        st.markdown(generate_download_link(file_path, file_name), unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Download failed: {e}")

    except Exception as e:
        st.error(f"Error fetching video details: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
