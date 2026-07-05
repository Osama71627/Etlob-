from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)


class Ad(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')
    title = models.CharField(max_length=200, blank=True)
    purpose = models.CharField(max_length=50)
    section = models.CharField(max_length=50)
    specialty = models.CharField(max_length=50)
    image_0 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_1 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='ads/', blank=True, null=True)
    text_ar = models.TextField(blank=True)
    text_en = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.purpose} - {self.user.username}'
