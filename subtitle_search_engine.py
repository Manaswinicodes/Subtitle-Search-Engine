import sqlite3
import pandas as pd
import zipfile
import io
import os
import re
from typing import List, Dict, Tuple, Optional, Union
import time

class SubtitleProcessor:
    """
    Class to handle processing of subtitle data from the database.
    Provides functionality to extract, decode, and search through subtitle content.
    """
    
    def __init__(self, db_path: str = "data/eng_subtitles_database.db"):
        """
        Initialize the SubtitleProcessor with the path to the subtitle database.
        
        Args:
            db_path: Path to the SQLite database containing subtitle data
        """
        self.db_path = db_path
        self.conn = None
        self.df = None
        
    def connect_to_database(self) -> bool:
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Successfully connected to database at {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def load_subtitle_data(self, limit: Optional[int] = None) -> bool:
        """
        Load subtitle data from the database into a pandas DataFrame.
        
        Args:
            limit: Optional number of rows to load (for testing)
            
        Returns:
            Boolean indicating success or failure
        """
        if not self.conn:
            if not self.connect_to_database():
                return False
        
        query = "SELECT * FROM zipfiles"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            self.df = pd.read_sql_query(query, self.conn)
            print(f"Loaded {len(self.df)} subtitle entries")
            return True
        except pd.io.sql.DatabaseError as e:
            print(f"Error loading data from database: {e}")
            return False
    
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
            # Return None for failed extractions instead of crashing
            return None
    
    def process_subtitles(self, batch_size: int = 1000) -> bool:
        """
        Process subtitles in batches with progress tracking.
        
        Args:
            batch_size: Number of subtitles to process in each batch
        
        Returns:
            Boolean indicating success or failure
        """
        if self.df is None:
            print("No data loaded. Call load_subtitle_data first.")
            return False
        
        total_rows = len(self.df)
        success_count = 0
        
        # Create a column for the processed subtitle text
        self.df['subtitle_text'] = None
        
        start_time = time.time()
        
        for i in range(0, total_rows, batch_size):
            batch_start = time.time()
            end_idx = min(i + batch_size, total_rows)
            batch = self.df.iloc[i:end_idx]
            
            # Process batch
            print(f"Processing batch {i//batch_size + 1}/{(total_rows-1)//batch_size + 1}...")
            batch_results = [self.extract_subtitle(data) for data in batch['content']]
            self.df.loc[i:end_idx-1, 'subtitle_text'] = batch_results
            
            # Count successful extractions
            successful = sum(1 for result in batch_results if result is not None)
            success_count += successful
            
            # Print progress
            batch_time = time.time() - batch_start
            print(f"Processed {end_idx}/{total_rows} subtitles "
                  f"({successful}/{len(batch_results)} successful in this batch, "
                  f"{batch_time:.2f} seconds)")
        
        total_time = time.time() - start_time
        print(f"\nProcessing complete.")
        print(f"Total subtitles processed: {total_rows}")
        print(f"Successfully extracted: {success_count} ({success_count/total_rows*100:.2f}%)")
        print(f"Total processing time: {total_time:.2f} seconds")
        
        return True
    
    def save_subtitles_to_files(self, output_dir: str = "extracted_subtitles") -> int:
        """
        Save extracted subtitles to individual text files.
        
        Args:
            output_dir: Directory to save subtitle files
            
        Returns:
            Number of subtitle files successfully saved
        """
        if self.df is None or 'subtitle_text' not in self.df.columns:
            print("No processed subtitles available. Process subtitles first.")
            return 0
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        count = 0
        for _, row in self.df.iterrows():
            if row['subtitle_text'] is not None:
                # Create a unique filename using the num and name
                filename = f"{row['num']}_{row['name']}.srt"
                filename = re.sub(r'[\\/*?:"<>|]', '_', filename)  # Remove invalid filename chars
                file_path = os.path.join(output_dir, filename)
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(row['subtitle_text'])
                    count += 1
                except Exception as e:
                    print(f"Error saving {filename}: {e}")
        
        print(f"Successfully saved {count} subtitle files to {output_dir}")
        return count
    
    def search_subtitles(self, query: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Search through processed subtitles for a specific query.
        
        Args:
            query: Text to search for
            case_sensitive: Whether to perform a case-sensitive search
            
        Returns:
            DataFrame containing matching subtitles
        """
        if self.df is None or 'subtitle_text' not in self.df.columns:
            print("No processed subtitles available. Process subtitles first.")
            return pd.DataFrame()
        
        # Filter out None values
        valid_df = self.df[self.df['subtitle_text'].notna()].copy()
        
        if len(valid_df) == 0:
            print("No valid subtitles to search.")
            return pd.DataFrame()
        
        if case_sensitive:
            mask = valid_df['subtitle_text'].str.contains(query, regex=False)
        else:
            mask = valid_df['subtitle_text'].str.contains(query, case=False, regex=False)
        
        results = valid_df[mask].copy()
        print(f"Found {len(results)} subtitles containing '{query}'")
        
        # Add a column with a snippet of the matching content
        if not results.empty:
            # Extract a snippet around the match
            def extract_snippet(text, search_term, context_size=50):
                if not case_sensitive:
                    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
                else:
                    pattern = re.compile(re.escape(search_term))
                
                match = pattern.search(text)
                if match:
                    start = max(0, match.start() - context_size)
                    end = min(len(text), match.end() + context_size)
                    snippet = text[start:end]
                    # Add ellipsis if we trimmed the text
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(text):
                        snippet = snippet + "..."
                    return snippet
                return None
            
            if case_sensitive:
                results['snippet'] = results['subtitle_text'].apply(
                    lambda x: extract_snippet(x, query)
                )
            else:
                results['snippet'] = results['subtitle_text'].apply(
                    lambda x: extract_snippet(x, query)
                )
        
        return results
    
    def get_subtitle_info(self, subtitle_id: int) -> Dict:
        """
        Get detailed information about a specific subtitle.
        
        Args:
            subtitle_id: The 'num' identifier of the subtitle
            
        Returns:
            Dictionary with subtitle information
        """
        if self.df is None:
            print("No data loaded. Call load_subtitle_data first.")
            return {}
        
        subtitle_row = self.df[self.df['num'] == subtitle_id]
        
        if subtitle_row.empty:
            return {"error": f"Subtitle with ID {subtitle_id} not found"}
        
        # Get the first matching row (should only be one)
        row = subtitle_row.iloc[0]
        
        # Extract subtitle text if available
        text = row.get('subtitle_text', None)
        if text is None and 'content' in row:
            # Extract on demand if not already processed
            text = self.extract_subtitle(row['content'])
        
        # Basic information
        info = {
            "id": int(row['num']),
            "name": row['name'],
            "url": f"https://www.opensubtitles.org/en/subtitles/{int(row['num'])}",
            "text_available": text is not None
        }
        
        # Add text info if available
        if text:
            # Count lines
            lines = text.count('\n')
            # Estimate word count (rough approximation)
            words = len(re.findall(r'\b\w+\b', text))
            
            info.update({
                "line_count": lines,
                "word_count": words,
                "preview": text[:200] + "..." if len(text) > 200 else text
            })
        
        return info
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def __del__(self):
        """Destructor to ensure database connection is closed."""
        self.close()
