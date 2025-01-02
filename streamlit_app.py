import os
import re
import json
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64
import tempfile

# Temporary download directory for server-side processing -- Safe temporary directory
TEMP_DOWNLOAD_DIR = tempfile.mkdtemp()

# Custom CSS for compact layout
st.markdown("""
    <style>
    body {
        background-color: #1E1E1E;
        color: #FFFFFF;
        font-family: "Segoe UI", Tahoma, Geneva, sans-serif;
    }
    .title {
        color: #4a90e2;
        font-size: 30px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #AAAAAA;
        font-size: 16px;
        text-align: center;
        margin-bottom: 20px;
    }
    .card {
        # background: #2C2C2C;
        padding: 5px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 10px;
    }
    .btn-primary {
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 5px;
        font-size: 14px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #0056b3;
    }
    .compact-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown('<div class="title">YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Download YouTube videos and audio with your preferred settings.</div>', unsafe_allow_html=True)

# Input URL and fetch cookies button
url = st.text_input("🔗 YouTube URL:", placeholder="Paste your YouTube link here")

st.markdown('<div class="card compact-row">', unsafe_allow_html=True)
st.write("In case of Authentication Errors, Click on button below to fetch cookies")
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

# Generate a downloadable link for the client
# Generate a direct downloadable link for the client
def generate_download_link(file_path, file_name):
    href = f'📥 Click here to download <a href="file/{file_path}" download="{file_name}" class="btn-primary">📥 Click here to download {file_name}</a>'
    return href

# Display video details and customization options in a compact layout
if url:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    try:
        ydl_opts = {
            "outtmpl": os.path.join(TEMP_DOWNLOAD_DIR, "%(title).200s.%(ext)s"),
            "cookiefile": "youtube_cookies.json" if os.path.exists("youtube_cookies.json") else None,
        }

        # Debugging: Show the download path
        st.write(f"Downloading to: {TEMP_DOWNLOAD_DIR}")

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Display thumbnail and details side by side
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(info_dict.get("thumbnail"), width=150)
        with col2:
            st.markdown(f"**Title:** {info_dict.get('title')}")
            st.markdown(f"**Uploader:** {info_dict.get('uploader')}")
            st.markdown(f"**Views:** {info_dict.get('view_count'):,}")
            st.markdown(f"**Duration:** {info_dict.get('duration') // 60} minutes")

        # Format selection options
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            format_options = st.radio("Format:", ["Video", "Audio"], horizontal=True)
        with col2:
            if format_options == "Video":
                video_quality = st.selectbox("Quality:", ["Best", "Worst", "Custom"])
                if video_quality == "Custom":
                    custom_format = st.text_input("Custom Format:", "bestvideo+bestaudio")
            else:
                audio_format = st.selectbox("Audio Format:", ["MP3", "AAC", "WAV", "FLAC"])
                audio_bitrate = st.slider("Bitrate (kbps):", 64, 320, 128, step=32)

        # Download button
        if st.button("Generate Download Link"):
            with st.spinner("Generating Link..."):
                progress_bar = st.progress(0)  # Initialize progress bar
                progress_text = st.empty()  # Placeholder for progress text

                # Custom HTML for better progress display
                progress_html = st.empty()  # Placeholder for styled progress
                progress_details = st.empty()  # Placeholder for download details

                # Update ydl_opts based on user settings
                if format_options == "Video":
                    if video_quality == "Custom":
                        ydl_opts["format"] = custom_format
                    else:
                        ydl_opts["format"] = "best" if video_quality == "Best" else "worst"
                else:
                    ydl_opts["format"] = "bestaudio"
                    ydl_opts["postprocessors"] = [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format.lower(),
                        "preferredquality": str(audio_bitrate),
                    }]

                # Enhanced Progress Hook
                def progress_hook(d):
                    if d["status"] == "downloading":
                        percent_str = d.get("_percent_str", "0.0%").strip()
                        percent = float(re.sub(r'[^\d.]', '', percent_str))  # Extract percentage
                        speed = d.get("_speed_str", "N/A")  # Current download speed
                        downloaded = d.get("downloaded_bytes", 0) / (1024 * 1024)  # Bytes to MB
                        total_size = d.get("total_bytes", 0) / (1024 * 1024) if d.get("total_bytes") else None  # Total size

                        # Update progress bar
                        progress_bar.progress(min(int(percent), 100))

                        # Update HTML-styled progress details
                        if total_size:
                            progress_details.markdown(
                                f"""
                                <div style="color: #4a90e2; font-size: 16px; text-align: center; margin-top: 10px;">
                                    <b>Progress:</b> {percent:.2f}%<br>
                                    <b>Speed:</b> {speed}<br>
                                    <b>Downloaded:</b> {downloaded:.2f} MB / {total_size:.2f} MB
                                </div>
                                """, unsafe_allow_html=True
                            )
                        else:
                            progress_details.markdown(
                                f"""
                                <div style="color: #4a90e2; font-size: 16px; text-align: center; margin-top: 10px;">
                                    <b>Progress:</b> {percent:.2f}%<br>
                                    <b>Speed:</b> {speed}<br>
                                    <b>Downloaded:</b> {downloaded:.2f} MB
                                </div>
                                """, unsafe_allow_html=True
                            )

                ydl_opts["progress_hooks"] = [progress_hook]

                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        # Download and process the video
                        info_dict = ydl.extract_info(url, download=True)
                        final_file_path = ydl.prepare_filename(info_dict)

                        # If postprocessors are applied (e.g., audio extraction), adjust the file name
                        if "postprocessors" in ydl_opts and format_options == "Audio":
                            final_file_path = re.sub(r"\.webm|\.m4a|\.mp4", f".{audio_format.lower()}", final_file_path)

                        file_name = os.path.basename(final_file_path)

                        st.success("Link Generated Successfully!")

                        # Serve the file using st.download_button
                        with open(final_file_path, "rb") as file:
                            file_data = file.read()
                            st.download_button(
                                label="📥 Click here to download your file",
                                data=file_data,
                                file_name=file_name,
                                mime="application/octet-stream",
                            )
                except Exception as e:
                    st.error(f"Download failed: {e}")

    except Exception as e:
        st.error(f"Error fetching video details: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
