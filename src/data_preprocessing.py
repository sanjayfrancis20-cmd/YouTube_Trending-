"""
Data Preprocessing & Standardization Pipeline for YouTube Trending Video Analytics.
Cleans and standardizes multi-region datasets (US, CA, IN), maps category metadata,
computes engagement and latency metrics, performs sentiment analysis, and prepares
analytical datasets for SQL, Tableau, and Python visualization.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sentiment_analysis import YouTubeSentimentAnalyzer

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
DATA_PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
TABLEAU_DIR = os.path.join(os.path.dirname(__file__), '..', 'tableau')

def load_category_mapping(json_path: str) -> dict:
    """Load category ID to name dictionary from official category JSON."""
    if not os.path.exists(json_path):
        print(f"Warning: Category JSON not found at {json_path}. Using fallback.")
        return {}
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for item in data.get('items', []):
        cat_id = int(item['id'])
        cat_name = item['snippet']['title']
        mapping[cat_id] = cat_name
        
    # Additional YouTube Category IDs for fallback
    standard_fallbacks = {
        1: 'Film & Animation',
        2: 'Autos & Vehicles',
        10: 'Music',
        15: 'Pets & Animals',
        17: 'Sports',
        18: 'Short Movies',
        19: 'Travel & Events',
        20: 'Gaming',
        21: 'Videoblogging',
        22: 'People & Blogs',
        23: 'Comedy',
        24: 'Entertainment',
        25: 'News & Politics',
        26: 'Howto & Style',
        27: 'Education',
        28: 'Science & Technology',
        29: 'Nonprofits & Activism',
        30: 'Movies',
        31: 'Anime/Animation',
        32: 'Action/Adventure',
        33: 'Classics',
        34: 'Comedy Movies',
        35: 'Documentary',
        36: 'Drama',
        37: 'Family',
        38: 'Foreign',
        39: 'Horror',
        40: 'Sci-Fi/Fantasy',
        41: 'Thriller',
        42: 'Shorts',
        43: 'Shows',
        44: 'Trailers'
    }
    for k, v in standard_fallbacks.items():
        if k not in mapping:
            mapping[k] = v
            
    return mapping

def load_and_standardize_region(filepath: str, region_code: str, category_map: dict) -> pd.DataFrame:
    """Load a region's CSV file and perform schema harmonization."""
    print(f"Loading {region_code} from {filepath}...")
    try:
        df = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='latin1', on_bad_lines='skip')

    df['region'] = region_code
    
    # Filter out removed/error videos
    if 'video_error_or_removed' in df.columns:
        df = df[df['video_error_or_removed'] != True].copy()
        
    # Convert trending_date ('yy.dd.mm') to datetime
    df['trending_date'] = pd.to_datetime(df['trending_date'], format='%y.%d.%m', errors='coerce')
    
    # Convert publish_time to datetime (UTC)
    df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce', utc=True)
    df['publish_date'] = df['publish_time'].dt.date
    df['publish_date'] = pd.to_datetime(df['publish_date'])
    df['publish_hour'] = df['publish_time'].dt.hour
    df['publish_day_name'] = df['publish_time'].dt.day_name()
    df['publish_day_of_week'] = df['publish_time'].dt.dayofweek
    
    # Calculate days to trend (latency)
    df['days_to_trend'] = (df['trending_date'] - df['publish_date']).dt.days
    df['days_to_trend'] = df['days_to_trend'].apply(lambda x: max(0, x) if pd.notna(x) else np.nan)
    
    # Map category names
    df['category_id'] = pd.to_numeric(df['category_id'], errors='coerce').fillna(0).astype(int)
    df['category_name'] = df['category_id'].map(category_map).fillna('Other / Uncategorized')
    
    # Ensure numeric columns
    numeric_cols = ['views', 'likes', 'dislikes', 'comment_count']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(np.int64)
        
    # Filter out zero or negative views anomalies
    df = df[df['views'] > 0].copy()
    
    # Text cleaning & tag count
    df['title'] = df['title'].fillna('').astype(str).str.strip()
    df['tags'] = df['tags'].fillna('').astype(str).str.strip()
    df['channel_title'] = df['channel_title'].fillna('Unknown Channel').astype(str).str.strip()
    df['description'] = df['description'].fillna('').astype(str).str.strip()
    
    def count_tags(tag_str):
        if not tag_str or tag_str == '[none]':
            return 0
        return len([t for t in tag_str.split('|') if t.strip()])
        
    df['tag_count'] = df['tags'].apply(count_tags)
    df['title_length'] = df['title'].str.len()
    
    # Capital letters ratio in title (indicator for clickbait/hyperbole)
    def calc_caps_ratio(title):
        letters = [c for c in title if c.isalpha()]
        if not letters:
            return 0.0
        return sum(1 for c in letters if c.isupper()) / len(letters)
        
    df['title_caps_ratio'] = df['title'].apply(calc_caps_ratio)
    
    # Interaction & Engagement metrics
    total_ratings = df['likes'] + df['dislikes']
    df['like_ratio'] = np.where(total_ratings > 0, df['likes'] / total_ratings, 0.0)
    df['dislike_ratio'] = np.where(total_ratings > 0, df['dislikes'] / total_ratings, 0.0)
    df['engagement_rate'] = ((df['likes'] + df['dislikes'] + df['comment_count']) / df['views']) * 100
    
    # Booleans
    for b_col in ['comments_disabled', 'ratings_disabled', 'video_error_or_removed']:
        if b_col in df.columns:
            df[b_col] = df[b_col].astype(bool)
            
    print(f"Processed {len(df)} rows for {region_code}.")
    return df

