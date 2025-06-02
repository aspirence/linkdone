
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import math
from .models import ProfileAnalysis
from .linkedin_scraper import LinkedInProfileScraper

def index(request):
    return render(request, 'linkedin_analyzer/index.html')

@csrf_exempt
def analyze_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check if URL is provided for automatic extraction
            linkedin_url = data.get('linkedin_url')
            if linkedin_url:
                scraper = LinkedInProfileScraper()
                try:
                    profile_data = scraper.extract_profile_data(linkedin_url)
                    # Use scraped data
                    analysis = ProfileAnalysis(
                        name=profile_data['name'],
                        headline=profile_data['headline'],
                        summary=profile_data['summary'],
                        experience_years=int(profile_data['experience_years']),
                        education_level=profile_data['education_level'],
                        skills_count=int(profile_data['skills_count']),
                        connections_count=int(profile_data['connections_count']),
                        posts_per_month=int(profile_data['posts_per_month']),
                        recommendations_received=int(profile_data['recommendations_received']),
                        volunteer_experience=profile_data['volunteer_experience'],
                        certifications_count=int(profile_data['certifications_count']),
                        languages_count=int(profile_data['languages_count']),
                    )
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Failed to scrape profile: {str(e)}'})
            else:
                # Use manual input data
                analysis = ProfileAnalysis(
                    name=data.get('name', ''),
                    headline=data.get('headline', ''),
                    summary=data.get('summary', ''),
                    experience_years=int(data.get('experience_years', 0)),
                    education_level=data.get('education_level', ''),
                    skills_count=int(data.get('skills_count', 0)),
                    connections_count=int(data.get('connections_count', 0)),
                    posts_per_month=int(data.get('posts_per_month', 0)),
                    recommendations_received=int(data.get('recommendations_received', 0)),
                    volunteer_experience=data.get('volunteer_experience', False),
                    certifications_count=int(data.get('certifications_count', 0)),
                    languages_count=int(data.get('languages_count', 0)),
                )
            
            # Calculate AI-powered scores
            scores = calculate_profile_scores(analysis)
            
            analysis.profile_completeness_score = scores['completeness']
            analysis.engagement_score = scores['engagement']
            analysis.professional_score = scores['professional']
            analysis.network_score = scores['network']
            analysis.overall_score = scores['overall']
            
            analysis.save()
            
            # Generate recommendations
            recommendations = generate_recommendations(analysis)
            
            return JsonResponse({
                'success': True,
                'scores': scores,
                'recommendations': recommendations,
                'analysis_id': analysis.id,
                'redirect_url': f'/results/{analysis.id}/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def calculate_profile_scores(profile):
    """AI-powered scoring algorithm based on LinkedIn best practices"""
    
    # Profile Completeness Score (0-100)
    completeness_factors = {
        'headline': 15 if len(profile.headline) > 50 else len(profile.headline) * 0.3,
        'summary': 20 if len(profile.summary) > 200 else len(profile.summary) * 0.1,
        'skills': min(profile.skills_count * 2, 25),
        'education': 15 if profile.education_level else 0,
        'certifications': min(profile.certifications_count * 5, 15),
        'languages': min(profile.languages_count * 3, 10)
    }
    completeness_score = sum(completeness_factors.values())
    
    # Engagement Score (0-100)
    engagement_factors = {
        'posts_frequency': min(profile.posts_per_month * 8, 40),
        'recommendations': min(profile.recommendations_received * 10, 30),
        'volunteer': 20 if profile.volunteer_experience else 0,
        'activity_consistency': 10 if profile.posts_per_month >= 2 else profile.posts_per_month * 5
    }
    engagement_score = sum(engagement_factors.values())
    
    # Professional Score (0-100)
    professional_factors = {
        'experience': min(profile.experience_years * 8, 40),
        'headline_quality': 25 if any(keyword in profile.headline.lower() for keyword in ['specialist', 'manager', 'director', 'expert', 'consultant']) else 10,
        'summary_quality': 25 if len(profile.summary) > 300 else 10,
        'certifications_relevance': min(profile.certifications_count * 10, 30)
    }
    professional_score = sum(professional_factors.values())
    
    # Network Score (0-100)
    if profile.connections_count <= 50:
        network_base = profile.connections_count * 0.8
    elif profile.connections_count <= 500:
        network_base = 40 + (profile.connections_count - 50) * 0.11
    else:
        network_base = 90 + min((profile.connections_count - 500) * 0.01, 10)
    
    network_score = min(network_base, 100)
    
    # Overall Score (weighted average)
    weights = {
        'completeness': 0.25,
        'engagement': 0.20,
        'professional': 0.35,
        'network': 0.20
    }
    
    overall_score = (
        completeness_score * weights['completeness'] +
        engagement_score * weights['engagement'] +
        professional_score * weights['professional'] +
        network_score * weights['network']
    )
    
    return {
        'completeness': round(completeness_score, 1),
        'engagement': round(engagement_score, 1),
        'professional': round(professional_score, 1),
        'network': round(network_score, 1),
        'overall': round(overall_score, 1)
    }

def generate_recommendations(profile):
    """AI-generated recommendations based on profile analysis"""
    recommendations = []
    
    # Profile completeness recommendations
    if len(profile.headline) < 50:
        recommendations.append({
            'category': 'Profile Completeness',
            'priority': 'High',
            'suggestion': 'Expand your headline to include key skills and value proposition (aim for 50+ characters)',
            'impact': '+15 points'
        })
    
    if len(profile.summary) < 200:
        recommendations.append({
            'category': 'Profile Completeness',
            'priority': 'High',
            'suggestion': 'Write a comprehensive summary showcasing your achievements and goals (200+ words)',
            'impact': '+20 points'
        })
    
    if profile.skills_count < 10:
        recommendations.append({
            'category': 'Profile Completeness',
            'priority': 'Medium',
            'suggestion': f'Add more relevant skills (current: {profile.skills_count}, recommended: 10+)',
            'impact': f'+{(10 - profile.skills_count) * 2} points'
        })
    
    # Engagement recommendations
    if profile.posts_per_month < 2:
        recommendations.append({
            'category': 'Engagement',
            'priority': 'High',
            'suggestion': 'Increase posting frequency to 2-3 times per month for better visibility',
            'impact': '+15 points'
        })
    
    if profile.recommendations_received < 3:
        recommendations.append({
            'category': 'Engagement',
            'priority': 'Medium',
            'suggestion': 'Request recommendations from colleagues and clients',
            'impact': '+20 points'
        })
    
    # Professional recommendations
    if profile.certifications_count == 0:
        recommendations.append({
            'category': 'Professional Development',
            'priority': 'Medium',
            'suggestion': 'Obtain relevant industry certifications to boost credibility',
            'impact': '+25 points'
        })
    
    # Network recommendations
    if profile.connections_count < 100:
        recommendations.append({
            'category': 'Networking',
            'priority': 'High',
            'suggestion': 'Expand your network by connecting with industry professionals (aim for 100+ connections)',
            'impact': '+30 points'
        })
    
    return recommendations

@csrf_exempt
def validate_linkedin_url(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url', '')
            
            scraper = LinkedInProfileScraper()
            is_valid = scraper.validate_linkedin_url(url)
            
            return JsonResponse({'valid': is_valid})
        except Exception as e:
            return JsonResponse({'valid': False, 'error': str(e)})
    
    return JsonResponse({'valid': False, 'error': 'Invalid request method'})

def results(request, analysis_id):
    try:
        analysis = ProfileAnalysis.objects.get(id=analysis_id)
        
        # Generate recommendations for display
        recommendations = generate_recommendations(analysis)
        
        context = {
            'analysis': analysis,
            'recommendations': recommendations
        }
        
        return render(request, 'linkedin_analyzer/results.html', context)
    except ProfileAnalysis.DoesNotExist:
        return render(request, 'linkedin_analyzer/index.html', {
            'error': 'Analysis not found. Please try analyzing your profile again.'
        })

def get_analysis_history(request):
    analyses = ProfileAnalysis.objects.order_by('-created_at')[:10]
    data = [{
        'id': analysis.id,
        'name': analysis.name,
        'overall_score': analysis.overall_score,
        'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M')
    } for analysis in analyses]
    
    return JsonResponse({'analyses': data})
