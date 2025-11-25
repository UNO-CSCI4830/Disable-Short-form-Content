from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.home, name='home'),
    path('stats/', views.stats, name='stats'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('resources/', views.resources, name='resources'),
    path('accounts/', include('django.contrib.auth.urls')),
    path("track-user/", views.track_user, name="track_user"),
]
