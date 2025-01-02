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

# Custom CSS for a better layout
st.markdown("""
    <style>
    body {
        background-color: #1E1E1E;
        color: #FFFFFF;
        font-family: "Segoe UI", Tahoma, Geneva, sans-serif;
        margin: 0;
    }
    .title {
        color: #4a90e2;
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .subtitle {
        color: #AAAAAA;
        font-size: 18px;
        text-align: center;
        margin-bottom: 30px;
    }
    .card {
        background: #2C2C2C;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .btn-primary {
        background-color: #4a90e2;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #0056b3;
    }
    .input-group {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .input-group input {
        flex: 1;
        padding: 10px;
        font-size: 16px;
        border: none;
        border-radius: 5px;
        margin-right: 10px;
    }
    .input-group button {
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        border-radius: 5px;
        background-color: #4a90e2;
        color: white;
        cursor: pointer;
    }
    .input-group button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="title">YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Quickly download YouTube videos or audio with ease.</div>', unsafe_allow_html=True)

# Input group for URL and fetch button
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="input-group">', unsafe_allow_html=True)

url = st.text_input("🔗 Enter YouTube URL:", "", placeholder="Paste your YouTube link here")
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

# Video details and download options
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

                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                        st.success("Download complete! Check your downloads folder.")
                except Exception as e:
                    st.error(f"Download failed: {e}")

    except Exception as e:
        st.error(f"Error fetching video details: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
