import streamlit as st

st.set_page_config(
    page_title="Joshua Converts - YouTube Music Downloader",
    page_icon="🎵",
    layout="wide",
)

import os
import yt_dlp
import re
import unicodedata
from ytmusicapi import YTMusic

# Initialize YTMusic
ytmusic = YTMusic()

# Initialize session state
if "selected_song" not in st.session_state:
    st.session_state.selected_song = None
if "progress_text" not in st.session_state:
    st.session_state.progress_text = st.empty()
if "speed_text" not in st.session_state:
    st.session_state.speed_text = st.empty()
if "eta_text" not in st.session_state:
    st.session_state.eta_text = st.empty()
if "download_complete" not in st.session_state:
    st.session_state.download_complete = False
if "download_data" not in st.session_state:
    st.session_state.download_data = None

# Custom CSS
st.markdown(
    """
<style>
    .search-result {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .search-result:hover {
        background-color: #e6e9ef;
        transform: translateX(5px);
    }
    .song-title {
        font-size: 1.1em;
        font-weight: bold;
        margin: 0;
    }
    .song-artist {
        color: #666;
        font-size: 0.9em;
        margin: 0;
    }
    .song-duration {
        color: #666;
        font-size: 0.9em;
        margin: 0;
    }
    .album-image {
        border-radius: 5px;
        width: 60px;
        height: 60px;
        object-fit: cover;
    }
    .stButton button {
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    .ghost-button {
        background-color: transparent !important;
        border: 1px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }
    .ghost-button:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
    }
    .primary-button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }
    .primary-button:hover {
        background-color: #FF3333 !important;
        transform: translateY(-2px);
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    #MainMenu {
        display: none;
    }
    div[data-testid="stDecoration"] {
        display: none;
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    div[data-testid="stStatusWidget"] {
        display: none;
    }
    .clickable-card {
        cursor: pointer;
        text-decoration: none;
        color: inherit;
    }
    .clickable-card:hover {
        text-decoration: none;
        color: inherit;
    }
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def sanitize_filename(title):
    """Remove invalid characters and normalize unicode characters"""
    title = unicodedata.normalize("NFKD", title)
    title = title.encode("ascii", "ignore").decode()
    title = re.sub(r'[<>:"/\\|?*]', "", title)
    title = re.sub(r"[\x00-\x1f]", "", title)
    title = title[:200]
    title = title.strip(". ")
    return title if title else "audio"


def format_duration(milliseconds):
    """Format duration from milliseconds to MM:SS"""
    if not milliseconds:
        return "Unknown"
    seconds = milliseconds // 1000
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def my_hook(d):
    try:
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "calculating...")
            st.session_state.progress_text.text(f"Downloading: {percent}")

            if d.get("speed"):
                speed = float(d["speed"]) / 1024 / 1024
                st.session_state.speed_text.text(f"Speed: {speed:.2f} MB/s")

            if d.get("eta"):
                eta = int(d["eta"])
                st.session_state.eta_text.text(f"ETA: {eta} seconds")

        elif d["status"] == "finished":
            st.session_state.progress_text.text(
                "Download finished. Converting to MP3..."
            )
            st.session_state.speed_text.empty()
            st.session_state.eta_text.empty()

    except Exception as e:
        st.error(f"Progress update error: {str(e)}")


def convert_to_mp3(video_id, title):
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "progress_hooks": [my_hook],
            "outtmpl": {
                "default": "downloads/%(title)s.%(ext)s",
            },
            "quiet": False,
            "no_warnings": True,
        }

        url = f"https://www.youtube.com/watch?v={video_id}"
        safe_title = sanitize_filename(title)
        output_path = f"downloads/{safe_title}"
        ydl_opts["outtmpl"] = {"default": output_path + ".%(ext)s"}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            output_file = f"{output_path}.mp3"

            if os.path.exists(output_file):
                return output_file, None
            else:
                return None, "Failed to create output file"

    except Exception as e:
        return None, f"Download error: {str(e)}"


def search_songs(query):
    """Search for songs using YTMusic API"""
    try:
        results = ytmusic.search(query, limit=10)
        return results
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []


def show_song_details(song):
    """Display song details in a card format"""
    col1, col2 = st.columns([1, 3])

    with col1:
        st.image(song["thumbnails"][0]["url"], width=160)

    with col2:
        st.markdown(f"### {song['title']}")
        st.markdown(f"**Artist:** {song.get('artists', [{}])[0].get('name', '')}")
        if "album" in song:
            st.markdown(f"**Album:** {song.get('album', {}).get('name', '')}")
        st.markdown(
            f"**Duration:** {format_duration(song.get('duration_seconds', 0) * 1000)}"
        )


def embed_youtube_video(video_id):
    """Embed a YouTube video player"""
    embed_code = f"""
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
        <iframe src="https://www.youtube.com/embed/{video_id}" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
    </div>
    """
    st.markdown(embed_code, unsafe_allow_html=True)


# Main UI
# st.title("🎵 Joshua Converts")

# Show either search page or song details page
if st.session_state.selected_song:
    # Song details page
    st.markdown("## Selected Song")

    col1, col2 = st.columns([2, 1])

    with col1:
        show_song_details(st.session_state.selected_song)
        embed_youtube_video(st.session_state.selected_song["videoId"])

    with col2:
        st.markdown("### Download Options")

        # Show download button only if download is not complete
        if not st.session_state.download_complete:
            if st.button(
                "Start Download", use_container_width=True, key="download_btn"
            ):
                with st.spinner("Converting..."):
                    output_file, error = convert_to_mp3(
                        st.session_state.selected_song["videoId"],
                        st.session_state.selected_song["title"],
                    )

                    if error:
                        st.error(f"Error: {error}")
                    else:
                        with open(output_file, "rb") as file:
                            st.session_state.download_data = file.read()
                            st.session_state.download_complete = True
                            st.rerun()

        # Show download button after conversion is complete
        if st.session_state.download_complete and st.session_state.download_data:
            st.download_button(
                label="Download MP3",
                data=st.session_state.download_data,
                file_name=f"{sanitize_filename(st.session_state.selected_song['title'])}.mp3",
                mime="audio/mpeg",
                use_container_width=True,
                key="download_mp3_btn",
            )

        # Add back button with ghost style
        if st.button(
            " Back to Search",
            use_container_width=True,
            key="back_btn",
            type="secondary",
        ):
            st.session_state.selected_song = None
            st.session_state.download_complete = False
            st.session_state.download_data = None
            st.rerun()

else:
    # Search page
    # Center the search box
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_query = st.text_input(
            "",  # Remove label
            placeholder="Enter song name, artist, or album...",
            key="search_box",
        )

    if search_query:
        results = search_songs(search_query)

        if results:
            # Center the results
            with st.container():
                # Use enumerate to get unique index for each result
                for idx, song in enumerate(results):
                    # if song['resultType'] == 'song':
                    # Get the highest quality thumbnail
                    thumbnail_url = song["thumbnails"][-1]["url"]

                    # Create a container for each result
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col2:
                        st.markdown(
                            """
                                <style>
                                    .custom-card {
                                        padding: 15px 5px;
                                        margin-bottom: 10px;
                                        border-bottom: 1px solid #eee;
                                    }
                                    .button-container {
                                        margin-top: 10px;
                                    }
                                    .button-container button {
                                        width: 100%;
                                    }
                                </style>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Start the card
                        st.markdown('<div class="custom-card">', unsafe_allow_html=True)

                        # Song info
                        st.markdown(
                            f"""
                                <div style='display: flex; align-items: center;'>
                                    <img src='{thumbnail_url}' class='album-image'>
                                    <div style='margin-left: 15px; flex-grow: 1;'>
                                        <p class='song-title'>{song.get('title', '')}</p>
                                        <p class='song-artist'>{song.get('artists', [{}])[0].get('name', '')}</p>
                                    </div>
                                    <div style='text-align: right; margin-left: 15px;'>
                                        <p class='song-duration'>{format_duration(song.get('duration_seconds', 0) * 1000)}</p>
                                    </div>
                                </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Button container
                        st.markdown(
                            '<div class="button-container">', unsafe_allow_html=True
                        )
                        if st.button(
                            "Select",
                            key=f"select_{idx}_{song.get('videoId', '')}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            st.session_state.selected_song = song
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Close the card
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No results found. Try a different search term.")
