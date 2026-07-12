"""
STEP 7 - INTERACTIVE DASHBOARD (Plotly)
Nexus Bank Capstone | Team 4

The brief specifically asks for an "interactive dashboard", and matplotlib
PNGs (Section 8's static charts) don't satisfy that on their own. This
script builds a genuinely interactive, self-contained HTML dashboard using
Plotly: hover tooltips, zoom/pan, a ticker toggle via the legend, and a
dropdown to switch between price/volatility views. No server, no Dash
install, no Tableau/Power BI license needed — just open the HTML file in
any browser.

Output: outputs/dashboard/nexus_bank_dashboard.html
"""

import os
import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
DASH_DIR = os.path.join(ROOT, "outputs", "dashboard")
os.makedirs(DASH_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
feat = pd.read_sql("SELECT * FROM price_features", conn, parse_dates=["date"])
txn = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

tickers = sorted(feat.ticker.unique())
colors = ["#1F3864", "#B08D57", "#2E86AB", "#C0392B", "#6A994E"]

# ---- Tab 1: Price trend with MA + Bollinger, toggle by ticker via legend ----
fig1 = go.Figure()
for i, t in enumerate(tickers):
    g = feat[feat.ticker == t]
    fig1.add_trace(go.Scatter(x=g.date, y=g.close, name=f"{t} Close", line=dict(color=colors[i % 5]),
                               visible=(i == 0)))
    fig1.add_trace(go.Scatter(x=g.date, y=g.MA30, name=f"{t} MA30", line=dict(color=colors[i % 5], dash="dot"),
                               visible=(i == 0)))
buttons = []
for i, t in enumerate(tickers):
    vis = [False] * (2 * len(tickers))
    vis[2*i] = True
    vis[2*i+1] = True
    buttons.append(dict(label=t, method="update", args=[{"visible": vis}, {"title": f"{t} — Price Trend with MA30"}]))
fig1.update_layout(updatemenus=[dict(active=0, buttons=buttons, x=1.1, y=1)],
                    title=f"{tickers[0]} — Price Trend with MA30", height=450,
                    xaxis_title="Date", yaxis_title="Price (USD)", hovermode="x unified")

# ---- Tab 2: Volatility, all tickers, legend-toggleable ----
fig2 = go.Figure()
for i, t in enumerate(tickers):
    g = feat[feat.ticker == t]
    fig2.add_trace(go.Scatter(x=g.date, y=g.Volatility20, name=t, line=dict(color=colors[i % 5])))
fig2.update_layout(title="20-Day Rolling Annualised Volatility (click legend to toggle tickers)",
                    height=420, xaxis_title="Date", yaxis_title="Volatility", hovermode="x unified")

# ---- Tab 3: Risk heatmap (interactive, hoverable) ----
pivot = feat.pivot(index="date", columns="ticker", values="returns")
corr = pivot.corr()
fig3 = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns,
                                  colorscale="RdBu", zmid=0, text=np.round(corr.values, 2),
                                  texttemplate="%{text}"))
fig3.update_layout(title="Portfolio Risk Heatmap — Return Correlations (hover for exact values)", height=450)

# ---- Tab 4: Fraud timeline, zoomable/pannable ----
txn_sorted = txn.sort_values("Time")
legit = txn_sorted[txn_sorted.Class == 0]
fraud = txn_sorted[txn_sorted.Class == 1]
fig4 = go.Figure()
fig4.add_trace(go.Scattergl(x=legit.Time/3600, y=legit.Amount, mode="markers",
                             marker=dict(size=3, opacity=0.3, color="#1F3864"), name="Legitimate"))
fig4.add_trace(go.Scattergl(x=fraud.Time/3600, y=fraud.Amount, mode="markers",
                             marker=dict(size=8, symbol="x", color="#C0392B"), name="Fraud"))
fig4.update_layout(title="Fraud Incident Timeline (zoom/pan enabled, hover for transaction detail)",
                    height=420, xaxis_title="Time (hours since start)", yaxis_title="Transaction Amount ($)")

# ---- Assemble a single-page dashboard with simple tab switching via HTML/JS ----
html_parts = []
for i, fig in enumerate([fig1, fig2, fig3, fig4], start=1):
    html_parts.append(fig.to_html(full_html=False, include_plotlyjs=(i == 1), div_id=f"chart{i}"))

page = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Nexus Bank Capstone — Interactive Dashboard (Team 4)</title>
<style>
  body {{ font-family: Calibri, Arial, sans-serif; margin: 0; background: #f7f7f7; }}
  header {{ background: #1F3864; color: white; padding: 20px 30px; }}
  header h1 {{ margin: 0; font-size: 22px; }}
  header p {{ margin: 4px 0 0; color: #d9d9d9; font-size: 14px; }}
  .tabs {{ display: flex; background: white; border-bottom: 2px solid #1F3864; }}
  .tab {{ padding: 14px 22px; cursor: pointer; font-weight: bold; color: #1F3864; }}
  .tab.active {{ background: #1F3864; color: white; }}
  .panel {{ display: none; padding: 20px; background: white; margin: 0 20px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
  .panel.active {{ display: block; }}
</style>
</head>
<body>
<header>
  <h1>Nexus Bank Financial Analytics — Interactive Dashboard</h1>
  <p>Team 4 | Hover, zoom, pan, and toggle series using the controls in each chart</p>
</header>
<div class="tabs">
  <div class="tab active" onclick="showTab(1)">Price Trend</div>
  <div class="tab" onclick="showTab(2)">Volatility</div>
  <div class="tab" onclick="showTab(3)">Risk Heatmap</div>
  <div class="tab" onclick="showTab(4)">Fraud Timeline</div>
</div>
<div id="panel1" class="panel active">{html_parts[0]}</div>
<div id="panel2" class="panel">{html_parts[1]}</div>
<div id="panel3" class="panel">{html_parts[2]}</div>
<div id="panel4" class="panel">{html_parts[3]}</div>
<script>
function showTab(n) {{
  for (let i = 1; i <= 4; i++) {{
    document.getElementById('panel' + i).classList.toggle('active', i === n);
    document.querySelectorAll('.tab')[i-1].classList.toggle('active', i === n);
  }}
  window.dispatchEvent(new Event('resize'));
}}
</script>
</body>
</html>
"""

out_path = os.path.join(DASH_DIR, "nexus_bank_dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(page)
print(f"Interactive dashboard written to {out_path}")
print(f"File size: {os.path.getsize(out_path) / 1024:.0f} KB")
