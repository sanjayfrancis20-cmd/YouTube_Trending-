"""
Exports pre-aggregated metrics and top video records to dashboard/data.json
for an ultra-fast, responsive interactive dashboard.
"""

import os
import sys
import json
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed')
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')
os.makedirs(DASHBOARD_DIR, exist_ok=True)

def generate_dashboard_json():
    summary_path = os.path.join(DATA_PROC_DIR, 'youtube_trending_summary.csv')
    df = pd.read_csv(summary_path)
    
    regions = ['ALL', 'US', 'CA', 'IN']
    dashboard_payload = {}
    
    for reg in regions:
        if reg == 'ALL':
            sub_df = df
        else:
            sub_df = df[df['region'] == reg]
            
        total_videos = len(sub_df)
        avg_views = int(sub_df['peak_views'].mean())
        avg_likes = int(sub_df['peak_likes'].mean())
        avg_engagement = round(sub_df['engagement_rate'].mean(), 2)
        avg_days_trending = round(sub_df['trending_days_count'].mean(), 2)
        
        # Category Breakdown
        cat_agg = sub_df.groupby('category_name').agg(
            count=('video_id', 'count'),
            avg_views=('peak_views', 'mean'),
            avg_engagement=('engagement_rate', 'mean')
        ).reset_index().sort_values(by='avg_views', ascending=False)
        
        categories = cat_agg.to_dict(orient='records')
        for c in categories:
            c['avg_views'] = int(c['avg_views']) if pd.notna(c['avg_views']) else 0
            c['avg_engagement'] = round(c['avg_engagement'], 2) if pd.notna(c['avg_engagement']) else 0
            
        # Sentiment Breakdown
        sent_agg = sub_df.groupby('title_sentiment_label').agg(
            count=('video_id', 'count'),
            avg_views=('peak_views', 'mean'),
            avg_engagement=('engagement_rate', 'mean')
        ).reset_index()
        
        sentiments = sent_agg.to_dict(orient='records')
        for s in sentiments:
            s['avg_views'] = int(s['avg_views']) if pd.notna(s['avg_views']) else 0
            s['avg_engagement'] = round(s['avg_engagement'], 2) if pd.notna(s['avg_engagement']) else 0
            s['pct'] = round(s['count'] * 100 / total_videos, 1) if total_videos > 0 else 0
            
        # Duration Tiers
        duration_bins = pd.cut(
            sub_df['trending_days_count'],
            bins=[0, 1, 4, 9, 200],
            labels=['1 Day (Flash)', '2-4 Days (Standard)', '5-9 Days (Extended)', '10+ Days (Viral Hit)']
        )
        duration_agg = sub_df.assign(duration_tier=duration_bins).groupby('duration_tier', observed=False).agg(
            count=('video_id', 'count'),
            avg_views=('peak_views', 'mean')
        ).reset_index()
        
        durations = duration_agg.to_dict(orient='records')
        for d in durations:
            d['avg_views'] = int(d['avg_views']) if pd.notna(d['avg_views']) else 0
            d['pct'] = round(d['count'] * 100 / total_videos, 1) if total_videos > 0 else 0
            
        # Hourly Distribution
        hour_agg = sub_df.groupby('publish_hour').agg(
            count=('video_id', 'count'),
            avg_views=('peak_views', 'mean')
        ).reset_index().sort_values(by='publish_hour')
        
        hourly = hour_agg.to_dict(orient='records')
        for h in hourly:
            h['avg_views'] = int(h['avg_views'])

        # Top 15 Viral Videos
        top_videos = sub_df.sort_values(by='peak_views', ascending=False).head(15)[[
            'video_id', 'title', 'channel_title', 'category_name', 'region',
            'peak_views', 'peak_likes', 'engagement_rate', 'trending_days_count',
            'title_sentiment_label'
        ]].to_dict(orient='records')
        
        dashboard_payload[reg] = {
            'metrics': {
                'total_videos': total_videos,
                'avg_views': avg_views,
                'avg_likes': avg_likes,
                'avg_engagement': avg_engagement,
                'avg_days_trending': avg_days_trending
            },
            'categories': categories,
            'sentiments': sentiments,
            'durations': durations,
            'hourly': hourly,
            'top_videos': top_videos
        }
        
    out_path = os.path.join(DASHBOARD_DIR, 'data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_payload, f, indent=2)
        
    print(f"Exported dashboard JSON data ({os.path.getsize(out_path):,} bytes) to {out_path}")

if __name__ == '__main__':
    generate_dashboard_json()
