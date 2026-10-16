/**
 * Interactive Executive Dashboard Application
 * Handles data loading, region filtering, KPI updates, Chart.js visualizations, and video table search.
 */

let dashboardData = null;
let currentRegion = 'ALL';
let chartInstances = {};

// Color tokens matching the design system
const THEME = {
  cyan: '#38bdf8',
  blue: '#3b82f6',
  green: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  purple: '#a855f7',
  muted: '#64748b',
  grid: 'rgba(255, 255, 255, 0.05)',
  text: '#94a3b8'
};

// Formatting helpers
function formatNumber(num) {
  if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toLocaleString();
}

async function initDashboard() {
  try {
    const res = await fetch('data.json');
    if (!res.ok) throw new Error('Failed to load dashboard data');
    dashboardData = await res.json();
    
    setupEventListeners();
    renderRegion(currentRegion);
  } catch (err) {
    console.error('Error initializing dashboard:', err);
    document.querySelector('.dashboard-container').innerHTML += `
      <div style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; margin-top: 20px; color: #fca5a5;">
        <strong>Error Loading Data:</strong> ${err.message}. Ensure you run a local HTTP server (e.g., <code>python -m http.server</code>).
      </div>
    `;
  }
}

function setupEventListeners() {
  // Region Tab buttons
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      currentRegion = btn.dataset.region;
      renderRegion(currentRegion);
    });
  });

  // Table Search Input
  const searchInput = document.getElementById('tableSearchInput');
  searchInput.addEventListener('input', (e) => {
    filterTable(e.target.value.toLowerCase());
  });
}

function renderRegion(regionKey) {
  const data = dashboardData[regionKey];
  if (!data) return;

  // 1. Update KPIs
  document.getElementById('kpiTotalVideos').textContent = data.metrics.total_videos.toLocaleString();
  document.getElementById('kpiAvgViews').textContent = formatNumber(data.metrics.avg_views);
  document.getElementById('kpiAvgEngagement').textContent = data.metrics.avg_engagement + '%';
  document.getElementById('kpiAvgDuration').textContent = data.metrics.avg_days_trending + ' Days';
  
  // Find highest sentiment
  const topSentiment = [...data.sentiments].sort((a, b) => b.count - a.count)[0];
  document.getElementById('kpiDominantSentiment').textContent = `${topSentiment.title_sentiment_label} (${topSentiment.pct}%)`;

  // 2. Render Charts
  renderCategoryChart(data.categories.slice(0, 8));
  renderSentimentChart(data.sentiments);
  renderDurationChart(data.durations);
  renderHourlyChart(data.hourly);

  // 3. Render Table
  renderVideosTable(data.top_videos);
}

