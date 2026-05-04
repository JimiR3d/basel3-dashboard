# Basel III Capital Ratio Dashboard

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

A Python + Streamlit dashboard that monitors Basel III capital adequacy ratios for Nigerian banks against CBN (Central Bank of Nigeria) minimum thresholds. Upload a CSV of bank balance sheet data and instantly see whether capital ratios are compliant — with trend analysis and one-click PDF export.

## Who this is for

Nigerian bank compliance teams, risk analysts, fintech companies operating under CBN regulatory frameworks, and anyone working with Basel III capital adequacy requirements in the Nigerian banking sector.

## What it computes

| Ratio | Formula | CBN Minimum |
|-------|---------|-------------|
| CET1 Ratio | Common Equity Tier 1 / Risk-Weighted Assets | 8.0% |
| Tier 1 Capital Ratio | Tier 1 Capital / Risk-Weighted Assets | 9.5% |
| Total Capital Adequacy Ratio | Total Capital / Risk-Weighted Assets | 11.5% |

Ratios below threshold are flagged in red. A trend line shows quarter-over-quarter movement.

## Tech stack

- **Python** — core computation
- **Pandas** — data processing
- **Streamlit** — interactive web dashboard
- **Plotly** — charts and visualisation
- **ReportLab** — PDF report export

## How to run locally

```bash
# Clone the repo
git clone https://github.com/JimiR3d/basel3-dashboard.git
cd basel3-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload the included `data/sample_bank_data.csv` to see it in action.

## Live demo

_Coming soon — will be deployed to Streamlit Community Cloud._

## Project structure

```
basel3-dashboard/
├── app.py                  # Main Streamlit app
├── ratios.py               # Ratio computation logic
├── report.py               # PDF export logic
├── data/
│   └── sample_bank_data.csv
├── requirements.txt
├── .github/
│   └── workflows/
│       └── lint.yml
└── README.md
```

## Context

This is a clean-room rebuild demonstrating regulatory reporting competency with simulated data. Built by [Jimi Aboderin](https://github.com/JimiR3d) — a data analyst who previously built Basel III compliance automation pipelines for a Nigerian bank at Qucoon.

## License

MIT
