# Subtitle Search Engine

A powerful tool for searching and exploring a large database of movie and TV show subtitles.

## Features

- **Fast Search**: Search through 82,498+ subtitle files from movies and TV series
- **Context Display**: See the exact timestamps and dialogue where your search terms appear
- **Full Subtitle View**: View complete subtitles for any search result
- **User-Friendly Interface**: Easy-to-use web interface built with Streamlit

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/Subtitle-Search-Engine.git
   cd Subtitle-Search-Engine
   ```

2. Create a `data` directory and place the subtitle database file in it:
   ```
   mkdir -p data
   # Place eng_subtitles_database.db in the data directory
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

3. Connect to the database using the sidebar

4. Enter your search query and explore the results

## Database Information

The subtitle database contains:
- 82,498 subtitle files from opensubtitles.org
- Movies and TV series released between 1990 and 2024
- SQLite database with a 'zipfiles' table containing:
  - `num`: Unique Subtitle ID reference for www.opensubtitles.org
  - `name`: Subtitle File Name
  - `content`: Compressed subtitle files stored as binary using 'latin-1' encoding

## Deployment

This application can be deployed to various platforms:

### Streamlit Cloud

1. Push your code to GitHub
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy your app directly from your GitHub repository

### Local Server

1. Install required dependencies
2. Run `streamlit run app.py`
3. The app will be accessible on your local network

## License

This project is licensed under the terms of the LICENSE file included in this repository.

## Acknowledgments

- Data source: [OpenSubtitles.org](https://www.opensubtitles.org)
- Built with [Streamlit](https://streamlit.io/)
