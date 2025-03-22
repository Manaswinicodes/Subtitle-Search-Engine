import streamlit as st
from subtitle_search_engine import SubtitleProcessor
import pandas as pd
import os
from pathlib import Path

st.set_page_config(page_title="Subtitle Search Engine 🔍", layout="wide")

# Create header
st.title("📂 Subtitle Search Engine 🔍")

# Sidebar for database connection
st.sidebar.header("Database Connection")

# Use a key for this input to avoid duplicate ID errors
db_path = st.sidebar.text_input("Database Path", value="data/eng_subtitles_database.db", key="db_path_input")

# Add file uploader as alternative
uploaded_db = st.sidebar.file_uploader("Or upload database file", type=['db'], key="db_file_uploader")
if uploaded_db is not None:
    # Save the uploaded file to a temporary location
    temp_db_path = "temp_database.db"
    with open(temp_db_path, "wb") as f:
        f.write(uploaded_db.getbuffer())
    db_path = temp_db_path
    st.sidebar.success(f"Database uploaded to {temp_db_path}")

# Initialize processor with the specified database path
processor = SubtitleProcessor(db_path)

# Connect to Database button with a unique key
if st.sidebar.button("Connect to Database", key="connect_button"):
    conn = processor.connect_to_database()
    if conn:
        st.sidebar.success("✅ Connected to database")
        conn.close()  # Close the connection after testing
    else:
        st.sidebar.error("❌ Failed to connect to database")
        
        # Try to provide more diagnostic information
        if not os.path.exists(db_path):
            st.sidebar.error(f"Database file not found at: {db_path}")
            
            # Check alternative paths
            current_dir = Path.cwd()
            alt_paths = [
                current_dir / db_path,
                current_dir.parent / db_path,
                Path(db_path).absolute()
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    st.sidebar.info(f"Database found at: {path}")
                    st.sidebar.info("Try using this path instead")

# Options section in sidebar
st.sidebar.header("Options")
sample_size = st.sidebar.slider("Sample size for testing (0 for all data)", 0, 1000, 100, key="sample_slider")

# Load sample data button with a unique key
if st.sidebar.button("Load Sample Data", key="load_sample_button"):
    with st.spinner("Loading sample data..."):
        sample_data = processor.load_sample_data(sample_size)
        if not sample_data.empty:
            st.dataframe(sample_data)
            st.success(f"Loaded {len(sample_data)} sample subtitle entries.")
        else:
            st.error("Failed to load sample data.")

# Main search interface
st.header("Search Subtitles")

# Search input with a unique key
search_query = st.text_input("Enter your search query", key="search_query_input")
max_results = st.number_input("Max results", min_value=1, max_value=1000, value=100, key="max_results_input")

# Search button with a unique key
if st.button("🔍 Search", key="search_button"):
    if not search_query:
        st.warning("Please enter a search query")
    else:
        with st.spinner(f"Searching for '{search_query}'..."):
            results = processor.search_subtitles(search_query, max_results)
            
            if not results.empty:
                # Display results
                st.success(f"Found {len(results)} results")
                
                # Display each result with a link to opensubtitles.org
                for i, row in results.iterrows():
                    st.markdown(f"### {i+1}. {row['name']}")
                    st.markdown(f"[View on OpenSubtitles](https://www.opensubtitles.org/en/subtitles/{row['num']})")
                    
                    # Display content preview (first 200 chars)
                    try:
                        # Assuming content is stored in binary with latin-1 encoding
                        content = row['content'].decode('latin-1')[:200] + "..."
                        st.text(content)
                    except:
                        st.text("Unable to display content preview")
                    
                    st.markdown("---")
            else:
                st.info(f"No results found for '{search_query}'")

# Add information about the database
st.markdown("""
## About the Database
Database contains a sample of 82,498 subtitle files from opensubtitles.org.

Most of the subtitles are of movies and TV series released between 1990 and 2024.

**Database structure:**
- Table: 'zipfiles'
- Columns:
  1. num: Unique Subtitle ID for opensubtitles.org
  2. name: Subtitle File Name
  3. content: Compressed subtitle content stored as binary with 'latin-1' encoding
""")
