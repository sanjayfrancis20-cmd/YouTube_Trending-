-- YouTube Trending Video Analytics - Key Analytical Queries

-- ====================================================================
-- QUERY 1: Rank Categories by Average Views (Overall & Per Region)
-- Uses SQL Window Function RANK() partitioned by region
-- ====================================================================
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
    avg_views,
    avg_likes,
    avg_comments,
    avg_engagement_pct,
    RANK() OVER (PARTITION BY region ORDER BY avg_views DESC) as rank_by_views,
    DENSE_RANK() OVER (PARTITION BY region ORDER BY avg_engagement_pct DESC) as rank_by_engagement
FROM category_stats
ORDER BY region, rank_by_views;


-- ====================================================================
-- QUERY 1B: Global Overall Category Ranking (Across All Regions)
-- ====================================================================
SELECT 
    c.category_name,
    COUNT(DISTINCT v.video_id) AS total_unique_videos,
    ROUND(AVG(v.peak_views), 0) AS avg_peak_views,
    ROUND(AVG(v.peak_likes), 0) AS avg_peak_likes,
    ROUND(AVG(v.peak_comments), 0) AS avg_peak_comments,
    ROUND(AVG(v.peak_engagement_rate), 2) AS avg_engagement_rate,
    ROUND(AVG(v.trending_days_count), 2) AS avg_days_on_trending,
    RANK() OVER (ORDER BY AVG(v.peak_views) DESC) AS rank_by_avg_views
FROM videos v
JOIN categories c ON v.category_id = c.category_id
GROUP BY c.category_name
ORDER BY rank_by_avg_views;


-- ====================================================================
-- QUERY 2: Sentiment Impact on Views, Engagement, and Like Ratio
-- Uncovers whether positive, negative, or neutral titles drive more views
-- ====================================================================
SELECT 
    v.title_sentiment_label,
    COUNT(DISTINCT v.video_id) AS video_count,
    ROUND(COUNT(DISTINCT v.video_id) * 100.0 / (SELECT COUNT(*) FROM videos), 2) AS pct_of_library,
    ROUND(AVG(v.peak_views), 0) AS avg_views,
    ROUND(AVG(v.peak_likes), 0) AS avg_likes,
    ROUND(AVG(v.peak_engagement_rate), 2) AS avg_engagement_pct,
    ROUND(AVG(v.peak_like_ratio) * 100, 2) AS avg_positive_like_pct,
    ROUND(AVG(v.days_to_trend), 2) AS avg_days_to_reach_trending,
    ROUND(AVG(v.trending_days_count), 2) AS avg_trending_duration_days
FROM videos v
GROUP BY v.title_sentiment_label
ORDER BY avg_views DESC;


-- ====================================================================
-- QUERY 3: Sentiment Distribution by Category
-- Identifies genres with highest positive/negative emotional polarity
-- ====================================================================
SELECT 
    c.category_name,
    COUNT(*) AS total_videos,
    ROUND(AVG(v.title_sentiment_score), 3) AS avg_sentiment_score,
    SUM(CASE WHEN v.title_sentiment_label = 'Positive' THEN 1 ELSE 0 END) AS positive_titles,
    SUM(CASE WHEN v.title_sentiment_label = 'Neutral' THEN 1 ELSE 0 END) AS neutral_titles,
    SUM(CASE WHEN v.title_sentiment_label = 'Negative' THEN 1 ELSE 0 END) AS negative_titles,
    ROUND(100.0 * SUM(CASE WHEN v.title_sentiment_label = 'Positive' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_positive,
    ROUND(100.0 * SUM(CASE WHEN v.title_sentiment_label = 'Negative' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_negative
FROM videos v
JOIN categories c ON v.category_id = c.category_id
GROUP BY c.category_name
HAVING COUNT(*) >= 100
ORDER BY avg_sentiment_score DESC;


-- ====================================================================
-- QUERY 4: Trending Duration Tiers & Viral Retention
-- Classifies video longevity on the trending tab into duration brackets
-- ====================================================================
SELECT 
    CASE 
        WHEN trending_days_count = 1 THEN '1 Day (Flash Trend)'
        WHEN trending_days_count BETWEEN 2 AND 4 THEN '2-4 Days (Standard)'
        WHEN trending_days_count BETWEEN 5 AND 9 THEN '5-9 Days (Extended)'
        ELSE '10+ Days (Viral Mega-Hit)'
    END AS duration_tier,
    COUNT(*) AS total_videos,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM videos), 2) AS pct_of_videos,
    ROUND(AVG(peak_views), 0) AS avg_peak_views,
    ROUND(AVG(peak_likes), 0) AS avg_peak_likes,
    ROUND(AVG(peak_engagement_rate), 2) AS avg_engagement_pct,
    ROUND(AVG(title_caps_ratio) * 100, 1) AS avg_title_caps_pct
FROM videos
GROUP BY duration_tier
ORDER BY avg_peak_views DESC;


-- ====================================================================
-- QUERY 5: Optimal Publishing Windows (Hour of Day & Day of Week)
-- ====================================================================
SELECT 
    publish_day_name,
    publish_hour,
    COUNT(*) AS videos_published,
    ROUND(AVG(peak_views), 0) AS avg_views,
    ROUND(AVG(days_to_trend), 2) AS avg_days_to_trend,
    RANK() OVER (ORDER BY AVG(peak_views) DESC) AS rank_by_views
FROM videos
GROUP BY publish_day_name, publish_hour
ORDER BY rank_by_views
LIMIT 20;


-- ====================================================================
-- QUERY 6: Top 10 Dominant Channels Across Regions
-- ====================================================================
SELECT 
    region,
    channel_title,
    COUNT(DISTINCT video_id) AS trending_videos_count,
    ROUND(AVG(peak_views), 0) AS avg_views_per_video,
    MAX(peak_views) AS top_video_views,
    ROUND(AVG(trending_days_count), 1) AS avg_days_on_trending,
    RANK() OVER (PARTITION BY region ORDER BY COUNT(DISTINCT video_id) DESC) as channel_rank
FROM videos
GROUP BY region, channel_title
HAVING COUNT(DISTINCT video_id) >= 5
ORDER BY region, channel_rank
LIMIT 30;
