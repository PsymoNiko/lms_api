from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    ROLE = [
        ('admin', 'Admin'),
        ('instructor', 'Instructor'),
        ('student', 'Student')
    ]
    role = models.CharField(max_length=10, choices=ROLE, default='student')

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        storage=None,
        height_field=None,
        width_field=None,
        max_length=255
    )
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"




@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)