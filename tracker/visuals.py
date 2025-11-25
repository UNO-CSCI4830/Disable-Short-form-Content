import pandas as pd
from datetime import datetime, timedelta


def get_platform_summary(df):
    """
    Prepare platform usage totals for bar charts.
    Returns (labels, data) lists.
    """
    if df.empty or "Platform" not in df.columns:
        return [], []

    totals = df.groupby("Platform")["Minutes"].sum()

    labels = list(totals.index)
    data = list(totals.values)

    return labels, data


def get_weekly_trend(df):
    """
    Prepare last 7 days usage data for line charts.
    Returns (labels, data) lists.
    """
    if df.empty or "Date" not in df.columns:
        return [], []

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
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
    Sum all minutes to get total wasted time.
    """
    if df.empty or "Minutes" not in df.columns:
        return 0

    return int(df["Minutes"].sum())
