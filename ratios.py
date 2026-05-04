"""
Basel III Capital Ratio Computation Module

Computes CET1, Tier 1, and Total Capital Adequacy ratios
against CBN (Central Bank of Nigeria) minimum thresholds.
"""

import pandas as pd
from typing import Dict, List, Tuple

# CBN minimum capital ratio thresholds for Nigerian banks
# Reference: CBN Prudential Guidelines (aligned with Basel III)
CBN_THRESHOLDS = {
    "CET1 Ratio (%)": 8.0,
    "Tier 1 Capital Ratio (%)": 9.5,
    "Total Capital Adequacy Ratio (%)": 11.5,
}


def compute_cet1_ratio(cet1_capital: float, risk_weighted_assets: float) -> float:
    """
    Compute Common Equity Tier 1 (CET1) ratio.

    CET1 Ratio = CET1 Capital / Risk-Weighted Assets × 100

    CET1 capital includes: ordinary shares, retained earnings,
    disclosed reserves, and regulatory adjustments.
    """
    if risk_weighted_assets <= 0:
        return 0.0
    return round((cet1_capital / risk_weighted_assets) * 100, 2)


def compute_tier1_ratio(tier1_capital: float, risk_weighted_assets: float) -> float:
    """
    Compute Tier 1 Capital ratio.

    Tier 1 Ratio = Tier 1 Capital / Risk-Weighted Assets × 100

    Tier 1 capital = CET1 + Additional Tier 1 (AT1) capital
    (e.g., non-cumulative preference shares, contingent convertibles).
    """
    if risk_weighted_assets <= 0:
        return 0.0
    return round((tier1_capital / risk_weighted_assets) * 100, 2)


def compute_total_car(total_capital: float, risk_weighted_assets: float) -> float:
    """
    Compute Total Capital Adequacy Ratio (CAR).

    Total CAR = Total Capital / Risk-Weighted Assets × 100

    Total capital = Tier 1 + Tier 2 capital
    (Tier 2 includes subordinated debt, general loan-loss provisions).
    """
    if risk_weighted_assets <= 0:
        return 0.0
    return round((total_capital / risk_weighted_assets) * 100, 2)


def compute_all_ratios(row: pd.Series) -> Dict[str, float]:
    """
    Compute all three Basel III ratios from a single row of balance sheet data.

    Expected columns in row:
        - cet1_capital
        - tier1_capital (CET1 + Additional Tier 1)
        - total_capital (Tier 1 + Tier 2)
        - risk_weighted_assets
    """
    rwa = row["risk_weighted_assets"]
    return {
        "CET1 Ratio (%)": compute_cet1_ratio(row["cet1_capital"], rwa),
        "Tier 1 Capital Ratio (%)": compute_tier1_ratio(row["tier1_capital"], rwa),
        "Total Capital Adequacy Ratio (%)": compute_total_car(row["total_capital"], rwa),
    }


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a full DataFrame of bank balance sheet data.

    Adds computed ratio columns and breach flags for each period.

    Returns:
        DataFrame with original data plus ratio columns and breach flags.
    """
    ratios_list = df.apply(compute_all_ratios, axis=1).tolist()
    ratios_df = pd.DataFrame(ratios_list)

    result = pd.concat([df, ratios_df], axis=1)

    # Add breach flags
    for ratio_name, threshold in CBN_THRESHOLDS.items():
        flag_col = f"{ratio_name} — Breach"
        result[flag_col] = result[ratio_name] < threshold

    return result


def get_latest_ratios(df: pd.DataFrame) -> Dict[str, float]:
    """Get the most recent period's ratios."""
    processed = process_dataframe(df)
    latest = processed.iloc[-1]
    return {
        ratio: latest[ratio] for ratio in CBN_THRESHOLDS.keys()
    }


def get_breach_summary(df: pd.DataFrame) -> List[Dict[str, any]]:
    """
    Get a summary of all ratio breaches across all periods.

    Returns a list of dicts with period, ratio name, value, and threshold.
    """
    processed = process_dataframe(df)
    breaches = []

    for _, row in processed.iterrows():
        for ratio_name, threshold in CBN_THRESHOLDS.items():
            if row[ratio_name] < threshold:
                breaches.append({
                    "period": row.get("period", "Unknown"),
                    "ratio": ratio_name,
                    "value": row[ratio_name],
                    "threshold": threshold,
                    "shortfall": round(threshold - row[ratio_name], 2),
                })

    return breaches
