from google.cloud import aiplatform
from google.oauth2 import service_account

def interview_results(request, mock_id):
    interview = get_object_or_404(MockInterview, mock_id=mock_id, user=request.user)
    
    if request.method == 'POST':
        answers = json.loads(request.POST.get('answers', []))
        
        # Generate feedback using Gemini
        feedback = generate_ai_feedback(interview.questions, answers)
        
        # Save results to database
        InterviewResult.objects.update_or_create(
            interview=interview,
            defaults={
                'answers': answers,
                'feedback': feedback,
                'score': calculate_score(feedback)
            }
        )
        
    return render(request, 'dashboard/interview_results.html', {
        'interview': interview,
        'results': interview.results
    })

def generate_ai_feedback(questions, answers):
    credentials = service_account.Credentials.from_service_account_file('path/to/service-account.json')
    client = aiplatform.gapic.PredictionServiceClient(credentials=credentials)
    
    prompt = f"""
    Analyze these interview Q&A pairs and provide detailed feedback:
    
    {[
        f"Question: {q['Question']}\nExpected Answer: {q['Answer']}\nCandidate Answer: {a}\n\n"
        for q, a in zip(questions, answers)
    ]}
    
    Provide feedback on:
    1. Relevance to question
    2. Technical accuracy
    3. Communication clarity
    4. Areas for improvement
    5. Overall score (1-10)
    """
    
    response = client.predict(
        endpoint="projects/{project}/locations/{location}/publishers/google/models/gemini-pro",
        instances=[{"content": prompt}]
    )
    
    return response.predictions[0]['content'] 