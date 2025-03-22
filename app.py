import streamlit as st
from subtitle_search_engine import SubtitleProcessor
import pandas as pd

st.set_page_config(page_title="Subtitle Search Engine 🔍", layout="wide")

# Create header
st.title("📂 Subtitle Search Engine 🔍")

# Sidebar for database connection
st.sidebar.header("Database Connection")
db_path = st.sidebar.text_input("Database Path", value="data/eng_subtitles_database.db")

# Initialize processor with the specified database path
processor = SubtitleProcessor(db_path)

# Connect to Database button
if st.sidebar.button("Connect to Database"):
    if processor.connect_to_database():
        st.sidebar.success("✅ Connected to database")
    else:
        st.sidebar.error("❌ Failed to connect to database")

# Options section in sidebar
st.sidebar.header("Options")
sample_size = st.sidebar.slider("Sample size for testing (0 for all data)", 0, 1000, 100)

# Load sample data button
if st.sidebar.button("Load Sample Data"):
    with st.spinner("Loading sample data..."):
        sample_data = processor.load_sample_data(sample_size)
        if not sample_data.empty:
            st.dataframe(sample_data)
            st.success(f"Loaded {len(sample_data)} sample subtitle entries.")
        else:
            st.error("Failed to load sample data.")

# Add this in the sidebar section
st.sidebar.header("Database Connection")
db_path = st.sidebar.text_input("Database Path", value="data/eng_subtitles_database.db")

# Add file uploader as alternative
uploaded_db = st.sidebar.file_uploader("Or upload database file", type=['db'])
if uploaded_db is not None:
    # Save the uploaded file to a temporary location
    temp_db_path = "temp_database.db"
    with open(temp_db_path, "wb") as f:
        f.write(uploaded_db.getbuffer())
    db_path = temp_db_path
    st.sidebar.success(f"Database uploaded to {temp_db_path}")

# Main search interface
st.header("Search Subtitles")

# Search input
search_query = st.text_input("Enter your search query")
max_results = st.number_input("Max results", min_value=1, max_value=1000, value=100)

# Search button
if st.button("🔍 Search"):
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
