from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    share_code = models.CharField(max_length=12, unique=True, blank=True)
    friends = models.ManyToManyField("self", symmetrical=False, blank=True)

    def save(self, *args, **kwargs):
        if not self.share_code or len(self.share_code) != 12:
            self.share_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Profile"

    def regenerate_share_code(self):
        self.share_code = uuid.uuid4().hex[:12].upper()
        self.save()
        return self.share_code

    def share_page(self):
        return reverse("share-page", kwargs={"share_code": self.share_code})

    def as_dict(self):
        return {
            "username": self.user.username,
            "email": self.user.email,
            "share_code": self.share_code,
        }

    def is_complete(self):
        return bool(self.share_code and self.user.username)
class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.minutes} min on {self.date}"