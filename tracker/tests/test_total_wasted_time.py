import pandas as pd
from tracker import visuals

def test_total_wasted_time_basic():
    df = pd.DataFrame({
        "Minutes": [10, 20, 30]
    })
    assert visuals.get_total_wasted_time(df) == 60


def test_total_wasted_time_empty_df():
    df = pd.DataFrame()
    assert visuals.get_total_wasted_time(df) == 0


def test_total_wasted_time_missing_column():
    df = pd.DataFrame({"Other": [10, 20]})
    assert visuals.get_total_wasted_time(df) == 0
