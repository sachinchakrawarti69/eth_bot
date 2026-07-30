"""
Cryptocurrency Sentiment Analysis from Social Media
Free using NewsAPI and Twitter scraping
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import re

class SentimentAnalyzer:
    def __init__(self):
        # Free NewsAPI (no key needed for limited requests)
        self.news_url = "https://newsapi.org/v2/everything"
        # Get free key from newsapi.org
        self.api_key = "YOUR_NEWS_API_KEY"  # Optional
        
    def fetch_crypto_news(self, query="Ethereum", days=7):
        """Fetch recent crypto news"""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en'
        }
        if self.api_key != "YOUR_NEWS_API_KEY":
            params['apiKey'] = self.api_key
        
        try:
            response = requests.get(self.news_url, params=params)
            articles = response.json().get('articles', [])
            return pd.DataFrame(articles)
        except:
            return pd.DataFrame()
    
    def analyze_sentiment(self, text):
        """Simple rule-based sentiment analysis"""
        positive_words = ['bullish', 'surge', 'rally', 'gain', 'up', 'high', 'record', 'breakthrough']
        negative_words = ['bearish', 'crash', 'drop', 'fall', 'down', 'low', 'decline', 'selloff']
        
        text_lower = text.lower()
        pos_score = sum(1 for word in positive_words if word in text_lower)
        neg_score = sum(1 for word in negative_words if word in text_lower)
        
        if pos_score > neg_score:
            return 1  # Positive
        elif neg_score > pos_score:
            return -1  # Negative
        return 0  # Neutral
    
    def get_sentiment_score(self):
        """Get overall sentiment score"""
        df = self.fetch_crypto_news()
        if len(df) == 0:
            return 0
        
        df['sentiment'] = df['title'].apply(self.analyze_sentiment)
        sentiment_score = df['sentiment'].mean()
        
        return {
            'score': sentiment_score,
            'positive_count': len(df[df['sentiment'] == 1]),
            'negative_count': len(df[df['sentiment'] == -1]),
            'neutral_count': len(df[df['sentiment'] == 0])
        }

# Add to config.py
# SENTIMENT_ENABLED = True