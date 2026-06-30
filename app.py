"""
Basel III Capital Ratio Dashboard

Interactive Streamlit dashboard for monitoring Basel III capital adequacy
ratios for Nigerian banks against CBN minimum thresholds.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ratios import CBN_THRESHOLDS, process_dataframe, get_breach_summary
from report import generate_pdf_report

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Basel III Capital Ratio Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .metric-card {
        background: linear-gradient(135deg, #0A0F1E 0%, #1a1f3e 100%);
        border-radius: 12px;
        padding: 24px;
        color: white;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 8px 0;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-threshold {
        font-size: 0.75rem;
        color: #6B7280;
        margin-top: 4px;
    }

    .compliant { color: #00D4AA; }
    .breach { color: #EF4444; }

    .header-section {
        background: linear-gradient(135deg, #0A0F1E 0%, #111827 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }

    .header-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .header-subtitle {
        color: #9CA3AF;
        font-size: 1rem;
    }

    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricLabel"] {
        color: #0A0F1E !important;
    }

    .breakdown-card {
        background: linear-gradient(135deg, #1a1f3e 0%, #0A0F1E 100%);
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .breakdown-label {
        color: #9CA3AF;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .breakdown-value {
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Data Source")
    st.markdown("Upload a CSV file with bank balance sheet data, or use the built-in sample.")

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help="CSV must contain: period, bank_name, cet1_capital, tier1_capital, total_capital, risk_weighted_assets"
    )

    use_sample = st.checkbox("Use sample data", value=True if uploaded_file is None else False)

    st.markdown("---")
    st.markdown("### CBN Thresholds")
    for ratio, threshold in CBN_THRESHOLDS.items():
        short_name = ratio.replace(" (%)", "")
        st.markdown(f"**{short_name}:** {threshold}%")

    st.markdown("---")
    st.markdown(
        "<small>Built by <a href='https://github.com/JimiR3d'>Jimi Aboderin</a></small>",
        unsafe_allow_html=True
    )


# ── Load data ────────────────────────────────────────────────────────
@st.cache_data
def load_data(file=None, use_sample=False):
    if file is not None:
        return pd.read_csv(file)
    elif use_sample:
        return pd.read_csv("data/sample_bank_data.csv")
    return None


df = load_data(uploaded_file, use_sample)

if df is None:
    st.info("👆 Upload a CSV file or check 'Use sample data' to get started.")
    st.stop()


# ── Process data ─────────────────────────────────────────────────────
processed = process_dataframe(df)
latest = processed.iloc[-1]
bank_name = latest.get("bank_name", "Bank")

# ── Header ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-section">
    <div class="header-title">🏦 Basel III Capital Adequacy Dashboard</div>
    <div class="header-subtitle">{bank_name} — {latest.get('period', 'Latest Period')}</div>
</div>
""", unsafe_allow_html=True)

# ── Key Metrics (3 cards) ────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

ratios_display = [
    ("CET1 Ratio (%)", "CET1 Ratio", "Common Equity Tier 1 / RWA"),
    ("Tier 1 Capital Ratio (%)", "Tier 1 Ratio", "Tier 1 Capital / RWA"),
    ("Total Capital Adequacy Ratio (%)", "Total CAR", "Total Capital / RWA"),
]

