-- YouTube Trending Analytics Schema
-- Relational / Star Schema for Multi-Region Analysis

DROP TABLE IF EXISTS trending_snapshots;
DROP TABLE IF EXISTS videos;
DROP TABLE IF EXISTS categories;

-- Dimension: Categories
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- Dimension/Entity: Unique Video Records per Region with Lifecycle & Sentiment
CREATE TABLE videos (
    video_id VARCHAR(50),
    region VARCHAR(10),
    title TEXT,
    channel_title VARCHAR(255),
    category_id INTEGER,
    publish_time TIMESTAMP,
    publish_date DATE,
    publish_hour INTEGER,
    publish_day_name VARCHAR(20),
    days_to_trend INTEGER,
    tag_count INTEGER,
    title_length INTEGER,
    title_caps_ratio REAL,
    title_sentiment_score REAL,
    title_sentiment_label VARCHAR(20),
    tags_sentiment_score REAL,
    tags_sentiment_label VARCHAR(20),
    trending_days_count INTEGER,
    trending_duration_span INTEGER,
    peak_views INTEGER,
    peak_likes INTEGER,
    peak_dislikes INTEGER,
    peak_comments INTEGER,
    peak_engagement_rate REAL,
    peak_like_ratio REAL,
    PRIMARY KEY (video_id, region),
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
);

-- Fact: Daily Trending Snapshot Records
CREATE TABLE trending_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id VARCHAR(50),
    region VARCHAR(10),
    trending_date DATE,
    views INTEGER,
    likes INTEGER,
    dislikes INTEGER,
    comment_count INTEGER,
    like_ratio REAL,
    engagement_rate REAL,
    days_to_trend INTEGER,
    FOREIGN KEY (video_id, region) REFERENCES videos (video_id, region)
);

-- Performance & Analysis Indexes
CREATE INDEX idx_videos_region ON videos(region);
CREATE INDEX idx_videos_category ON videos(category_id);
CREATE INDEX idx_videos_sentiment ON videos(title_sentiment_label);
CREATE INDEX idx_snapshots_date ON trending_snapshots(trending_date);
CREATE INDEX idx_snapshots_vid_reg ON trending_snapshots(video_id, region);
