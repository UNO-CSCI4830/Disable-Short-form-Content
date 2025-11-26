import pytest
from django.contrib.auth.models import User
from tracker.models import UserProfile
from django.urls import reverse


@pytest.mark.django_db
def test_profile_and_code_creation():
    """
    Ensure that when a User is created, a related UserProfile is automatically
    created and assigned a 12-character share_code.
    """
    user = User.objects.create(username="testuser")
    profile = user.userprofile

    assert profile.share_code is not None
    assert len(profile.share_code) == 12


@pytest.mark.django_db
def test_regenerate_share_code():
    """
    Confirm that regenerate_share_code() generates a new 12-character code
    and that the new value differs from the old value.
    """
    user = User.objects.create(username="testuser")
    profile = user.userprofile

    old_code = profile.share_code
    new_code = profile.regenerate_share_code()

    assert new_code != old_code
    assert len(new_code) == 12


@pytest.mark.django_db
def test_get_share_url():
    """
    Verify that share_page() returns a URL containing the user's share_code.
    """
    user = User.objects.create(username="testuser")
    profile = user.userprofile

    url = profile.share_page()
    assert profile.share_code in url


@pytest.mark.django_db
def test_as_dict():
    """
    Test that as_dict() returns expected fields: username, email, and share_code.
    """
    user = User.objects.create(username="bob", email="bob@example.com")
    profile = user.userprofile

    d = profile.as_dict()

    assert d["username"] == "bob"
    assert d["email"] == "bob@example.com"
    assert d["share_code"] == profile.share_code
