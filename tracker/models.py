from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    share_code = models.CharField(max_length=12, unique=True, default='', blank=True)

    def save(self, *args, **kwargs):
        if not self.share_code:
            self.share_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.minutes} min on {self.date}"