for col, (ratio_key, short_name, description) in zip([col1, col2, col3], ratios_display):
    value = latest[ratio_key]
    threshold = CBN_THRESHOLDS[ratio_key]
    is_compliant = value >= threshold
    status_class = "compliant" if is_compliant else "breach"
    status_text = "✓ Compliant" if is_compliant else "✗ BREACH"

    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{short_name}</div>
            <div class="metric-value {status_class}">{value:.2f}%</div>
            <div class="metric-threshold">CBN Min: {threshold}% — {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Trend Charts ─────────────────────────────────────────────────────
st.markdown("### 📈 Capital Ratio Trends")

fig = make_subplots(
    rows=1, cols=1,
    subplot_titles=["Capital Ratios vs CBN Minimum Thresholds"]
)

color_map = {
    "CET1 Ratio (%)": "#00D4AA",
    "Tier 1 Capital Ratio (%)": "#3B82F6",
    "Total Capital Adequacy Ratio (%)": "#8B5CF6",
}

threshold_colors = {
    "CET1 Ratio (%)": "rgba(0, 212, 170, 0.3)",
    "Tier 1 Capital Ratio (%)": "rgba(59, 130, 246, 0.3)",
    "Total Capital Adequacy Ratio (%)": "rgba(139, 92, 246, 0.3)",
}

for ratio_name in CBN_THRESHOLDS.keys():
    # Actual ratio line
    fig.add_trace(go.Scatter(
        x=processed["period"],
        y=processed[ratio_name],
        mode="lines+markers",
        name=ratio_name.replace(" (%)", ""),
        line=dict(color=color_map[ratio_name], width=3),
        marker=dict(size=8),
    ))

    # Threshold line
    threshold = CBN_THRESHOLDS[ratio_name]
    fig.add_trace(go.Scatter(
        x=processed["period"],
        y=[threshold] * len(processed),
        mode="lines",
        name=f"Min {ratio_name.replace(' (%)', '')}",
        line=dict(color=threshold_colors[ratio_name], width=2, dash="dash"),
        showlegend=False,
    ))

fig.update_layout(
    height=450,
    template="plotly_white",
    font=dict(family="Inter, sans-serif"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis_title="Ratio (%)",
    xaxis_title="Period",
    margin=dict(l=40, r=40, t=60, b=40),
)

st.plotly_chart(fig, use_container_width=True)


# ── Detailed Data Table ──────────────────────────────────────────────
st.markdown("### 📋 Detailed Ratio Data")

display_cols = ["period", "bank_name"] + list(CBN_THRESHOLDS.keys())
display_df = processed[display_cols].copy()

# Style the dataframe
def highlight_breaches(val, ratio_name):
    threshold = CBN_THRESHOLDS.get(ratio_name, 0)
    if isinstance(val, (int, float)) and val < threshold:
        return "background-color: #FEE2E2; color: #991B1B; font-weight: 600"
    elif isinstance(val, (int, float)):
        return "background-color: #D1FAE5; color: #065F46; font-weight: 600"
    return ""


styled_df = display_df.style
for ratio_name in CBN_THRESHOLDS.keys():
    styled_df = styled_df.map(
        lambda val, rn=ratio_name: highlight_breaches(val, rn),
        subset=[ratio_name]
    )

st.dataframe(styled_df, use_container_width=True, hide_index=True)


# ── Breach Alerts ────────────────────────────────────────────────────
breaches = get_breach_summary(df)

if breaches:
    st.markdown("### ⚠️ Breach Alerts")
    for breach in breaches:
        st.error(
            f"**{breach['period']}** — {breach['ratio'].replace(' (%)', '')} "
            f"at **{breach['value']}%** is below the CBN minimum of "
            f"**{breach['threshold']}%** (shortfall: {breach['shortfall']}pp)"
        )
else:
    st.success("✓ All ratios are above CBN minimum thresholds across all periods.")


# ── Capital Composition Breakdown ────────────────────────────────────
st.markdown("### 🏗️ Capital Composition — Latest Period")

if all(col in processed.columns for col in ["cet1_capital", "additional_tier1", "tier2_capital"]):
    comp_col1, comp_col2 = st.columns(2)

    with comp_col1:
        fig_comp = go.Figure(data=[go.Pie(
            labels=["CET1 Capital", "Additional Tier 1", "Tier 2 Capital"],
            values=[
                latest["cet1_capital"],
                latest.get("additional_tier1", 0),
                latest.get("tier2_capital", 0),
            ],
            hole=0.5,
            marker=dict(colors=["#00D4AA", "#3B82F6", "#8B5CF6"]),
            textinfo="label+percent",
            textfont=dict(size=12),
        )])

        fig_comp.update_layout(
            height=350,
            template="plotly_white",
            font=dict(family="Inter, sans-serif"),
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with comp_col2:
        st.markdown("**Capital Breakdown (₦ millions)**")

        breakdown_items = [("CET1 Capital", latest["cet1_capital"])]
        if "additional_tier1" in latest:
            breakdown_items.append(("Additional Tier 1", latest["additional_tier1"]))
        if "tier2_capital" in latest:
            breakdown_items.append(("Tier 2 Capital", latest["tier2_capital"]))
        breakdown_items.append(("Total Capital", latest["total_capital"]))
        breakdown_items.append(("Risk-Weighted Assets", latest["risk_weighted_assets"]))

        for label, value in breakdown_items:
            st.markdown(f"""
            <div class="breakdown-card">
                <div class="breakdown-label">{label}</div>
                <div class="breakdown-value">₦{value:,.0f}M</div>
            </div>
            """, unsafe_allow_html=True)


# ── PDF Export ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📄 Export Report")

if st.button("📥 Download PDF Report", type="primary"):
    pdf_bytes = generate_pdf_report(processed, bank_name)
    st.download_button(
        label="Click to download",
        data=pdf_bytes,
        file_name=f"basel3_report_{bank_name.lower().replace(' ', '_')}.pdf",
        mime="application/pdf",
    )
