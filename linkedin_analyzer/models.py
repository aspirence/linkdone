
from django.db import models

class ProfileAnalysis(models.Model):
    name = models.CharField(max_length=200)
    headline = models.TextField()
    summary = models.TextField()
    experience_years = models.IntegerField()
    education_level = models.CharField(max_length=100)
    skills_count = models.IntegerField()
    connections_count = models.IntegerField()
    posts_per_month = models.IntegerField()
    recommendations_received = models.IntegerField()
    volunteer_experience = models.BooleanField(default=False)
    certifications_count = models.IntegerField()
    languages_count = models.IntegerField()
    
    # Calculated scores
    profile_completeness_score = models.FloatField(default=0)
    engagement_score = models.FloatField(default=0)
    professional_score = models.FloatField(default=0)
    network_score = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.overall_score}/100"
