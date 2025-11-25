import pandas as pd
from datetime import datetime, timedelta


def get_platform_summary(df):
    """
    Prepare platform usage totals for bar charts.
    Fully edge-case safe.
    """
    if df is None or df.empty:
        return [], []

    if not {"Platform", "Minutes"}.issubset(df.columns):
        return [], []

    # Convert Minutes safely to numeric
    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce").fillna(0)

    totals = df.groupby("Platform")["Minutes"].sum()
    return list(totals.index), list(totals.values)


def get_weekly_trend(df):
    """
    Prepare last 7 days usage data for line charts.
    Fully edge-case safe.
    """
    if df is None or df.empty or "Date" not in df.columns:
        return [], []

    # Coerce invalid dates to NaT
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    if df.empty:
        return [], []

    last_week = datetime.now() - timedelta(days=7)
    recent = df[df["Date"] >= last_week]

    if recent.empty:
        return [], []

    daily = recent.groupby("Date")["Minutes"].sum().reset_index()

    labels = daily["Date"].dt.strftime("%m/%d").tolist()
    data = daily["Minutes"].tolist()

    return labels, data


def get_total_wasted_time(df):
    """
    Sum all minutes; handles non-numeric, empty, missing column.
    """
    if df is None or df.empty or "Minutes" not in df.columns:
        return 0

    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce").fillna(0)
    return int(df["Minutes"].sum())
