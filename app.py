import argparse
import os
import time
import pandas as pd
from subtitle_search_engine import SubtitleProcessor

def setup_database():
    """Check if database exists and create data directory if needed."""
    data_dir = "data"
    
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    # Check if database file exists
    db_path = os.path.join(data_dir, "eng_subtitles_database.db")
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        print("Please download the database file and place it in the data directory.")
        return False
    
    return True

def process_command(args):
    """Process command line arguments and execute appropriate functions."""
    processor = SubtitleProcessor()
    
    # Initialize database connection
    if not setup_database():
        return
    
    # Load data
    if not processor.load_subtitle_data(limit=args.limit):
        return
    
    # Execute the specific command
    if args.command == "process":
        # Process subtitles
        processor.process_subtitles(batch_size=args.batch_size)
        
        # Save to files if requested
        if args.save:
            processor.save_subtitles_to_files(output_dir=args.output_dir)
            
    elif args.command == "search":
        # Process subtitles if not already done
        if 'subtitle_text' not in processor.df.columns or processor.df['subtitle_text'].isna().all():
            print("Processing subtitles first...")
            processor.process_subtitles(batch_size=args.batch_size)
        
        # Perform search
        results = processor.search_subtitles(args.query, case_sensitive=args.case_sensitive)
        
        # Display results
        if not results.empty:
            print("\nSearch Results:")
            for idx, row in results.iterrows():
                print(f"\n{'-'*50}")
                print(f"ID: {row['num']} - {row['name']}")
                print(f"URL: https://www.opensubtitles.org/en/subtitles/{int(row['num'])}")
                print(f"\nSnippet: {row['snippet']}")
            
            # Save results if requested
            if args.save:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"search_results_{timestamp}.csv"
                results.to_csv(filename, index=False)
                print(f"\nSaved search results to {filename}")
        
    elif args.command == "info":
        # Get info for a specific subtitle
        info = processor.get_subtitle_info(args.id)
        
        if "error" in info:
            print(info["error"])
        else:
            print("\nSubtitle Information:")
            print(f"ID: {info['id']}")
            print(f"Name: {info['name']}")
            print(f"URL: {info['url']}")
            
            if info['text_available']:
                print(f"Line Count: {info['line_count']}")
                print(f"Word Count: {info['word_count']}")
                print("\nPreview:")
                print(info['preview'])
            else:
                print("\nSubtitle text not available.")
    
    # Close database connection
    processor.close()

def main():
    """Main function to handle command line interface."""
    parser = argparse.ArgumentParser(description="Subtitle Search Engine")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process subtitle files")
    process_parser.add_argument("--limit", type=int, help="Limit number of subtitles to process")
    process_parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    process_parser.add_argument("--save", action="store_true", help="Save processed subtitles to files")
    process_parser.add_argument("--output-dir", default="extracted_subtitles", help="Directory to save subtitle files")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for subtitles")
    search_parser.add_argument("query", help="Text to search for")
    search_parser.add_argument("--limit", type=int, help="Limit number of subtitles to search")
    search_parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    search_parser.add_argument("--case-sensitive", action="store_true", help="Perform case-sensitive search")
    search_parser.add_argument("--save", action="store_true", help="Save search results to CSV")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get information about a specific subtitle")
    info_parser.add_argument("id", type=int, help="Subtitle ID (num)")
    
    args = parser.parse_args()
    
    if args.command:
        process_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
