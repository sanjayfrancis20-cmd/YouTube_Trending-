"""
SQL Database ETL & Analytical Query Execution.
Loads cleaned YouTube datasets into SQLite database, executes advanced SQL analytical
queries, computes category rankings, and outputs query results for reporting.
"""

import os
import sys
import sqlite3
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'youtube_analytics.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'sql', 'schema.sql')
QUERIES_PATH = os.path.join(BASE_DIR, 'sql', 'queries.sql')
DATA_PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

def init_database():
    """Create tables and indexes from schema.sql."""
    print(f"Initializing SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("Database schema created successfully.")

def populate_database():
    """Load categories, video summaries, and snapshots into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Populate Categories
    cleaned_csv = os.path.join(DATA_PROC_DIR, 'youtube_trending_cleaned.csv')
    print("Reading cleaned dataset to extract categories...")
    df_clean = pd.read_csv(cleaned_csv, encoding='utf-8')
    
    cat_df = df_clean[['category_id', 'category_name']].drop_duplicates().dropna()
    cat_df.to_sql('categories', conn, if_exists='append', index=False)
    print(f"Populated {len(cat_df)} categories.")
    
    # 2. Populate Videos (Aggregated Video Entity)
    summary_csv = os.path.join(DATA_PROC_DIR, 'youtube_trending_summary.csv')
    print("Reading video summary dataset...")
    df_summary = pd.read_csv(summary_csv, encoding='utf-8')
    
    video_cols = [
        'video_id', 'region', 'title', 'channel_title', 'category_id',
        'publish_time', 'publish_date_str', 'publish_hour', 'publish_day_name',
        'days_to_trend', 'tag_count', 'title_length', 'title_caps_ratio',
        'title_sentiment_score', 'title_sentiment_label',
        'tags_sentiment_score', 'tags_sentiment_label',
        'trending_days_count', 'trending_duration_span',
        'peak_views', 'peak_likes', 'dislikes', 'peak_comments',
        'engagement_rate', 'like_ratio'
    ]
    
    # Rename matching columns to DB schema
    df_videos = df_summary[video_cols].rename(columns={
        'publish_date_str': 'publish_date',
        'dislikes': 'peak_dislikes',
        'engagement_rate': 'peak_engagement_rate',
        'like_ratio': 'peak_like_ratio'
    }).drop_duplicates(subset=['video_id', 'region'])
    
    print(f"Inserting {len(df_videos):,} records into 'videos' table...")
    df_videos.to_sql('videos', conn, if_exists='append', index=False)
    
    # 3. Populate Trending Snapshots
    print("Inserting snapshots into 'trending_snapshots' table...")
    snapshot_cols = [
        'video_id', 'region', 'trending_date_str', 'views', 'likes',
        'dislikes', 'comment_count', 'like_ratio', 'engagement_rate', 'days_to_trend'
    ]
    df_snapshots = df_clean[snapshot_cols].rename(columns={'trending_date_str': 'trending_date'})
    df_snapshots.to_sql('trending_snapshots', conn, if_exists='append', index=False)
    print(f"Inserted {len(df_snapshots):,} records into 'trending_snapshots' table.")
    
    conn.commit()
    conn.close()
    print("Database population complete!")

def run_analytical_queries():
    """Run all primary analytical queries and export outputs as CSV and Markdown."""
    conn = sqlite3.connect(DB_PATH)
    os.makedirs(os.path.join(REPORTS_DIR, 'tables'), exist_ok=True)
    
    # Query 1: Rank categories by views per region
    q1 = """
    WITH category_stats AS (
        SELECT 
            v.region,
            c.category_name,
            COUNT(DISTINCT v.video_id) AS unique_videos_count,
            ROUND(AVG(v.peak_views), 0) AS avg_views,
            ROUND(AVG(v.peak_likes), 0) AS avg_likes,
            ROUND(AVG(v.peak_comments), 0) AS avg_comments,
            ROUND(AVG(v.peak_engagement_rate), 2) AS avg_engagement_pct
        FROM videos v
        JOIN categories c ON v.category_id = c.category_id
        GROUP BY v.region, c.category_name
    )
    SELECT 
        region,
        category_name,
        unique_videos_count,
        CAST(avg_views AS INT) as avg_views,
        CAST(avg_likes AS INT) as avg_likes,
        CAST(avg_comments AS INT) as avg_comments,
        avg_engagement_pct,
        RANK() OVER (PARTITION BY region ORDER BY avg_views DESC) as rank_by_views,
        DENSE_RANK() OVER (PARTITION BY region ORDER BY avg_engagement_pct DESC) as rank_by_engagement
    FROM category_stats
    ORDER BY region, rank_by_views;
    """
    df_q1 = pd.read_sql_query(q1, conn)
    df_q1.to_csv(os.path.join(REPORTS_DIR, 'tables', 'q1_category_ranking_by_region.csv'), index=False)
    
    # Query 1B: Overall category ranking across all regions
    q1b = """
    SELECT 
        c.category_name,
        COUNT(DISTINCT v.video_id) AS total_unique_videos,
        CAST(ROUND(AVG(v.peak_views), 0) AS INT) AS avg_peak_views,
        CAST(ROUND(AVG(v.peak_likes), 0) AS INT) AS avg_peak_likes,
        CAST(ROUND(AVG(v.peak_comments), 0) AS INT) AS avg_peak_comments,
        ROUND(AVG(v.peak_engagement_rate), 2) AS avg_engagement_pct,
        ROUND(AVG(v.trending_days_count), 2) AS avg_days_on_trending,
        RANK() OVER (ORDER BY AVG(v.peak_views) DESC) AS rank_by_avg_views
    FROM videos v
    JOIN categories c ON v.category_id = c.category_id
    GROUP BY c.category_name
    ORDER BY rank_by_avg_views;
    """
    df_q1b = pd.read_sql_query(q1b, conn)
    df_q1b.to_csv(os.path.join(REPORTS_DIR, 'tables', 'q1b_overall_category_ranking.csv'), index=False)
    
    # Query 2: Sentiment impact on performance
    q2 = """
    SELECT 
        v.title_sentiment_label,
        COUNT(DISTINCT v.video_id) AS video_count,
        ROUND(COUNT(DISTINCT v.video_id) * 100.0 / (SELECT COUNT(*) FROM videos), 2) AS pct_of_library,
        CAST(ROUND(AVG(v.peak_views), 0) AS INT) AS avg_views,
        CAST(ROUND(AVG(v.peak_likes), 0) AS INT) AS avg_likes,
        ROUND(AVG(v.peak_engagement_rate), 2) AS avg_engagement_pct,
        ROUND(AVG(v.peak_like_ratio) * 100, 2) AS avg_positive_like_pct,
        ROUND(AVG(v.days_to_trend), 2) AS avg_days_to_trend,
        ROUND(AVG(v.trending_days_count), 2) AS avg_trending_duration_days
    FROM videos v
    GROUP BY v.title_sentiment_label
    ORDER BY avg_views DESC;
    """
    df_q2 = pd.read_sql_query(q2, conn)
    df_q2.to_csv(os.path.join(REPORTS_DIR, 'tables', 'q2_sentiment_performance.csv'), index=False)
    
    # Query 3: Duration tier distribution
    q4 = """
    SELECT 
        CASE 
            WHEN trending_days_count = 1 THEN '1 Day (Flash Trend)'
            WHEN trending_days_count BETWEEN 2 AND 4 THEN '2-4 Days (Standard)'
            WHEN trending_days_count BETWEEN 5 AND 9 THEN '5-9 Days (Extended)'
            ELSE '10+ Days (Viral Mega-Hit)'
        END AS duration_tier,
        COUNT(*) AS total_videos,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM videos), 2) AS pct_of_videos,
        CAST(ROUND(AVG(peak_views), 0) AS INT) AS avg_peak_views,
        CAST(ROUND(AVG(peak_likes), 0) AS INT) AS avg_peak_likes,
        ROUND(AVG(peak_engagement_rate), 2) AS avg_engagement_pct
    FROM videos
    GROUP BY duration_tier
    ORDER BY avg_peak_views DESC;
    """
    df_q4 = pd.read_sql_query(q4, conn)
    df_q4.to_csv(os.path.join(REPORTS_DIR, 'tables', 'q4_duration_tiers.csv'), index=False)

    conn.close()
    
    print("\n--- SQL Query 1 Results: Top 5 Categories per Region by Avg Views ---")
    print(df_q1[df_q1['rank_by_views'] <= 5][['region', 'rank_by_views', 'category_name', 'avg_views', 'avg_engagement_pct']].to_string(index=False))
    
    print("\n--- SQL Query 1B Results: Overall Categories Ranked by Avg Views ---")
    print(df_q1b.head(10)[['rank_by_avg_views', 'category_name', 'avg_peak_views', 'avg_engagement_pct', 'avg_days_on_trending']].to_string(index=False))
    
    print("\n--- SQL Query 2 Results: Sentiment Performance ---")
    print(df_q2.to_string(index=False))
    
    print("\n--- SQL Query 4 Results: Trending Duration Tiers ---")
    print(df_q4.to_string(index=False))

if __name__ == '__main__':
    init_database()
    populate_database()
    run_analytical_queries()
