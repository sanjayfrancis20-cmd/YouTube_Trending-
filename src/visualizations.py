"""
Visualizations Pipeline for YouTube Trending Video Analytics.
Generates publication-quality charts using Matplotlib and Seaborn:
1. Region-wise category popularity & view rankings
2. Sentiment distribution & engagement across countries
3. Time-series trending duration & publishing latency dynamics
4. Sentiment impact matrix (views vs engagement)
5. Optimal publishing window heatmaps
6. Multi-metric correlation matrix
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed')
FIG_DIR = os.path.join(BASE_DIR, 'reports', 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

# Styling Configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eaeaea'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

PALETTE = {
    'US': '#1f77b4',     # Classic Navy Blue
    'CA': '#e74c3c',     # Crimson Maple
    'IN': '#f39c12',     # Saffron Orange
    'Positive': '#2ecc71',
    'Neutral': '#95a5a6',
    'Negative': '#e74c3c'
}

def load_data():
    """Load cleaned snapshot and summary data."""
    summary_path = os.path.join(DATA_PROC_DIR, 'youtube_trending_summary.csv')
    cleaned_path = os.path.join(DATA_PROC_DIR, 'youtube_trending_cleaned.csv')
    
    df_summary = pd.read_csv(summary_path)
    df_clean = pd.read_csv(cleaned_path)
    
    # Ensure datetime parsing
    df_clean['trending_date'] = pd.to_datetime(df_clean['trending_date'])
    df_clean['publish_date'] = pd.to_datetime(df_clean['publish_date'])
    df_summary['trending_date'] = pd.to_datetime(df_summary['trending_date'])
    df_summary['publish_date'] = pd.to_datetime(df_summary['publish_date'])
    
    return df_summary, df_clean

def plot_region_category_comparison(df_summary):
    """Plot 1: Regional comparison of top categories by average views."""
    print("Generating Figure 1: Region-wise Category Comparison...")
    
    # Calculate average views per region and category (minimum 20 videos)
    cat_region = df_summary.groupby(['region', 'category_name']).filter(lambda x: len(x) >= 20)
    agg = cat_region.groupby(['region', 'category_name'])['peak_views'].mean().reset_index()
    
    # Select top 8 categories overall
    top_cats = df_summary.groupby('category_name')['peak_views'].mean().nlargest(8).index.tolist()
    agg_top = agg[agg['category_name'].isin(top_cats)].copy()
    agg_top['avg_views_millions'] = agg_top['peak_views'] / 1e6
    
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    
    sns.barplot(
        data=agg_top,
        x='avg_views_millions',
        y='category_name',
        hue='region',
        palette=PALETTE,
        ax=ax,
        order=top_cats,
        edgecolor='black',
        linewidth=0.5
    )
    
    ax.set_title("Top YouTube Categories by Average Views Across Regions", fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel("Average Peak Views (Millions)", fontsize=12, labelpad=10)
    ax.set_ylabel("Category / Genre", fontsize=12)
    ax.legend(title='Region', frameon=True, facecolor='white', framealpha=0.9)
    
    # Add value annotations
    for p in ax.patches:
        val = p.get_width()
        if val > 0.1 and not np.isnan(val):
            ax.annotate(f"{val:.1f}M",
                        (p.get_x() + val, p.get_y() + p.get_height() / 2.),
                        xytext=(5, 0), textcoords="offset points",
                        ha='left', va='center', fontsize=8, color='#333333')
            
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig1_region_category_comparison.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def plot_sentiment_distribution_by_region(df_summary):
    """Plot 2: Sentiment distribution and breakdown across regions."""
    print("Generating Figure 2: Regional Sentiment Distribution...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    
    # Panel 1: Percentage of Sentiment by Region
    sentiment_pct = df_summary.groupby(['region', 'title_sentiment_label']).size().unstack(fill_value=0)
    sentiment_pct = sentiment_pct.div(sentiment_pct.sum(axis=1), axis=0) * 100
    
    sentiment_pct[['Positive', 'Neutral', 'Negative']].plot(
        kind='bar',
        stacked=True,
        color=[PALETTE['Positive'], PALETTE['Neutral'], PALETTE['Negative']],
        edgecolor='black',
        linewidth=0.6,
        ax=ax1
    )
    ax1.set_title("Title Sentiment Breakdown by Region (%)", fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlabel("Region", fontsize=11)
    ax1.set_ylabel("Percentage (%)", fontsize=11)
    ax1.set_xticklabels(['Canada (CA)', 'India (IN)', 'United States (US)'], rotation=0)
    ax1.legend(title='Sentiment', frameon=True, facecolor='white')
    
    for p in ax1.patches:
        h = p.get_height()
        if h > 5:
            ax1.annotate(f"{h:.1f}%",
                         (p.get_x() + p.get_width() / 2., p.get_y() + h / 2.),
                         ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # Panel 2: Distribution of Sentiment Scores (KDE)
    for reg, col in [('US', PALETTE['US']), ('CA', PALETTE['CA']), ('IN', PALETTE['IN'])]:
        reg_data = df_summary[df_summary['region'] == reg]['title_sentiment_score']
        sns.kdeplot(reg_data, ax=ax2, label=reg, color=col, linewidth=2, fill=True, alpha=0.15)
        
    ax2.set_title("Continuous Sentiment Polarity Density by Region", fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlabel("VADER Compound Score (-1.0 Negative to +1.0 Positive)", fontsize=11)
    ax2.set_ylabel("Density", fontsize=11)
    ax2.axvline(0, color='gray', linestyle=':', alpha=0.8)
    ax2.axvline(0.05, color='green', linestyle='--', alpha=0.4, label='Positive threshold')
    ax2.axvline(-0.05, color='red', linestyle='--', alpha=0.4, label='Negative threshold')
    ax2.legend(frameon=True, facecolor='white')
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig2_sentiment_distribution_by_region.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def plot_trending_duration_timeseries(df_summary, df_clean):
    """Plot 3: Time-series trending duration & publishing latency dynamics."""
    print("Generating Figure 3: Trending Duration Dynamics...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=300)
    
    # Panel 1: Duration Tiers distribution
    duration_tiers = pd.cut(
        df_summary['trending_days_count'],
        bins=[0, 1, 4, 9, 100],
        labels=['1 Day (Flash)', '2-4 Days (Standard)', '5-9 Days (Extended)', '10+ Days (Viral Mega-Hit)']
    )
    df_summary_tiers = df_summary.copy()
    df_summary_tiers['duration_tier'] = duration_tiers
    
    tier_counts = df_summary_tiers.groupby(['region', 'duration_tier'], observed=False).size().unstack(fill_value=0)
    tier_pct = tier_counts.div(tier_counts.sum(axis=1), axis=0) * 100
    
    tier_pct.plot(
        kind='bar',
        stacked=True,
        colormap='viridis',
        edgecolor='black',
        linewidth=0.5,
        ax=ax1
    )
    ax1.set_title("Trending Shelf-Life Longevity by Region (%)", fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlabel("Region", fontsize=11)
    ax1.set_ylabel("Share of Unique Videos (%)", fontsize=11)
    ax1.set_xticklabels(['Canada (CA)', 'India (IN)', 'United States (US)'], rotation=0)
    ax1.legend(title='Duration Tier', frameon=True, facecolor='white')
    
    # Panel 2: Latency from Publish to Trending over Time (Monthly trend)
    df_clean_time = df_clean[df_clean['days_to_trend'] <= 30].copy()
    df_clean_time['trend_month'] = df_clean_time['trending_date'].dt.to_period('M').dt.to_timestamp()
    
    monthly_latency = df_clean_time.groupby(['trend_month', 'region'])['days_to_trend'].median().reset_index()
    
    for reg in ['US', 'CA', 'IN']:
        reg_df = monthly_latency[monthly_latency['region'] == reg]
        ax2.plot(reg_df['trend_month'], reg_df['days_to_trend'], marker='o', linewidth=2.2, label=f"{reg} Median Latency", color=PALETTE[reg])
        
    ax2.set_title("Monthly Evolution: Median Days from Upload to Trending", fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlabel("Trending Month", fontsize=11)
    ax2.set_ylabel("Median Days to Reach Trending Tab", fontsize=11)
    ax2.legend(frameon=True, facecolor='white')
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig3_trending_duration_dynamics.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def plot_sentiment_impact_matrix(df_summary):
    """Plot 4: Sentiment impact on views and engagement rate."""
    print("Generating Figure 4: Sentiment Impact Matrix...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    
    # Panel 1: Average Views by Sentiment Label
    sentiment_views = df_summary.groupby('title_sentiment_label')['peak_views'].mean() / 1e6
    colors = [PALETTE['Negative'], PALETTE['Neutral'], PALETTE['Positive']]
    
    order = ['Negative', 'Neutral', 'Positive']
    bars = ax1.bar(order, [sentiment_views[s] for s in order], color=colors, edgecolor='black', width=0.55, linewidth=0.6)
    ax1.set_title("Average Peak Views by Title Sentiment (Negativity Bias)", fontsize=13, fontweight='bold', pad=12)
    ax1.set_ylabel("Average Views (Millions)", fontsize=11)
    ax1.set_xlabel("Title Sentiment Classification", fontsize=11)
    
    for b in bars:
        h = b.get_height()
        ax1.annotate(f"{h:.2f}M", (b.get_x() + b.get_width() / 2., h),
                     xytext=(0, 5), textcoords="offset points", ha='center', fontsize=10, fontweight='bold')
                     
    # Panel 2: Engagement Rate vs Sentiment Boxplot (without extreme outliers)
    sns.boxplot(
        data=df_summary,
        x='title_sentiment_label',
        y='engagement_rate',
        hue='title_sentiment_label',
        order=['Negative', 'Neutral', 'Positive'],
        palette=PALETTE,
        showfliers=False,
        ax=ax2,
        width=0.45,
        legend=False
    )
    ax2.set_title("Engagement Rate Distribution by Title Sentiment", fontsize=13, fontweight='bold', pad=12)
    ax2.set_ylabel("Engagement Rate (%) [(Likes+Dislikes+Comments)/Views]", fontsize=11)
    ax2.set_xlabel("Title Sentiment Classification", fontsize=11)
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig4_sentiment_impact_matrix.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def plot_publishing_window_heatmap(df_summary):
    """Plot 5: Optimal publishing time heatmaps (Day of Week vs Hour)."""
    print("Generating Figure 5: Publishing Window Heatmap...")
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    heatmap_data = df_summary.pivot_table(
        index='publish_day_name',
        columns='publish_hour',
        values='peak_views',
        aggfunc='mean'
    ).reindex(days_order) / 1e6
    
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    
    sns.heatmap(
        heatmap_data,
        cmap='YlGnBu',
        annot=True,
        fmt='.2f',
        cbar_kws={'label': 'Average Peak Views (Millions)'},
        linewidths=0.5,
        ax=ax
    )
    
    ax.set_title("Optimal Publishing Window: Average Peak Views by Upload Day & Hour (UTC)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Publish Hour of Day (0 to 23 UTC)", fontsize=11)
    ax.set_ylabel("Publish Day of Week", fontsize=11)
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig5_publishing_window_heatmap.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def plot_correlation_heatmap(df_summary):
    """Plot 6: Multi-metric correlation matrix."""
    print("Generating Figure 6: Correlation Matrix Heatmap...")
    
    corr_cols = [
        'peak_views', 'peak_likes', 'peak_comments', 'dislikes',
        'trending_days_count', 'days_to_trend', 'engagement_rate',
        'title_sentiment_score', 'tag_count', 'title_length', 'title_caps_ratio'
    ]
    
    col_labels = [
        'Views', 'Likes', 'Comments', 'Dislikes',
        'Days Trending', 'Days to Trend', 'Engagement %',
        'Sentiment Score', 'Tag Count', 'Title Length', 'Caps Ratio'
    ]
    
    corr_matrix = df_summary[corr_cols].corr()
    corr_matrix.columns = col_labels
    corr_matrix.index = col_labels
    
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    
    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap='vlag',
        vmin=-0.5,
        vmax=1.0,
        center=0,
        annot=True,
        fmt='.2f',
        linewidths=0.8,
        cbar_kws={'label': 'Pearson Correlation Coefficient'},
        ax=ax
    )
    
    ax.set_title("Multi-Metric Correlation Matrix: YouTube Virality Drivers", fontsize=14, fontweight='bold', pad=15)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'fig6_correlation_matrix.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved: {fig_path}")

def run_all_visualizations():
    df_summary, df_clean = load_data()
    print(f"Loaded {len(df_summary):,} summary records and {len(df_clean):,} snapshot records.")
    
    plot_region_category_comparison(df_summary)
    plot_sentiment_distribution_by_region(df_summary)
    plot_trending_duration_timeseries(df_summary, df_clean)
    plot_sentiment_impact_matrix(df_summary)
    plot_publishing_window_heatmap(df_summary)
    plot_correlation_heatmap(df_summary)
    
    print("\nAll 6 visualization artifacts successfully generated in reports/figures/!")

if __name__ == '__main__':
    run_all_visualizations()
