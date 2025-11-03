import requests
import json
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import hashlib
from dotenv import dotenv_values

class NewsHistoryManager:
    def __init__(self, history_file='history_manager.txt', api_key=None):
        """
        Initialize the News History Manager
        
        Args:
            history_file: Path to the file storing news history
            api_key: NewsAPI key (get from https://newsapi.org/)
        """
        self.history_file = history_file
        self.api_key = api_key
        self.history = self._load_history()
        
    def _load_history(self) -> Dict:
        """Load existing history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure title_hashes is a list
                    if 'title_hashes' in data and isinstance(data['title_hashes'], list):
                        data['title_hashes'] = data['title_hashes']
                    else:
                        data['title_hashes'] = []
                    return data
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Warning: {self.history_file} is corrupted or not found. Starting fresh.")
                return {'processed_titles': [], 'title_hashes': []}
        return {'processed_titles': [], 'title_hashes': []}
    
    def _save_history(self):
        """Save history to file"""
        save_data = {
            'processed_titles': self.history['processed_titles'],
            'title_hashes': list(self.history.get('title_hashes', []))
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    def _generate_hash(self, title: str) -> str:
        """Generate hash for a title to check duplicates efficiently"""
        return hashlib.md5(title.lower().strip().encode()).hexdigest()
    
    def _is_duplicate(self, title: str) -> bool:
        """Check if title already exists in history"""
        title_hash = self._generate_hash(title)
        
        # Initialize title_hashes if not exists
        if 'title_hashes' not in self.history:
            self.history['title_hashes'] = []
        
        return title_hash in self.history['title_hashes']
    
    def fetch_latest_tech_news(self) -> Optional[Dict]:
        """
        Fetch the most recent tech news article
        
        Returns:
            Dictionary with the latest tech news or None if no news found
        """
        if not self.api_key:
            raise ValueError("NewsAPI key is required. Get one from https://newsapi.org/")
        
        # Fetch latest tech news - sorted by publishedAt (most recent first)
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': 'technology OR tech OR AI OR "artificial intelligence" OR ML OR "machine learning" OR gadgets OR software',
            'pageSize': 50,  # Fetch more to ensure we get a unique one
            'sortBy': 'publishedAt',  # Most recent first
            'language': 'en',
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = data.get('articles', [])
                
                # Find the first unique article
                for article in articles:
                    title = article.get('title', '').strip()
                    
                    if not title or title == '[Removed]':
                        continue
                    
                    # Check if it's not a duplicate
                    if not self._is_duplicate(title):
                        # Found a unique article!
                        news_item = {
                            'title': title,
                            'description': article.get('description', '') or article.get('content', '').split('[+')[0].strip() if article.get('content') else 'No description available',
                            'url': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'published_at': article.get('publishedAt', ''),
                            'processed_at': datetime.now().isoformat()
                        }
                        
                        # Add to history
                        title_hash = self._generate_hash(title)
                        if 'title_hashes' not in self.history:
                            self.history['title_hashes'] = []
                        self.history['title_hashes'].append(title_hash)
                        self.history['processed_titles'].append(news_item)
                        self._save_history()
                        
                        print(f"[SUCCESS] Found latest unique tech news!")
                        return news_item
                
                print("[INFO] No new unique articles found. All recent news already processed.")
                return None
            else:
                print(f"API Error: {data.get('message', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_latest_tech_news(self) -> Optional[Dict]:
        """
        Main method: Fetch the single most recent tech news
        
        Returns:
            Dictionary with title and description of the latest tech news
        """
        print(f"\n{'='*60}")
        print(f"Fetching the LATEST tech news...")
        print(f"{'='*60}")
        
        news = self.fetch_latest_tech_news()
        return news
    
    def get_history_stats(self) -> Dict:
        """Get statistics about processed news"""
        return {
            'total_processed': len(self.history['processed_titles']),
            'sources': list(set(item['source'] for item in self.history['processed_titles'])),
            'oldest_entry': self.history['processed_titles'][0]['processed_at'] if self.history['processed_titles'] else None,
            'latest_entry': self.history['processed_titles'][-1]['processed_at'] if self.history['processed_titles'] else None
        }
    
    def clear_history(self):
        """Clear all history (use with caution)"""
        self.history = {'processed_titles': [], 'title_hashes': []}
        self._save_history()
        print("[SUCCESS] History cleared")


def main():
    """Main function to fetch the single latest trending tech news"""
    # Get the main folder path (parent of fetch_trends)
    current_file = Path(__file__)  # trends.py
    fetch_trends_folder = current_file.parent  # fetch_trends/
    main_folder = fetch_trends_folder.parent  # main folder
    
    # Path to .env file in main folder
    env_path = main_folder / ".env"
    
    # Path to history file in history folder
    history_folder = main_folder / "history"
    history_folder.mkdir(exist_ok=True)  # Create history folder if it doesn't exist
    history_file = history_folder / "history_manager.txt"
    
    # Load environment variables
    if env_path.exists():
        env = dotenv_values(env_path)
        API_KEY = env.get('NEWS_API_KEY')
        if not API_KEY:
            print("[ERROR] NEWS_API_KEY not found in .env file")
            print("Please add NEWS_API_KEY=your_api_key to .env file")
            return
    else:
        print(f"[ERROR] .env file not found at {env_path}")
        print("Please create a .env file with NEWS_API_KEY=your_api_key")
        return
    
    # Initialize the manager
    manager = NewsHistoryManager(
        history_file=str(history_file),
        api_key=API_KEY
    )
    
    # Fetch the single latest tech news
    news = manager.get_latest_tech_news()
    
    if news:
        print(f"\n{'='*60}")
        print(f"📰 LATEST TECH NEWS")
        print(f"{'='*60}\n")
        print(f"Title: {news['title']}\n")
        print(f"Description: {news['description']}\n")
        print(f"Source: {news['source']}")
        print(f"Published: {news['published_at']}")
        print(f"URL: {news['url']}")
        print(f"\n{'='*60}\n")
        
        # Return the news for use by other modules
        return news
    else:
        print("\n[INFO] No new unique tech news available at the moment.")
        print("All recent articles have already been processed.")
        print("Please try again later or clear history to reprocess articles.")
        return None


if __name__ == "__main__":
    latest_news = main()
