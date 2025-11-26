import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from tracker.views import get_pet_stats, home, stats, leaderboard
from datetime import datetime, timedelta


# ------------------------
# Fake Django Session
# ------------------------
class FakeSession(dict):
    """Simulates Django's session with a 'modified' flag."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False


# ------------------------
# Dummy Request Object
# ------------------------
class DummyRequest:
    def __init__(self, method="GET"):
        self.method = method
        self.session = FakeSession()
        self.POST = {}
        self.META = {}  # REQUIRED for CSRF
        self.user = MagicMock()
        self.user.is_authenticated = True


# ============================================================
# TEST: get_pet_stats() — daily average
# ============================================================
@patch("tracker.views.return_pet_info")
@patch("tracker.views.UserProfile.objects.get")
@patch("tracker.views.pd.read_csv")
@patch("tracker.views.os.path.exists")
def test_get_pet_stats_calculates_daily_avg(mock_exists, mock_read, mock_user, mock_pet):

    mock_exists.return_value = True

    df = pd.DataFrame({
        "Code": ["ABC123"],
        "Date": [datetime.now().isoformat()],
        "Platform": ["YouTube"],
        "Minutes": [30]
    })
    mock_read.return_value = df

    profile = MagicMock()
    profile.share_code = "ABC123"
    mock_user.return_value = profile

    mock_pet.return_value = ("egg.png", "Stage 1", 25)

    req = DummyRequest()
    req.session["focus_platform"] = "YouTube"
    req.session["points"] = 0

    data = get_pet_stats(req)

    assert "daily_avg" in data
    assert data["pet_image"] == "egg.png"


# ============================================================
# TEST: get_pet_stats() — points increase
# ============================================================
@patch("tracker.views.return_pet_info")
@patch("tracker.views.UserProfile.objects.get")
@patch("tracker.views.pd.read_csv")
@patch("tracker.views.os.path.exists")
def test_get_pet_stats_increases_points(mock_exists, mock_read, mock_user, mock_pet):

    mock_exists.return_value = True

    df = pd.DataFrame({
        "Code": ["ABC123"],
        "Date": [datetime.now().isoformat()],
        "Platform": ["YouTube"],
        "Minutes": [10]  # low usage => should reward
    })
    mock_read.return_value = df

    profile = MagicMock()
    profile.share_code = "ABC123"
    mock_user.return_value = profile

    mock_pet.return_value = ("dragon.png", "Stage 1", 40)

    req = DummyRequest()
    req.session["points"] = 0
    req.session["focus_platform"] = "YouTube"

    data = get_pet_stats(req)

    assert data["points"] == 10  # rewarded


# ============================================================
# TEST: home() — adding one entry
# ============================================================
@patch("tracker.views.return_pet_info")
@patch("tracker.views.pd.to_datetime")
@patch("tracker.views.UserProfile.objects.get")
@patch("tracker.views.pd.read_csv")
@patch("tracker.views.os.path.exists")
def test_home_add_entry(mock_exists, mock_read, mock_user, mock_datetime, mock_pet):

    mock_exists.return_value = True
    mock_pet.return_value = ("img.png", "stage", 0)

    df = pd.DataFrame(columns=["Code", "Date", "Platform", "Minutes"])
    mock_read.return_value = df

    profile = MagicMock()
    profile.share_code = "ABC123"
    mock_user.return_value = profile

    req = DummyRequest(method="POST")
    req.POST = {
        "add_entry": True,
        "platform": "YouTube",
        "minutes": "25",
        "date": "2025-11-01"
    }

    response = home(req)

    # CSV was read & processed
    mock_read.assert_called()


# ============================================================
# TEST: stats() — summary totals
# ============================================================
@patch("tracker.views.render")
@patch("tracker.views.return_pet_info")
@patch("tracker.views.UserProfile.objects.get")
@patch("tracker.views.pd.read_csv")
def test_stats_summary(mock_read, mock_user, mock_pet, mock_render):

    df = pd.DataFrame({
        "Code": ["X"],
        "Date": ["2025-11-01"],
        "Platform": ["TikTok"],
        "Minutes": [100]
    })
    mock_read.return_value = df

    profile = MagicMock()
    profile.share_code = "X"
    mock_user.return_value = profile

    mock_pet.return_value = ("egg.png", "stage", 0)

    mock_render.return_value = MagicMock()  # avoid real template rendering

    req = DummyRequest()

    stats(req)

    # render(request, template_name, context_dict)
    args, kwargs = mock_render.call_args
    context = args[2]   # FIXED

    assert context["total_minutes"] == 100




# ============================================================
# TEST: leaderboard() — sorting logic
# ============================================================
@patch("tracker.views.render")
@patch("tracker.views.pd.read_csv")
def test_leaderboard_logic(mock_read, mock_render):

    df = pd.DataFrame({
        "Code": ["A", "A", "B"],
        "Minutes": [30, 40, 20]
    })
    mock_read.return_value = df

    mock_render.return_value = MagicMock()  # don't render template

    req = DummyRequest()

    leaderboard(req)

    # render(request, template, context)
    args, kwargs = mock_render.call_args
    
    context = args[2]  # 3rd positional arg is the context dict
    board = context["leaderboard"]

    assert board[0]["Code"] == "B"
    assert board[1]["Code"] == "A"