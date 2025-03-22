import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import re
import os
import json
import random

class SubtitleSearchEngine:
    def __init__(self, data_path, model_type='semantic', sample_ratio=1.0):
        """
        Initialize the subtitle search engine.
        
        Args:
            data_path (str): Path to the subtitle data file
            model_type (str): 'keyword' for BOW/TF-IDF or 'semantic' for BERT
            sample_ratio (float): Ratio of data to sample (0.1 to 1.0)
        """
        self.data_path = data_path
        self.model_type = model_type
        self.sample_ratio = sample_ratio
        self.subtitle_data = None
        self.embeddings = None
        self.model = None
        self.vectorizer = None
        
    def load_data(self):
        """Load subtitle data from the specified path"""
        try:
            file_extension = os.path.splitext(self.data_path)[1].lower()
            
            if file_extension == '.csv':
                # Load CSV file
                self.subtitle_data = pd.read_csv(self.data_path)
            elif file_extension == '.json':
                # Load JSON file
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to DataFrame
                if isinstance(data, list):
                    self.subtitle_data = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Handle nested JSON structures
                    if 'subtitles' in data:
                        self.subtitle_data = pd.DataFrame(data['subtitles'])
                    else:
                        # Try to convert the dictionary to a DataFrame
                        self.subtitle_data = pd.DataFrame([data])
            elif file_extension == '.txt':
                # Load TXT file
                # Assuming each line is a subtitle entry
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Create a simple DataFrame with text column
                self.subtitle_data = pd.DataFrame({'text': lines})
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
            
            # Sample data if needed
            if self.sample_ratio < 1.0:
                self.subtitle_data = self.subtitle_data.sample(
                    frac=self.sample_ratio, random_state=42
                )
            
            # Make sure there's a text column
            self._ensure_text_column()
            
            print(f"Loaded {len(self.subtitle_data)} subtitle documents")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def _ensure_text_column(self):
        """Ensure there's a 'text' column in the DataFrame"""
        if 'text' not in self.subtitle_data.columns:
            # Look for possible text columns with different names
            possible_text_columns = [
                col for col in self.subtitle_data.columns 
                if col.lower() in ['subtitle', 'content', 'dialogue', 'line', 'caption']
            ]
            
            if possible_text_columns:
                # Use the first matching column
                self.subtitle_data['text'] = self.subtitle_data[possible_text_columns[0]]
            else:
                # If no suitable column found, concatenate all string columns
                string_cols = self.subtitle_data.select_dtypes(include=['object']).columns
                if len(string_cols) > 0:
                    self.subtitle_data['text'] = self.subtitle_data[string_cols].apply(
                        lambda row: ' '.join(str(val) for val in row if pd.notna(val)), 
                        axis=1
                    )
                else:
                    raise ValueError("Could not identify a text column in the data")
    
    def clean_text(self, text):
        """
        Clean subtitle text by removing timestamps and other noise.
        
        Args:
            text (str): The subtitle text to clean
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove timestamp patterns (e.g., 00:01:23,456 --> 00:01:25,789)
        text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', text)
        
        # Remove numeric indices
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def preprocess_data(self):
        """Preprocess subtitle data by cleaning text"""
        if self.subtitle_data is None:
            print("No data loaded. Please load data first.")
            return False
        
        # Clean the text column
        self.subtitle_data['cleaned_text'] = self.subtitle_data['text'].apply(self.clean_text)
        
        return True
    
    def create_document_chunks(self, text, chunk_size=500, overlap=100):
        """
        Divide a document into overlapping chunks to prevent information loss.
        
        Args:
            text (str): The document text
            chunk_size (int): Size of each chunk
            overlap (int): Number of tokens to overlap between chunks
            
        Returns:
            list: List of text chunks
        """
        if not text or not isinstance(text, str):
            return []
            
        # Simple word-based chunking
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text]
            
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
            # Stop if we've reached the end
            if i + chunk_size >= len(words):
                break
                
        return chunks
    
    def vectorize_documents(self):
        """Generate vector representations of the subtitle documents"""
        if 'cleaned_text' not in self.subtitle_data.columns:
            print("No cleaned text found. Please preprocess the data first.")
            return False
        
        # Create document chunks
        all_chunks = []
        chunk_to_doc_map = []  # Maps each chunk back to its original document
        
        for idx, row in self.subtitle_data.iterrows():
            chunks = self.create_document_chunks(row['cleaned_text'])
            all_chunks.extend(chunks)
            chunk_to_doc_map.extend([idx] * len(chunks))
        
        self.chunk_to_doc_map = chunk_to_doc_map
        
        # Vectorize based on the selected model type
        if self.model_type == 'keyword':
            # TF-IDF vectorization for keyword-based search
            self.vectorizer = TfidfVectorizer()
            self.embeddings = self.vectorizer.fit_transform(all_chunks)
            print(f"Created {self.embeddings.shape[0]} TF-IDF vectors")
        else:
            # BERT embeddings for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')  # A good general-purpose model
            self.embeddings = self.model.encode(all_chunks, show_progress_bar=True)
            print(f"Created {len(self.embeddings)} semantic embeddings")
        
        # Store the chunks for future reference
        self.chunks = all_chunks
        
        return True
    
    def search(self, query, top_k=5):
        """
        Search for relevant subtitle documents based on the query.
        
        Args:
            query (str): The search query
            top_k (int): Number of top results to return
            
        Returns:
            list: List of dictionaries containing matched documents and scores
        """
        if self.embeddings is None:
            print("No embeddings found. Please vectorize documents first.")
            return []
            
        # Clean the query
        clean_query = self.clean_text(query)
        
        # Vectorize the query
        if self.model_type == 'keyword':
            query_vector = self.vectorizer.transform([clean_query])
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.embeddings).flatten()
        else:
            query_vector = self.model.encode([clean_query])[0]
            # Calculate cosine similarity
            similarities = cosine_similarity([query_vector], self.embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k*2]  # Get more than we need
        
        # Map chunk indices back to document indices and remove duplicates
        doc_scores = {}
        for chunk_idx in top_indices:
            doc_idx = self.chunk_to_doc_map[chunk_idx]
            # Keep the highest score if a document appears multiple times
            if doc_idx not in doc_scores or similarities[chunk_idx] > doc_scores[doc_idx]:
                doc_scores[doc_idx] = similarities[chunk_idx]
        
        # Sort document scores and take top_k
        top_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Prepare results
        results = []
        for doc_idx, score in top_docs:
            doc = self.subtitle_data.iloc[doc_idx]
            result = {
                'score': float(score),
                'document': doc.to_dict()
            }
            results.append(result)
        
        return results
    
    def process_audio_query(self, audio_path):
        """
        Process an audio query (placeholder for actual implementation).
        In a real implementation, this would:
        1. Transcribe the audio to text
        2. Clean the transcribed text
        3. Return the text for searching
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Transcribed and cleaned query text
        """
        # This is a placeholder - in a real implementation,
        # you would use a speech-to-text service like Google's Speech Recognition,
        # AWS Transcribe, or similar
        print(f"Processing audio from {audio_path}")
        print("Note: Actual audio processing not implemented in this demo")
        
        # Return a placeholder text
        return "This is a placeholder for transcribed audio"
