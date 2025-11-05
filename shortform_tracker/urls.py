from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tracker.urls')),  # Connects to your app
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

]