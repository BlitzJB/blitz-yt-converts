import streamlit as st
import os
import yt_dlp
import re
import unicodedata

def sanitize_filename(title):
    """Remove invalid characters and normalize unicode characters"""
    # Normalize unicode characters
    title = unicodedata.normalize('NFKD', title)
    # Convert to ASCII, ignoring non-ASCII characters
    title = title.encode('ascii', 'ignore').decode()
    # Remove invalid filename characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Remove or replace other problematic characters
    title = re.sub(r'[\x00-\x1f]', '', title)
    # Limit filename length
    title = title[:200]  # Limit to 200 characters
    # Remove leading/trailing spaces and dots
    title = title.strip('. ')
    # Replace empty string with default name
    return title if title else 'audio'

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes}:{remaining_seconds:02d}"

def my_hook(d):
    try:
        if d['status'] == 'downloading':
            # Get download progress
            percent = d.get('_percent_str', 'calculating...')
            progress_text.text(f"Downloading: {percent}")
            
            # Get download speed
            if d.get('speed'):
                speed = float(d['speed']) / 1024 / 1024  # Convert to MB/s
                speed_text.text(f"Speed: {speed:.2f} MB/s")
            
            # Get ETA
            if d.get('eta'):
                eta = int(d['eta'])
                eta_text.text(f"ETA: {eta} seconds")
                
        elif d['status'] == 'finished':
            progress_text.text("Download finished. Converting to MP3...")
            speed_text.empty()
            eta_text.empty()
            
        elif d['status'] == 'error':
            progress_text.text("Error occurred during download")
            
    except Exception as e:
        st.error(f"Progress update error: {str(e)}")

def convert_to_mp3(url):
    try:
        # Create downloads directory if it doesn't exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'progress_hooks': [my_hook],
            'outtmpl': {
                'default': 'downloads/%(title)s.%(ext)s',
            },
            'quiet': False,
            'no_warnings': True,
        }

        # First, get video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Get info first
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None, "Could not fetch video information"
                
                # Get basic video information
                title = str(info.get('title', 'video'))
                duration = int(info.get('duration', 0))
                
                # Show video info
                info_text.markdown(f"""
                **Video Information:**
                - Title: {title}
                - Duration: {format_duration(duration)}
                """)
                
                # Set output template with sanitized filename
                safe_title = sanitize_filename(title)
                if not safe_title:
                    safe_title = 'audio'
                
                output_path = f'downloads/{safe_title}'
                ydl_opts['outtmpl'] = {
                    'default': output_path + '.%(ext)s'
                }
                
                # Download and convert
                progress_text.text("Starting download...")
                ydl.download([url])
                
                # Check for output file
                output_file = f'{output_path}.mp3'
                if os.path.exists(output_file):
                    return output_file, None
                else:
                    return None, "Failed to create output file"
                
            except Exception as e:
                return None, f"Error during download: {str(e)}"
    except Exception as e:
        return None, f"Setup error: {str(e)}"

# Set page config
st.set_page_config(
    page_title="Joshua Converts - YouTube to MP3",
    page_icon="🎵",
    layout="centered"
)

# Main UI
st.title("🎵 Joshua Converts")
st.subheader("YouTube to MP3 Converter")

# URL input
url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

# Create placeholders for status updates
info_text = st.empty()
progress_text = st.empty()
speed_text = st.empty()
eta_text = st.empty()
download_button_placeholder = st.empty()

if st.button("Convert to MP3"):
    if url:
        try:
            # Clear previous status
            progress_text.empty()
            speed_text.empty()
            eta_text.empty()
            info_text.empty()
            download_button_placeholder.empty()
            
            output_file, error = convert_to_mp3(url)
            
            if error:
                st.error(f"Error: {error}")
            else:
                with open(output_file, 'rb') as file:
                    progress_text.success("Conversion Complete! Click below to download.")
                    download_button_placeholder.download_button(
                        label="Download MP3",
                        data=file,
                        file_name=os.path.basename(output_file),
                        mime="audio/mpeg"
                    )
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
    else:
        st.warning("Please enter a YouTube URL first!")

# Add some helpful information
st.markdown("---")
st.markdown("""
### Features:
- Downloads highest quality audio available
- Converts to 320kbps MP3 (maximum quality)
- Shows download progress and speed
- Supports most YouTube videos

### Tips:
- Make sure the YouTube video is publicly available
- For best quality, use official YouTube URLs
- Download may take a few moments depending on video length
""") 