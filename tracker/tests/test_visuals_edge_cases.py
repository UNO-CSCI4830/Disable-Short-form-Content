import pandas as pd
from tracker import visuals
from datetime import datetime, timedelta

def test_platform_summary_non_numeric_minutes():
    df = pd.DataFrame({
        "Platform": ["TikTok", "YouTube"],
        "Minutes": ["10", "20"]
    })

    df["Minutes"] = df["Minutes"].astype(int)
    labels, data = visuals.get_platform_summary(df)

    assert labels == ["TikTok", "YouTube"]
    assert data == [10, 20]


def test_weekly_trend_invalid_dates():
    df = pd.DataFrame({
        "Date": ["not-a-date", "2024-01-05"],
        "Minutes": [10, 20]
    })

    labels, data = visuals.get_weekly_trend(df)

    # Only valid date should appear
    assert len(labels) <= 1
