import os
import sqlite3
import pandas as pd
import streamlit as st
from typing import Optional
from pathlib import Path

class SubtitleProcessor:
    """Class to process and search subtitle data from a SQLite database."""
    
    def __init__(self, db_path: str = "data/eng_subtitles_database.db"):
        """
        Initialize the SubtitleProcessor with a database path.
        
        Args:
            db_path: Path to the SQLite database containing subtitle data
        """
        # Try to find the database file in multiple locations
        self.db_path = db_path
        
    def connect_to_database(self):
        """Create a new SQLite connection with thread safety enabled."""
        try:
            # Try the direct path first
            if os.path.exists(self.db_path):
                st.sidebar.success(f"Found database at: {self.db_path}")
                return sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Try relative to the current directory
            current_dir = Path.cwd()
            alt_path = current_dir / self.db_path
            if os.path.exists(alt_path):
                st.sidebar.success(f"Found database at: {alt_path}")
                return sqlite3.connect(alt_path, check_same_thread=False)
            
            # Try parent directory
            parent_path = current_dir.parent / self.db_path
            if os.path.exists(parent_path):
                st.sidebar.success(f"Found database at: {parent_path}")
                return sqlite3.connect(parent_path, check_same_thread=False)
            
            # If we got here, we couldn't find the database
            st.sidebar.error(f"Database not found. Tried: {self.db_path}, {alt_path}, {parent_path}")
            return None
            
        except sqlite3.Error as e:
            st.sidebar.error(f"Error connecting to database: {e}")
            return None
            
    def search_subtitles(self, search_query: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search subtitles containing the query string.
        
        Args:
            search_query: Text to search for in subtitles
            max_results: Maximum number of results to return
            
        Returns:
            DataFrame with search results
        """
        # Create a new connection for this search operation
        conn = self.connect_to_database()
        if not conn:
            return pd.DataFrame()
            
        try:
            # Simple query to search inside the content column
            query = """
            SELECT num, name, content
            FROM zipfiles
            WHERE content LIKE ?
            LIMIT ?
            """
            # Use % wildcards to find the search text anywhere in content
            search_param = f"%{search_query}%"
            
            # Execute query and get results as DataFrame
            results = pd.read_sql_query(query, conn, params=(search_param, max_results))
            
            # Close the connection after use
            conn.close()
            
            return results
        except Exception as e:
            st.error(f"Error searching subtitles: {e}")
            conn.close()
            return pd.DataFrame()
    
    def load_sample_data(self, sample_size: int = 100) -> pd.DataFrame:
        """
        Load a sample of subtitle data for testing.
        
        Args:
            sample_size: Number of random subtitle entries to load
            
        Returns:
            DataFrame containing a sample of subtitle data
        """
        conn = self.connect_to_database()
        if not conn:
            return pd.DataFrame()
            
        try:
            query = f"SELECT num, name FROM zipfiles LIMIT {sample_size}"
            sample_df = pd.read_sql_query(query, conn)
            conn.close()
            return sample_df
        except Exception as e:
            st.error(f"Error loading sample data: {e}")
            conn.close()
            return pd.DataFrame()
