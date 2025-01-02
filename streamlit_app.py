import os
import re
import json
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
from playwright.sync_api import sync_playwright

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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Download videos and audio effortlessly!</div>', unsafe_allow_html=True)

# Input URL
url = st.text_input("🔗 Enter YouTube URL:")

# Playwright function for fetching cookies
def fetch_youtube_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless browser
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.youtube.com")
        st.warning("If login is required, automate or manually paste cookies in the hosted app.")
        cookies = context.cookies()
        browser.close()
        return cookies

# Fetch cookies dynamically
if st.button("Fetch YouTube Cookies"):
    try:
        cookies = fetch_youtube_cookies()
        with open("youtube_cookies.json", "w") as f:
            json.dump(cookies, f)
        st.success("YouTube cookies fetched successfully.")
    except Exception as e:
        st.error(f"Error fetching cookies: {e}")

# Download video using yt-dlp
if url:
    st.write("Fetching video details...")
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "cookiefile": "youtube_cookies.json" if os.path.exists("youtube_cookies.json") else None,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            st.image(info_dict.get("thumbnail"))
            st.markdown(f"**Title:** {info_dict.get('title')}")
            st.markdown(f"**Uploader:** {info_dict.get('uploader')}")
            st.markdown(f"**Views:** {info_dict.get('view_count'):,}")
        if st.button("Download"):
            with st.spinner("Downloading..."):
                ydl.download([url])
                st.success("Download complete!")
    except Exception as e:
        st.error(f"Error: {e}")
