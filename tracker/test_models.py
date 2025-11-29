import pytest
import os
from django.contrib.auth.models import User
from django.urls import reverse
from .petLogic import *
from PIL import Image


def test_daily_point_change():
    #creates fake totals for both yesterday's total, and today's total, then checks if points are added
    assert daily_point_change(30, 40, 42) == 43

def test_weekly_point_change():
    #creates fake weekly averages, tests for if they take more than the proper amount away when points < 10
    assert weekly_point_change(20, 10, 5) == 0


def test_safe_image(tmp_path):
    #set up fake image path
    path = tmp_path / "fakeimage.png"

    #use pillow to make an image at said fake path
    test_image = Image.new("RGB", (25, 25), "white")
    test_image.save(path)

    #set result variable
    result = safe_image(path)

    #test that the resulting path is the path from the created temp variable
    assert result == path

def test_return_pet_info():
    #tests that a null list [null, null, null] is returned when using out of bounds pet variable
    assert return_pet_info(4, 10) == [None, None, None]


