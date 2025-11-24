from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    share_code = models.CharField(max_length=12, unique=True, default='', blank=True)

    def save(self, *args, **kwargs):
        if not self.share_code:
            self.share_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Profile"


    def regenerate_share_code(self):
        """Force-generate a new share code."""
        self.share_code = uuid.uuid4().hex[:12].upper()
        self.save()
        return self.share_code

    def get_share_url(self):
        return reverse("share-page", kwargs={"share_code": self.share_code})

    def as_dict(self):
        return {
            "username": self.user.username,
            "email": self.user.email,
            "share_code": self.share_code,
        }

    def is_complete(self): #check for share_code in account
        return bool(self.share_code and self.user.username)





class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.minutes} min on {self.date}"