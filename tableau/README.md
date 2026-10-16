# Tableau Integration Guide: YouTube Trending Video Analytics

This guide provides instructions for connecting and visualizing the sanitized **`youtube_trending_tableau.csv`** dataset in **Tableau Desktop / Tableau Public / Tableau Server**.

---

## 1. Connecting Data in Tableau
1. Open **Tableau**.
2. Under **Connect -> To a File**, select **Text file**.
3. Choose `tableau/youtube_trending_tableau.csv`.
4. Verify data types in the Data Source tab:
   - `video_id`, `title`, `channel_title`, `category_name`, `region`: **String**
   - `trending_date_str`, `publish_date_str`: **Date**
   - `publish_hour`, `views`, `likes`, `dislikes`, `comment_count`, `trending_days_count`: **Number (Whole)**
   - `engagement_rate`, `like_ratio`, `title_sentiment_score`, `title_caps_ratio`: **Number (Decimal)**

---

## 2. Recommended Calculated Fields

Create the following calculated fields in Tableau to enrich your analysis:

### A. Negativity Bias Flag
```tableau
IF [Title Sentiment Score] <= -0.05 THEN "Negative (Conflict/Drama)"
ELSEIF [Title Sentiment Score] >= 0.05 THEN "Positive (Uplifting)"
ELSE "Neutral (Informational)"
END
```

### B. Virality Velocity (Views Per Trending Day)
```tableau
[Views] / MAX([Trending Days Count], 1)
```

### C. Shelf-Life Tier
```tableau
IF [Trending Days Count] = 1 THEN "1 Day (Flash Trend)"
ELSEIF [Trending Days Count] <= 4 THEN "2-4 Days (Standard)"
ELSEIF [Trending Days Count] <= 9 THEN "5-9 Days (Extended)"
ELSE "10+ Days (Viral Mega-Hit)"
END
```

### D. Like-to-Dislike Ratio (%)
```tableau
ZN([Likes]) / (ZN([Likes]) + ZN([Dislikes])) * 100
```

---

## 3. Recommended Tableau Dashboard Layout

### Sheet 1: Regional Category Leaderboard
- **Rows**: `[Category Name]`
- **Columns**: `AVG([Views])`
- **Color**: `[Region]`
- **Filter**: `[Region]`, Top N Categories by `AVG([Views])`

### Sheet 2: Sentiment vs. Engagement Matrix
- **Columns**: `[Title Sentiment Label]`
- **Rows**: `AVG([Views])` (Dual Axis with `AVG([Engagement Rate])`)
- **Marks 1**: Bar Chart (Views)
- **Marks 2**: Line Chart (Engagement Rate)

### Sheet 3: Viral Retention Funnel
- **Rows**: `[Shelf-Life Tier]`
- **Columns**: `COUNTD([Video Id])` and `AVG([Views])`
- **Color**: `[Shelf-Life Tier]`

### Sheet 4: Optimal Publishing Clock
- **Columns**: `[Publish Hour]` (0 to 23)
- **Rows**: `[Publish Day Name]` (Mon to Sun)
- **Color**: `AVG([Views])` (Heatmap / Highlight Table)
