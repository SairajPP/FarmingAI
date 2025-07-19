
from django.db import models
from django.contrib.auth.models import User

class Crop(models.Model):
    STAGE_CHOICES = [
        ('germination', 'Germination'),
        ('vegetative', 'Vegetative'),
        ('flowering', 'Flowering'),
        ('harvest', 'Harvest'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    date_planted = models.DateField()
    growth_stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    notes = models.TextField(blank=True)
    status = models.CharField(    max_length=20,
    choices=[('Growing', 'Growing'), ('Harvested', 'Harvested')],
    default='Growing'  # ← added default here
    )
    land_area = models.DecimalField(max_digits=10, decimal_places=2, help_text="In acres or hectares", default=1.0)


    
    def __str__(self):
        return f"{self.name} ({self.growth_stage})"

class ImageAnalysis(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='crop_analyses/')
    analysis_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.crop.name} on {self.timestamp.strftime('%Y-%m-%d')}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.URLField(blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.user.username
