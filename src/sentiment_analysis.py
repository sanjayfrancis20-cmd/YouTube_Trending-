"""
Sentiment Analysis module for YouTube Trending Video Analytics.
Analyzes sentiment of video titles and tags using NLTK VADER.
"""

import re
import sys
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure VADER lexicon is available
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

class YouTubeSentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Add common YouTube/internet slang to VADER lexicon to improve domain sensitivity
        custom_lexicon = {
            'lit': 2.0,
            'fire': 2.0,
            'epic': 2.5,
            'insane': 1.8,
            'cringe': -1.8,
            'fail': -2.0,
            'wholesome': 2.2,
            'hilarious': 2.5,
            'breathtaking': 2.5,
            'scam': -2.8,
            'trash': -2.2,
            'legendary': 2.5,
            'goat': 2.5,
            'rip': -1.5,
            'clutch': 2.0,
            'hyped': 2.2,
            'flop': -2.0,
            'unbelievable': 1.5,
            'masterpiece': 2.8,
            'clickbait': -1.5,
            'exposed': -1.8,
            'banger': 2.2
        }
        self.sia.lexicon.update(custom_lexicon)

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean video title or tags for sentiment analysis."""
        if not isinstance(text, str) or pd.isna(text):
            return ""
        # Replace delimiter pipe for tags with space
        cleaned = text.replace('|', ' ').replace('"', ' ').replace("'", "")
        # Remove URLs
        cleaned = re.sub(r'http\S+|www\S+', '', cleaned)
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def analyze_text(self, text: str) -> dict:
        """Return VADER polarity scores and qualitative label."""
        cleaned = self.clean_text(text)
        if not cleaned or cleaned == '[none]':
            return {
                'compound': 0.0,
                'pos': 0.0,
                'neu': 1.0,
                'neg': 0.0,
                'label': 'Neutral'
            }
        scores = self.sia.polarity_scores(cleaned)
        compound = scores['compound']
        
        if compound >= 0.05:
            label = 'Positive'
        elif compound <= -0.05:
            label = 'Negative'
        else:
            label = 'Neutral'
            
        scores['label'] = label
        return scores

    def batch_analyze_series(self, series: pd.Series) -> pd.DataFrame:
        """
        Efficiently analyze sentiment on a pandas Series of text by caching unique strings.
        Returns a DataFrame with ['compound', 'pos', 'neu', 'neg', 'label'].
        """
        unique_texts = series.dropna().unique()
        cache = {text: self.analyze_text(text) for text in unique_texts}
        
        # Default for missing/null values
        default_score = {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0, 'label': 'Neutral'}
        
        results = [cache.get(t, default_score) if pd.notna(t) else default_score for t in series]
        return pd.DataFrame(results, index=series.index)


if __name__ == '__main__':
    analyzer = YouTubeSentimentAnalyzer()
    test_titles = [
        "Marvel Studios' Avengers: Infinity War Official Trailer",
        "THIS WAS A COMPLETE DISASTER!! (Worst Day Ever)",
        "10 INSANE Life Hacks You Must Try Today!",
        "Official Press Conference - Statement on Crisis",
        "Wholesome dog rescues tiny kitten ❤️"
    ]
    for t in test_titles:
        res = analyzer.analyze_text(t)
        print(f"[{res['label'].upper():<8}] ({res['compound']:+.3f}) {t}")
