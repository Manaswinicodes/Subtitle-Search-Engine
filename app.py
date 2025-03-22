import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
import json
from subtitle_search_engine import SubtitleSearchEngine

st.set_page_config(
    page_title="Video Subtitle Search Engine",
    page_icon="🎬",
    layout="wide"
)

@st.cache_resource
def load_search_engine(data_path, model_type, sample_ratio):
    """Load and prepare the search engine (cached for performance)"""
    engine = SubtitleSearchEngine(data_path, model_type, sample_ratio)
    engine.load_data()
    engine.preprocess_data()
    engine.vectorize_documents()
    return engine

def main():
    st.title("Video Subtitle Search Engine")
    st.markdown("### Enhancing Search Engine Relevance for Video Subtitles")
    
    # Sidebar for configuration
    st.sidebar.title("Configuration")
    
    # Model selection
    model_type = st.sidebar.radio(
        "Search Engine Type",
        ("semantic", "keyword"),
        help="Semantic search understands context, keyword search matches exact terms"
    )
    
    # Data sampling for limited resources
    sample_ratio = st.sidebar.slider(
        "Data Sample Ratio", 
        min_value=0.1, 
        max_value=1.0, 
        value=0.3, 
        step=0.1,
        help="Use a smaller sample for faster processing (useful for limited resources)"
    )
    
    # Option to choose between uploaded file or specified data path
    data_source = st.sidebar.radio(
        "Data Source",
        ("Upload File", "Use Downloaded Data")
    )
    
    data_path = None
    
    if data_source == "Upload File":
        # File uploader for subtitle data
        uploaded_file = st.sidebar.file_uploader("Upload Subtitle Data", type=["csv", "json", "txt"])
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            file_extension = uploaded_file.name.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                data_path = tmp_file.name
    else:
        # Specify the path to the downloaded data
        data_folder = st.sidebar.text_input(
            "Path to data folder", 
            value="./data",
            help="Enter the path where you downloaded the subtitle data"
        )
        
        # Attempt to list files in the specified directory
        if os.path.exists(data_folder):
            try:
                files = [f for f in os.listdir(data_folder) 
                         if f.lower().endswith(('.csv', '.json', '.txt'))]
                
                if files:
                    selected_file = st.sidebar.selectbox("Select a file", files)
                    data_path = os.path.join(data_folder, selected_file)
                else:
                    st.sidebar.warning(f"No CSV, JSON, or TXT files found in {data_folder}")
            except Exception as e:
                st.sidebar.error(f"Error accessing directory: {str(e)}")
        else:
            st.sidebar.warning(f"Directory not found: {data_folder}")
            st.sidebar.info("Please create a 'data' folder in your project directory and place the downloaded subtitle data there.")
    
    if data_path and os.path.exists(data_path):
        try:
            # Initialize and load the search engine
            with st.spinner("Processing subtitle data..."):
                search_engine = load_search_engine(data_path, model_type, sample_ratio)
            
            st.success(f"Loaded subtitle data with {model_type} search engine")
            
            # Display data overview
            st.subheader("Data Overview")
            if hasattr(search_engine, 'subtitle_data'):
                st.write(f"Total documents: {len(search_engine.subtitle_data)}")
                if len(search_engine.subtitle_data) > 0:
                    st.write("Sample data:")
                    st.dataframe(search_engine.subtitle_data.head())
            
            # Search interface
            st.header("Search Subtitles")
            
            # Tabs for text and audio search
            tab1, tab2 = st.tabs(["Text Search", "Audio Search"])
            
            with tab1:
                # Text query input
                query = st.text_input("Enter your search query")
                search_button = st.button("Search")
                
                if search_button and query:
                    with st.spinner("Searching..."):
                        results = search_engine.search(query, top_k=5)
                    
                    if results:
                        st.subheader("Search Results")
                        for i, result in enumerate(results):
                            with st.expander(f"Result {i+1} - Score: {result['score']:.4f}"):
                                # Display document details
                                # Adapt this based on your actual data structure
                                st.json(result['document'])
                    else:
                        st.info("No results found. Try a different query.")
            
            with tab2:
                st.write("Upload a 2-minute audio recording for search")
                audio_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "ogg"])
                
                if audio_file is not None:
                    st.audio(audio_file)
                    
                    # Save the uploaded audio temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.'+audio_file.name.split('.')[-1]) as tmp_audio:
                        tmp_audio.write(audio_file.getvalue())
                        audio_path = tmp_audio.name
                    
                    audio_search_button = st.button("Search with Audio")
                    
                    if audio_search_button:
                        with st.spinner("Processing audio and searching..."):
                            # Process audio to text (placeholder)
                            transcribed_text = search_engine.process_audio_query(audio_path)
                            st.markdown("**Transcribed Query:**")
                            st.text(transcribed_text)
                            
                            # Search using the transcribed text
                            results = search_engine.search(transcribed_text, top_k=5)
                        
                        if results:
                            st.subheader("Search Results")
                            for i, result in enumerate(results):
                                with st.expander(f"Result {i+1} - Score: {result['score']:.4f}"):
                                    st.json(result['document'])
                        else:
                            st.info("No results found. Try a different audio query.")
                    
                    # Clean up the temporary audio file
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
        
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.info("Please make sure your data format matches the expected structure")
        
        # Clean up the temporary file if it was created
        finally:
            if data_source == "Upload File" and os.path.exists(data_path):
                os.unlink(data_path)
    
    else:
        st.info("Please select a data source to get started")
        
        # Show information about expected data
        st.subheader("Instructions")
        st.markdown("""
        ### How to use this application:
        
        1. **Download the subtitle data** from the provided Google Drive link
        2. **Create a 'data' folder** in your project directory
        3. **Extract and place** the subtitle data files in the 'data' folder
        4. **Select 'Use Downloaded Data'** in the sidebar and specify the path if needed
        5. **Choose a file** from the dropdown menu
        
        Alternatively, you can upload a file directly using the 'Upload File' option.
        """)

if __name__ == "__main__":
    main()
