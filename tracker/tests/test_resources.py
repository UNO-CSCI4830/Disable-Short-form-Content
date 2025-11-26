import pytest
import pandas as pd
from django.test import RequestFactory
from tracker.views import resources


@pytest.fixture
def fake_request():
    factory = RequestFactory()
    request = factory.get("/resources")
    request.session = {}

    # Add a mock authenticated user
    class MockUser:
        is_authenticated = True

    request.user = MockUser()
    return request


def test_no_csv_file_returns_defaults(monkeypatch, fake_request):
    monkeypatch.setattr("os.path.exists", lambda path: False)

    captured = {}

    def fake_render(req, template, context):
        captured["context"] = context
        return None

    monkeypatch.setattr("tracker.views.render", fake_render)

    resources(fake_request)
    context = captured["context"]

    assert context["most_used"] == "N/A"
    assert context["all_equal"] is False


def test_empty_csv_returns_defaults(monkeypatch, fake_request):
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("pandas.read_csv", lambda path: pd.DataFrame())

    captured = {}

    def fake_render(req, template, context):
        captured["context"] = context
        return None

    monkeypatch.setattr("tracker.views.render", fake_render)

    resources(fake_request)
    context = captured["context"]

    assert context["most_used"] == "N/A"
    assert context["all_equal"] is False


def test_correct_most_used_platform(monkeypatch, fake_request):
    monkeypatch.setattr("os.path.exists", lambda path: True)

    df = pd.DataFrame({
        "Platform": ["TikTok", "YouTube", "TikTok"],
        "Minutes": [10, 20, 30]
    })
    monkeypatch.setattr("pandas.read_csv", lambda path: df)

    captured = {}

    def fake_render(req, template, context):
        captured["context"] = context
        return None

    monkeypatch.setattr("tracker.views.render", fake_render)

    resources(fake_request)
    context = captured["context"]

    assert context["most_used"] == "TikTok"


def test_all_equal_true(monkeypatch, fake_request):
    monkeypatch.setattr("os.path.exists", lambda path: True)

    df = pd.DataFrame({
        "Platform": ["TikTok", "YouTube", "Other"],
        "Minutes": [30, 30, 99]
    })
    monkeypatch.setattr("pandas.read_csv", lambda path: df)

    captured = {}

    def fake_render(req, template, context):
        captured["context"] = context
        return None

    monkeypatch.setattr("tracker.views.render", fake_render)

    resources(fake_request)
    context = captured["context"]

    assert context["all_equal"] is True
