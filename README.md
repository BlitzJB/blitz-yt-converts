# Joshua Converts

A simple Streamlit web application that converts YouTube videos to MP3 format.

## Features

- Convert YouTube videos to MP3 format
- High-quality audio (320kbps)
- Simple and intuitive user interface
- Direct download of converted files
- Real-time progress tracking

## Local Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

3. Run the Streamlit app:
```bash
streamlit run app.py
```

4. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

## Deployment on Streamlit Cloud

1. Fork this repository to your GitHub account

2. Log in to [Streamlit Cloud](https://streamlit.io/cloud)

3. Create a new app and select your forked repository

4. Deploy! Streamlit Cloud will automatically:
   - Install FFmpeg from packages.txt
   - Install Python dependencies from requirements.txt
   - Start your app

## Usage

1. Paste a YouTube video URL into the input field
2. Click "Convert to MP3"
3. Wait for the conversion to complete
4. Click the "Download MP3" button to save your file

## Requirements

- Python 3.7+
- streamlit
- yt-dlp
- FFmpeg

## File Structure

```
joshua-converts/
├── app.py              # Main application code
├── requirements.txt    # Python dependencies
├── packages.txt       # System dependencies (FFmpeg)
├── .streamlit/        # Streamlit configuration
│   └── config.toml
└── README.md          # Documentation
```

## Note

This app is for personal use only. Please respect YouTube's terms of service and copyright laws when using this application. 