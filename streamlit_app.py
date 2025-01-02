import os
import re
import json
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64

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

# Temporary download directory for server-side processing
TEMP_DOWNLOAD_DIR = "downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

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

# Function to create a downloadable link
def generate_download_link(file_path, file_name):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()  # Encode file to Base64
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📥 Click here to download {file_name}</a>'
    return href

# Download video using yt-dlp
if url:
    st.write("Fetching video details...")
    ydl_opts = {
        "outtmpl": os.path.join(TEMP_DOWNLOAD_DIR, "%(title)s.%(ext)s"),
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
                result = ydl.download([url])
                file_path = ydl.prepare_filename(info_dict)
                file_name = os.path.basename(file_path)
                st.success("Download complete!")
                st.markdown(generate_download_link(file_path, file_name), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
