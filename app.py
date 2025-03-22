import streamlit as st
import pandas as pd
import os
import time
from subtitle_search_engine import SubtitleProcessor

# Set page configuration
st.set_page_config(
    page_title="Subtitle Search Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0066ff;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle-block {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .timestamp {
        color: #888;
        font-size: 0.9rem;
    }
    .highlight {
        background-color: yellow;
        padding: 0 2px;
    }
    .movie-title {
        font-weight: bold;
        font-size: 1.2rem;
        color: #1f77b4;
    }
    .result-count {
        font-style: italic;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'view_subtitle' not in st.session_state:
    st.session_state.view_subtitle = None

# Title
st.markdown("<h1 class='main-header'>🎬 Subtitle Search Engine 🔍</h1>", unsafe_allow_html=True)

# Sidebar for database connection
with st.sidebar:
    st.header("Database Connection")
    
    db_path = st.text_input("Database Path", value="data/eng_subtitles_database.db")
    
    if st.button("Connect to Database"):
        if os.path.exists(db_path):
            with st.spinner("Connecting to database..."):
                processor = SubtitleProcessor(db_path)
                if processor.connect_to_database():
                    st.session_state.processor = processor
                    st.session_state.db_connected = True
                    st.success("Connected to database successfully!")
                else:
                    st.error("Failed to connect to database.")
        else:
            st.error(f"Database file not found: {db_path}")
    
    if st.session_state.db_connected:
        st.success("✅ Connected to database")
        
        # Option to load sample for testing
        st.divider()
        st.subheader("Options")
        
        sample_size = st.number_input("Sample size for testing (0 for all data)", 
                                     min_value=0, max_value=1000, value=100, step=100)
        
        if st.button("Load Sample Data"):
            with st.spinner("Loading sample data..."):
                df = st.session_state.processor.load_subtitle_data(limit=sample_size if sample_size > 0 else None)
                if df is not None:
                    st.success(f"Loaded {len(df)} subtitle entries")

# Main content
if st.session_state.db_connected:
    # Search functionality
    st.subheader("Search Subtitles")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Enter your search query", placeholder="What are you looking for?")
    
    with col2:
        max_results = st.number_input("Max results", min_value=10, max_value=1000, value=100, step=10)
    
    if st.button("🔍 Search", type="primary"):
        if search_query:
            with st.spinner(f"Searching for '{search_query}'..."):
                start_time = time.time()
                results = st.session_state.processor.search_subtitles(search_query, max_results)
                search_time = time.time() - start_time
                
                st.session_state.search_results = results
                
                if results:
                    st.success(f"Found {len(results)} results in {search_time:.2f} seconds")
                else:
                    st.info("No results found.")
        else:
            st.warning("Please enter a search query.")
    
    # Display search results
    if st.session_state.search_results:
        st.subheader("Search Results")
        st.markdown(f"<p class='result-count'>Found {len(st.session_state.search_results)} subtitles containing your search term</p>", unsafe_allow_html=True)
        
        for i, result in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown(f"<div class='subtitle-block'>", unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"<p class='movie-title'>{i+1}. {result['name']}</p>", unsafe_allow_html=True)
                    st.markdown(f"ID: {result['subtitle_id']} | Matches: {result['match_count']}")
                
                with col2:
                    if st.button("View Full Subtitle", key=f"view_{i}"):
                        st.session_state.view_subtitle = result['subtitle_id']
                    
                    st.markdown(f"[View on OpenSubtitles]({result['url']})")
                
                # Show a few sample matches
                st.markdown("### Sample matches:")
                for j, match in enumerate(result['matches'][:3]):
                    st.markdown(f"<p><span class='timestamp'>{match['timestamp']}</span><br>{match['text']}</p>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
    # View full subtitle
    if st.session_state.view_subtitle:
        st.subheader("Full Subtitle View")
        
        subtitle = st.session_state.processor.get_subtitle_by_id(st.session_state.view_subtitle)
        
        if subtitle:
            st.markdown(f"<h3>{subtitle['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"ID: {subtitle['subtitle_id']} | [View on OpenSubtitles]({subtitle['url']})")
            
            with st.expander("Show Full Subtitle Text", expanded=True):
                st.text_area("Subtitle Content", value=subtitle['text'], height=400)
        else:
            st.warning("Subtitle not found.")
            
        if st.button("Back to Results"):
            st.session_state.view_subtitle = None
            st.experimental_rerun()
else:
    # Not connected to database
    st.info("Please connect to a subtitle database using the sidebar to get started.")
    
    with st.expander("About This Application"):
        st.write("""
        ## Subtitle Search Engine
        
        This application allows you to search through a large database of movie and TV show subtitles.
        
        ### Features:
        - Search through thousands of subtitle files
        - Find specific quotes or dialogue
        - View timestamps where the text appears
        - Access full subtitle content
        
        ### Getting Started:
        1. Connect to a subtitle database using the sidebar
        2. Enter a search query
        3. Browse through the results
        4. Click on "View Full Subtitle" to see the complete subtitle file
        
        ### Database Information:
        The database should be in SQLite format with a table called 'zipfiles' containing:
        - 'num': Unique Subtitle ID
        - 'name': Subtitle File Name
        - 'content': Compressed subtitle content in binary format, encoded using latin-1
        """)

# Footer
st.markdown("---")
st.markdown("Subtitle Search Engine | Data from OpenSubtitles.org")
