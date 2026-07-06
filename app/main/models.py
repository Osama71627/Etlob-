from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = [
        ('user', 'مستخدم'),
        ('moderator', 'مشرف'),
        ('admin', 'مدير'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    warnings = models.IntegerField(default=0)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'مجاني'),
        ('basic', 'أساسي'),
        ('premium', 'مميز'),
        ('vip', 'VIP'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    max_ads = models.IntegerField(default=5)
    featured_ads = models.IntegerField(default=0)
    contact_visible = models.BooleanField(default=True)
    stars = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.get_plan_display()}'


class Notification(models.Model):
    TYPE_CHOICES = [
        ('warning', 'تحذير'),
        ('info', 'معلومات'),
        ('success', 'نجاح'),
        ('danger', 'خطأ'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} - {self.title}'


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Subscription.objects.create(user=instance)

post_save.connect(create_profile, sender=User)


class Ad(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')
    title = models.CharField(max_length=200, blank=True, db_index=True)
    purpose = models.CharField(max_length=50, db_index=True)
    section = models.CharField(max_length=50, db_index=True)
    specialty = models.CharField(max_length=50, db_index=True)
    image_0 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_1 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='ads/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='ads/', blank=True, null=True)
    text_ar = models.TextField(blank=True)
    text_en = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, default='draft', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.purpose} - {self.user.username}'


class StarPackage(models.Model):
    stars = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.stars} ⭐ = {self.price} ريال'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ad')

    def __str__(self):
        return f'{self.user.username} ❤️ {self.ad.id}'