function renderCategoryChart(categories) {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  if (chartInstances.category) chartInstances.category.destroy();

  const labels = categories.map(c => c.category_name);
  const views = categories.map(c => c.avg_views / 1e6);
  const engagements = categories.map(c => c.avg_engagement);

  chartInstances.category = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Average Views (Millions)',
        data: views,
        backgroundColor: 'rgba(56, 189, 248, 0.75)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        borderRadius: 6,
        hoverBackgroundColor: '#38bdf8'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          callbacks: {
            afterLabel: (ctx) => `Engagement: ${engagements[ctx.dataIndex]}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: THEME.grid },
          ticks: { color: THEME.text, callback: (v) => v + 'M' },
          title: { display: true, text: 'Average Views (Millions)', color: THEME.text, font: { size: 11 } }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f8fafc', font: { weight: '500' } }
        }
      }
    }
  });
}

function renderSentimentChart(sentiments) {
  const ctx = document.getElementById('sentimentChart').getContext('2d');
  if (chartInstances.sentiment) chartInstances.sentiment.destroy();

  const colorMap = {
    'Positive': THEME.green,
    'Neutral': THEME.muted,
    'Negative': THEME.rose
  };

  const labels = sentiments.map(s => s.title_sentiment_label);
  const data = sentiments.map(s => s.count);
  const colors = labels.map(l => colorMap[l] || '#94a3b8');

  chartInstances.sentiment = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderColor: '#0b0f19',
        borderWidth: 3,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          callbacks: {
            label: (ctx) => {
              const item = sentiments[ctx.dataIndex];
              return ` ${item.title_sentiment_label}: ${item.pct}% (${formatNumber(item.count)} videos)`;
            }
          }
        }
      }
    }
  });

  // Render custom legend below donut
  const legendContainer = document.getElementById('sentimentLegend');
  legendContainer.innerHTML = sentiments.map(s => `
    <div class="legend-item">
      <span class="legend-dot" style="background-color: ${colorMap[s.title_sentiment_label]};"></span>
      <span>${s.title_sentiment_label} (${s.pct}%)</span>
    </div>
  `).join('');
}

function renderDurationChart(durations) {
  const ctx = document.getElementById('durationChart').getContext('2d');
  if (chartInstances.duration) chartInstances.duration.destroy();

  const labels = durations.map(d => d.duration_tier);
  const counts = durations.map(d => d.count);
  const pcts = durations.map(d => d.pct);

  chartInstances.duration = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Videos',
        data: counts,
        backgroundColor: [
          'rgba(99, 102, 241, 0.7)',
          'rgba(59, 130, 246, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)'
        ],
        borderColor: ['#6366f1', '#3b82f6', '#10b981', '#f59e0b'],
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          callbacks: {
            label: (ctx) => ` ${formatNumber(ctx.raw)} videos (${pcts[ctx.dataIndex]}%)`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: THEME.text, font: { size: 10 } }
        },
        y: {
          grid: { color: THEME.grid },
          ticks: { color: THEME.text, callback: (v) => formatNumber(v) }
        }
      }
    }
  });
}

function renderHourlyChart(hourly) {
  const ctx = document.getElementById('hourlyChart').getContext('2d');
  if (chartInstances.hourly) chartInstances.hourly.destroy();

  const hours = hourly.map(h => `${h.publish_hour}:00`);
  const views = hourly.map(h => (h.avg_views / 1e6).toFixed(2));
  const counts = hourly.map(h => h.count);

  chartInstances.hourly = new Chart(ctx, {
    type: 'line',
    data: {
      labels: hours,
      datasets: [
        {
          label: 'Average Views (Millions)',
          data: views,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          yAxisID: 'y'
        },
        {
          label: 'Upload Count',
          data: counts,
          borderColor: 'rgba(56, 189, 248, 0.5)',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.3,
          borderWidth: 1.5,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: '#f8fafc', font: { size: 11 } }
        },
        tooltip: { backgroundColor: '#0f172a' }
      },
      scales: {
        x: {
          grid: { color: THEME.grid },
          ticks: { color: THEME.text, maxTicksLimit: 12 }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: THEME.grid },
          ticks: { color: '#f59e0b', callback: (v) => v + 'M' },
          title: { display: true, text: 'Avg Peak Views', color: '#f59e0b' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: THEME.cyan, callback: (v) => formatNumber(v) },
          title: { display: true, text: 'Upload Volume', color: THEME.cyan }
        }
      }
    }
  });
}

function renderVideosTable(videos) {
  const tbody = document.getElementById('videosTableBody');
  if (!videos || !videos.length) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px;">No video records available.</td></tr>`;
    return;
  }

  tbody.innerHTML = videos.map(v => {
    let badgeClass = 'badge-neutral';
    if (v.title_sentiment_label === 'Positive') badgeClass = 'badge-positive';
    if (v.title_sentiment_label === 'Negative') badgeClass = 'badge-negative';

    return `
      <tr>
        <td class="table-title" title="${escapeHtml(v.title)}">${escapeHtml(v.title)}</td>
        <td class="table-channel">${escapeHtml(v.channel_title)}</td>
        <td>${escapeHtml(v.category_name)}</td>
        <td><span class="badge badge-region">${v.region}</span></td>
        <td style="font-weight: 700; color: #ffffff;">${formatNumber(v.peak_views)}</td>
        <td>${v.engagement_rate}%</td>
        <td><span class="badge ${badgeClass}">${v.title_sentiment_label}</span></td>
        <td>${v.trending_days_count} d</td>
      </tr>
    `;
  }).join('');
}

function filterTable(query) {
  const rows = document.querySelectorAll('#videosTableBody tr');
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function(m) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[m];
  });
}

document.addEventListener('DOMContentLoaded', initDashboard);
