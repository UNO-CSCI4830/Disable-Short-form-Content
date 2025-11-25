import pandas as pd
from datetime import datetime, timedelta
from tracker import visuals

def test_weekly_trend_basic():
    today = datetime.now()
    df = pd.DataFrame({
        "Date": [today - timedelta(days=i) for i in reversed(range(3))],  # reversed!
        "Minutes": [10, 20, 30]
    })


    labels, data = visuals.get_weekly_trend(df)

    # Should produce 3 formatted dates
    assert len(labels) == 3
    assert data == [10, 20, 30]


def test_weekly_trend_empty():
    df = pd.DataFrame()
    labels, data = visuals.get_weekly_trend(df)
    assert labels == []
    assert data == []


def test_weekly_trend_no_recent_data():
    df = pd.DataFrame({
        "Date": [datetime(2000, 1, 1)],
        "Minutes": [50]
    })

    labels, data = visuals.get_weekly_trend(df)
    assert labels == []
    assert data == []
