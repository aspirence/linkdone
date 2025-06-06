
from django.urls import path
from . import views

app_name = 'linkedin_analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/', views.analyze_profile, name='analyze'),
    path('results/<int:analysis_id>/', views.results, name='results'),
    path('validate-url/', views.validate_linkedin_url, name='validate_url'),
    path('history/', views.get_analysis_history, name='history'),
]