def run_pipeline():
    os.makedirs(DATA_PROC_DIR, exist_ok=True)
    os.makedirs(TABLEAU_DIR, exist_ok=True)
    
    cat_json_path = os.path.join(DATA_RAW_DIR, 'US_category_id.json')
    category_map = load_category_mapping(cat_json_path)
    print(f"Loaded {len(category_map)} category mappings.")
    
    regions = [
        ('US', os.path.join(DATA_RAW_DIR, 'USvideos.csv')),
        ('CA', os.path.join(DATA_RAW_DIR, 'CAvideos.csv')),
        ('IN', os.path.join(DATA_RAW_DIR, 'INvideos.csv'))
    ]
    
    dfs = []
    for reg, path in regions:
        if os.path.exists(path):
            dfs.append(load_and_standardize_region(path, reg, category_map))
        else:
            print(f"Error: {path} not found.")
            
    if not dfs:
        raise RuntimeError("No regional datasets were loaded.")
        
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal combined rows across {len(dfs)} regions: {len(combined_df):,}")
    
    # --- Video Lifecycle & Trending Duration ---
    print("\nComputing trending duration and video lifecycle metrics...")
    lifecycle = combined_df.groupby(['video_id', 'region']).agg(
        trending_days_count=('trending_date', 'nunique'),
        first_trending_date=('trending_date', 'min'),
        last_trending_date=('trending_date', 'max'),
        peak_views=('views', 'max'),
        peak_likes=('likes', 'max'),
        peak_dislikes=('dislikes', 'max'),
        peak_comments=('comment_count', 'max')
    ).reset_index()
    
    lifecycle['trending_duration_span'] = (lifecycle['last_trending_date'] - lifecycle['first_trending_date']).dt.days + 1
    
    # Merge lifecycle metrics back onto snapshot rows
    combined_df = combined_df.merge(
        lifecycle[['video_id', 'region', 'trending_days_count', 'trending_duration_span', 'peak_views', 'peak_likes', 'peak_comments']],
        on=['video_id', 'region'],
        how='left'
    )
    
    # --- Sentiment Analysis ---
    print("\nExecuting sentiment analysis on unique titles and tags using VADER...")
    analyzer = YouTubeSentimentAnalyzer()
    
    # Analyze video titles
    print("Analyzing video titles...")
    title_sentiments = analyzer.batch_analyze_series(combined_df['title'])
    combined_df['title_sentiment_score'] = title_sentiments['compound'].values
    combined_df['title_sentiment_label'] = title_sentiments['label'].values
    
    # Analyze video tags
    print("Analyzing video tags...")
    tag_sentiments = analyzer.batch_analyze_series(combined_df['tags'])
    combined_df['tags_sentiment_score'] = tag_sentiments['compound'].values
    combined_df['tags_sentiment_label'] = tag_sentiments['label'].values
    
    # Format date strings for clean exports
    combined_df['trending_date_str'] = combined_df['trending_date'].dt.strftime('%Y-%m-%d')
    combined_df['publish_date_str'] = combined_df['publish_date'].dt.strftime('%Y-%m-%d')
    
    # Save full cleaned snapshots
    full_cleaned_path = os.path.join(DATA_PROC_DIR, 'youtube_trending_cleaned.csv')
    print(f"\nSaving full cleaned dataset to {full_cleaned_path}...")
    combined_df.to_csv(full_cleaned_path, index=False)
    
    # Save aggregated video-level summary (one row per unique video_id per region)
    # Picks the final snapshot attributes with peak metrics
    summary_path = os.path.join(DATA_PROC_DIR, 'youtube_trending_summary.csv')
    print(f"Saving video-level summary dataset to {summary_path}...")
    
    # Sort by views descending and take unique per (video_id, region)
    video_summary = combined_df.sort_values(by='views', ascending=False).drop_duplicates(subset=['video_id', 'region']).copy()
    video_summary.to_csv(summary_path, index=False)
    
    # Save Tableau export (concise columns, formatted cleanly)
    tableau_path = os.path.join(TABLEAU_DIR, 'youtube_trending_tableau.csv')
    print(f"Saving Tableau-optimized dataset to {tableau_path}...")
    tableau_cols = [
        'video_id', 'region', 'title', 'channel_title', 'category_name',
        'trending_date_str', 'publish_date_str', 'publish_hour', 'publish_day_name',
        'views', 'likes', 'dislikes', 'comment_count', 'like_ratio', 'engagement_rate',
        'days_to_trend', 'trending_days_count', 'trending_duration_span',
        'title_sentiment_score', 'title_sentiment_label', 'tags_sentiment_score', 'tags_sentiment_label',
        'tag_count', 'title_length', 'title_caps_ratio'
    ]
    combined_df[tableau_cols].to_csv(tableau_path, index=False)
    
    print("\nData Preprocessing & Standardization Pipeline completed successfully!")
    print(f"Summary metrics:")
    print(f" - Total Snapshot Records: {len(combined_df):,}")
    print(f" - Unique Video-Region Pairs: {len(video_summary):,}")
    print(f" - Regions Covered: {combined_df['region'].unique().tolist()}")
    print(f" - Top 3 Categories: {combined_df['category_name'].value_counts().head(3).to_dict()}")
    print(f" - Title Sentiment Breakdown: {combined_df['title_sentiment_label'].value_counts().to_dict()}")

if __name__ == '__main__':
    run_pipeline()
