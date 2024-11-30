import streamlit as st
st.set_page_config(
    page_title="Joshua Converts - YouTube Music Downloader",
    page_icon="🎵",
    layout="wide"
)

import os
import yt_dlp
import re
import unicodedata
from ytmusicapi import YTMusic

# Initialize YTMusic
ytmusic = YTMusic()

# Initialize session state
if 'selected_song' not in st.session_state:
    st.session_state.selected_song = None
if 'progress_text' not in st.session_state:
    st.session_state.progress_text = st.empty()
if 'speed_text' not in st.session_state:
    st.session_state.speed_text = st.empty()
if 'eta_text' not in st.session_state:
    st.session_state.eta_text = st.empty()
if 'download_complete' not in st.session_state:
    st.session_state.download_complete = False
if 'download_data' not in st.session_state:
    st.session_state.download_data = None

def sanitize_filename(title):
    """Remove invalid characters and normalize unicode characters"""
    title = unicodedata.normalize('NFKD', title)
    title = title.encode('ascii', 'ignore').decode()
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = re.sub(r'[\x00-\x1f]', '', title)
    title = title[:200]
    title = title.strip('. ')
    return title if title else 'audio'

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
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'calculating...')
            st.session_state.progress_text.text(f"Downloading: {percent}")
            
            if d.get('speed'):
                speed = float(d['speed']) / 1024 / 1024
                st.session_state.speed_text.text(f"Speed: {speed:.2f} MB/s")
            
            if d.get('eta'):
                eta = int(d['eta'])
                st.session_state.eta_text.text(f"ETA: {eta} seconds")
                
        elif d['status'] == 'finished':
            st.session_state.progress_text.text("Download finished. Converting to MP3...")
            st.session_state.speed_text.empty()
            st.session_state.eta_text.empty()
            
    except Exception as e:
        st.error(f"Progress update error: {str(e)}")

def convert_to_mp3(video_id, title):
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

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

        url = f"https://www.youtube.com/watch?v={video_id}"
        safe_title = sanitize_filename(title)
        output_path = f'downloads/{safe_title}'
        ydl_opts['outtmpl'] = {
            'default': output_path + '.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            output_file = f'{output_path}.mp3'
            
            if os.path.exists(output_file):
                return output_file, None
            else:
                return None, "Failed to create output file"

    except Exception as e:
        return None, f"Download error: {str(e)}"

def search_songs(query):
    """Search for songs using YTMusic API"""
    try:
        results = ytmusic.search(query, filter="songs", limit=10)
        return results
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def show_song_details(song):
    """Display song details in a card format"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.image(song['thumbnails'][0]['url'], width=160)
    
    with col2:
        st.markdown(f"### {song['title']}")
        st.markdown(f"**Artist:** {song['artists'][0]['name']}")
        if 'album' in song:
            st.markdown(f"**Album:** {song['album']['name']}")
        st.markdown(f"**Duration:** {format_duration(song['duration_seconds'] * 1000)}")

def embed_youtube_video(video_id):
    """Embed a YouTube video player"""
    embed_code = f'''
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
        <iframe src="https://www.youtube.com/embed/{video_id}" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
    </div>
    '''
    st.markdown(embed_code, unsafe_allow_html=True)

# Main UI
st.title("🎵 Joshua Converts")

# Show either search page or song details page
if st.session_state.selected_song:
    # Song details page
    st.markdown("## Selected Song")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_song_details(st.session_state.selected_song)
        embed_youtube_video(st.session_state.selected_song['videoId'])
    
    with col2:
        st.markdown("### Download Options")
        
        # Show download button only if download is not complete
        if not st.session_state.download_complete:
            if st.button("Start Download", use_container_width=True):
                with st.spinner("Converting..."):
                    output_file, error = convert_to_mp3(
                        st.session_state.selected_song['videoId'],
                        st.session_state.selected_song['title']
                    )
                    
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        with open(output_file, 'rb') as file:
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
                use_container_width=True
            )
        
        # Add back button
        if st.button("← Back to Search", use_container_width=True):
            st.session_state.selected_song = None
            st.session_state.download_complete = False
            st.session_state.download_data = None
            st.rerun()

else:
    # Search page
    search_query = st.text_input("Search for a song:", placeholder="Enter song name, artist, or album...")

    if search_query:
        results = search_songs(search_query)
        
        if results:
            st.markdown("### Search Results")
            
            for song in results:
                if song['resultType'] == 'song':  # Only show songs, not videos or playlists
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{song['title']}** - {song['artists'][0]['name']}")
                        
                        with col2:
                            st.markdown(f"Duration: {format_duration(song['duration_seconds'] * 1000)}")
                        
                        with col3:
                            if st.button("Select", key=song['videoId']):
                                st.session_state.selected_song = song
                                st.rerun()
                        
                        st.markdown("---") 