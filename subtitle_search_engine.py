import sqlite3
import pandas as pd
import zipfile
import io
import os
import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
import re
import time

class SubtitleProcessor:
    """Class to process and search subtitle data from a SQLite database."""
    
    def __init__(self, db_path: str = "data/eng_subtitles_database.db"):
        """
        Initialize the SubtitleProcessor with a database path.
        
        Args:
            db_path: Path to the SQLite database containing subtitle data
        """
        self.db_path = db_path
        self.conn = None
        self.df = None
        
    def connect_to_database(self) -> bool:
        """Connect to the SQLite database and return success status."""
        try:
            # Close any existing connection first
            if self.conn:
                self.conn.close()
                
            # Create a new connection
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            return True
        except sqlite3.Error as e:
            st.error(f"Error connecting to database: {e}")
            return False
            
       def load_subtitle_data(self, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load subtitle data from the database into a pandas DataFrame.
        
        Args:
            limit: Optional number of rows to load (for testing with smaller dataset)
        
        Returns:
            pandas DataFrame containing subtitle data or None if an error occurs
        """
        # Always create a fresh connection in the current thread
        if not self.connect_to_database():
            return None
                
        query = "SELECT * FROM zipfiles"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            self.df = pd.read_sql_query(query, self.conn)
            return self.df
        except pd.io.sql.DatabaseError as e:
            st.error(f"Error loading data from database: {e}")
            return None
    
    @staticmethod
    def extract_subtitle(binary_data: bytes) -> Optional[str]:
        """
        Extract subtitle content from compressed binary data.
        
        Args:
            binary_data: Compressed subtitle data in binary format
        
        Returns:
            Decoded subtitle text or None if extraction fails
        """
        try:
            with io.BytesIO(binary_data) as f:
                with zipfile.ZipFile(f, 'r') as zip_file:
                    # Get the first file in the archive (should be the subtitle file)
                    filename = zip_file.namelist()[0]
                    subtitle_content = zip_file.read(filename)
                    return subtitle_content.decode('latin-1')
        except (zipfile.BadZipFile, IndexError, UnicodeDecodeError, TypeError) as e:
            return None
    
    def search_subtitles(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for subtitles containing the query string.
        
        Args:
            query: The text to search for in subtitles
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing subtitle information and matching lines
        """
        if self.df is None:
            self.load_subtitle_data()
            if self.df is None:
                return []
                
        results = []
        count = 0
        
        # Use progress bar for processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_rows = len(self.df)
        for i, row in enumerate(self.df.itertuples()):
            # Update progress
            progress = min(i / total_rows, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Processing subtitle {i+1}/{total_rows}")
            
            # Extract subtitle content
            subtitle_text = self.extract_subtitle(row.content)
            if subtitle_text is None:
                continue
                
            # Search for query in subtitle text
            if query.lower() in subtitle_text.lower():
                # Find matching lines with timestamps
                matches = self.find_matching_lines(subtitle_text, query)
                
                # Add to results if matches found
                if matches:
                    results.append({
                        'subtitle_id': row.num,
                        'name': row.name,
                        'matches': matches,
                        'match_count': len(matches),
                        'url': f"https://www.opensubtitles.org/en/subtitles/{row.num}"
                    })
                    
                    count += 1
                    if count >= max_results:
                        break
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Sort results by number of matches (most relevant first)
        results.sort(key=lambda x: x['match_count'], reverse=True)
        return results
    
    @staticmethod
    def find_matching_lines(subtitle_text: str, query: str) -> List[Dict[str, str]]:
        """
        Find lines in subtitle text that match the query.
        
        Args:
            subtitle_text: The full subtitle text
            query: The search query
            
        Returns:
            List of dictionaries with timestamp and text for matching lines
        """
        matches = []
        
        # Split subtitle into blocks (typically timestamp + text)
        blocks = subtitle_text.split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
                
            # Look for timestamp line (typically the second line in a block)
            timestamp_line = None
            text_lines = []
            
            for i, line in enumerate(lines):
                if '-->' in line:
                    timestamp_line = line.strip()
                    # Text lines are the ones following the timestamp
                    text_lines = [l.strip() for l in lines[i+1:]]
                    break
            
            if not timestamp_line or not text_lines:
                continue
                
            # Join text lines into a single string for searching
            text = ' '.join(text_lines)
            
            # Check if query appears in the text
            if query.lower() in text.lower():
                matches.append({
                    'timestamp': timestamp_line,
                    'text': text
                })
                
        return matches
    
    def get_subtitle_by_id(self, subtitle_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a subtitle by its ID.
        
        Args:
            subtitle_id: The subtitle ID to retrieve
            
        Returns:
            Dictionary with subtitle information or None if not found
        """
        if self.df is None:
            self.load_subtitle_data()
            if self.df is None:
                return None
                
        # Find the subtitle with the given ID
        subtitle_row = self.df[self.df['num'] == subtitle_id]
        
        if len(subtitle_row) == 0:
            return None
            
        row = subtitle_row.iloc[0]
        subtitle_text = self.extract_subtitle(row['content'])
        
        if subtitle_text is None:
            return None
            
        return {
            'subtitle_id': row['num'],
            'name': row['name'],
            'text': subtitle_text,
            'url': f"https://www.opensubtitles.org/en/subtitles/{row['num']}"
        }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
