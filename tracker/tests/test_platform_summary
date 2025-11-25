import pandas as pd
import visuals

def test_platform_summary_basic():
    df = pd.DataFrame({
        "Platform": ["TikTok", "YouTube", "TikTok"],
        "Minutes": [10, 20, 30]
    })

    labels, data = visuals.get_platform_summary(df)

    assert labels == ["TikTok", "YouTube"]
    # TikTok = 10 + 30 = 40, YouTube = 20
    assert data == [40, 20]


def test_platform_summary_empty_df():
    df = pd.DataFrame()
    labels, data = visuals.get_platform_summary(df)
    assert labels == []
    assert data == []


def test_platform_summary_missing_column():
    df = pd.DataFrame({"Minutes": [10, 20]})
    labels, data = visuals.get_platform_summary(df)
    assert labels == []
    assert data == []
