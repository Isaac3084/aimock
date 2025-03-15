from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .utils.gemini_api import generate_interview
from .models import MockInterview
import json

def home(request):
    return render(request, 'home/index.html')

@ensure_csrf_cookie
def create_interview(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Generate interview questions
            interview_data = generate_interview(
                data['jobPosition'],
                data['jobDesc'],
                data['jobExperience']
            )
            
            # Save to database
            interview = MockInterview.objects.create(
                json_mock_resp=json.dumps(interview_data) if isinstance(interview_data, dict) else interview_data,
                job_position=data['jobPosition'],
                job_desc=data['jobDesc'],
                job_experience=data['jobExperience'],
                created_by=request.user.email
            )
            
            return JsonResponse({
                'success': True,
                'mockId': str(interview.mock_id)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def interview_detail(request, mock_id):
    interview = get_object_or_404(MockInterview, mock_id=mock_id)
    return render(request, 'home/interview_detail.html', {
        'interview': interview
    }) 