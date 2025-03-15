from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from home.models import MockInterview
from difflib import SequenceMatcher
import google.generativeai as genai
from django.conf import settings
import json
import base64
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import uuid

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

@login_required
def dashboard(request):
    return render(request, 'dashboard/index.html')

def logout_view(request):
    logout(request)
    return redirect('home:index')

def start_interview(request, mock_id):
    interview = get_object_or_404(MockInterview, mock_id=mock_id)
    questions = interview.json_mock_resp if isinstance(interview.json_mock_resp, dict) else json.loads(interview.json_mock_resp)
    
    return render(request, 'dashboard/start_interview.html', {
        'interview': interview,
        'questions': questions['questions']
    })

def calculate_answer_similarity(user_answer, correct_answer):
    """Calculate similarity between user's answer and correct answer with speech recognition in mind"""
    if not user_answer:
        return 0
    
    # Clean up speech recognition common issues
    def clean_text(text):
        return text.lower().replace('  ', ' ').strip()
    
    user_answer = clean_text(user_answer)
    correct_answer = clean_text(correct_answer)
    
    # Split into words and create word sets
    user_words = set(user_answer.split())
    correct_words = set(correct_answer.split())
    
    # Define key technical terms and their variations/common speech recognition errors
    technical_variations = {
        'component': {'component', 'components', 'kash component', 'cash component'},
        'static': {'static', 'statik', 'statics'},
        'lifecycle': {'lifecycle', 'life cycle', 'lifestyle', 'life style'},
        'state': {'state', 'states', 'status'},
        'props': {'props', 'properties', 'prop'},
        'render': {'render', 'renders', 'rendering'}
    }
    
    # Count matching concepts including variations
    matched_concepts = 0
    total_concepts = len(technical_variations)
    
    for variations in technical_variations.values():
        if any(var in user_words for var in variations):
            matched_concepts += 1
    
    # Calculate concept coverage (with higher weight for technical terms)
    concept_ratio = matched_concepts / total_concepts
    
    # Use SequenceMatcher for overall context similarity
    sequence_similarity = SequenceMatcher(None, user_answer, correct_answer).ratio()
    
    # Modified scoring calculation
    final_score = (concept_ratio * 0.7 + sequence_similarity * 0.3) * 1.25  # Max 1.25 points
    return round(final_score, 2)

def analyze_facial_expression(image_data):
    """Analyze facial expression and confidence using Gemini Vision"""
    try:
        # Convert base64 image to format Gemini can process
        prompt = """
        Analyze this interview candidate's facial expression and confidence level.
        Focus on:
        1. Facial expression (smile, eye contact, alertness)
        2. Posture and body language
        3. Overall confidence level
        4. Professional appearance
        
        Rate each aspect from 0-0.5 and provide a brief explanation.
        Return the response in JSON format with 'scores' and 'feedback' keys.
        """
        
        response = model.generate_content([prompt, image_data])
        analysis = json.loads(response.text)
        
        # Calculate total face score (max 2 points)
        face_score = sum(analysis['scores'].values())
        
        return {
            'score': round(face_score, 1),
            'feedback': analysis['feedback'],
            'expression_details': analysis['scores']
        }
    except Exception as e:
        print(f"Error analyzing facial expression: {str(e)}")
        return {
            'score': 0,
            'feedback': "Unable to analyze facial expression",
            'expression_details': {}
        }

@login_required
def interview_results(request, mock_id):
    interview = get_object_or_404(MockInterview, mock_id=mock_id)
    questions = interview.json_mock_resp if isinstance(interview.json_mock_resp, dict) else json.loads(interview.json_mock_resp)
    
    total_score = 0
    question_scores = []
    
    # Always give camera bonus (3.75 total, 0.75 per question)
    camera_bonus = 0.75  # Per question
    camera_total = 3.75  # Total camera bonus (5 questions * 0.75)
    
    for question in questions['questions']:
        user_answer = question.get('UserAnswer', '')
        correct_answer = question.get('Answer', '')
        
        # Calculate answer score (max 1.25)
        answer_score = calculate_answer_similarity(user_answer, correct_answer)
        
        # Add camera bonus to each question
        question_score = answer_score + camera_bonus
        
        total_score += question_score
        
        question_scores.append({
            'question': question['Question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'score': round(question_score, 2),
            'answer_score': round(answer_score, 2),
            'camera_bonus': camera_bonus,
            'feedback': generate_feedback(answer_score, user_answer, correct_answer),
        })

    # Total score out of 10 (5 questions × 2 marks each)
    final_score = round(total_score, 2)
    is_selected = final_score >= 6

    return render(request, 'dashboard/interview_results.html', {
        'interview': interview,
        'score': final_score,
        'is_selected': is_selected,
        'question_scores': question_scores,
        'camera_was_used': True,  # Always true since we're giving default camera bonus
        'camera_bonus_total': camera_total
    })

def generate_feedback(answer_score, user_answer, correct_answer):
    """Generate feedback based on new scoring system"""
    max_answer_score = 1.25
    percentage = (answer_score / max_answer_score) * 100
    
    if percentage >= 90:
        return "Excellent answer! Covered all key points with precise technical details."
    elif percentage >= 70:
        return "Good response. Covered most key concepts with some minor omissions."
    elif percentage >= 50:
        return "Fair attempt. Mentioned some relevant points but missing key technical details."
    elif percentage > 0:
        missing = get_missing_concepts(user_answer, correct_answer)
        return f"No valid answer provided. Focus on: {missing}"
    else:
        missing = get_missing_concepts(user_answer, correct_answer)
        return f"No valid answer provided. Focus on: {missing}"

def get_missing_concepts(user_answer, correct_answer):
    """Identify missing key concepts from speech-to-text answer"""
    user_words = set(user_answer.lower().split())
    
    # Define key concepts to look for
    key_concepts = {
        'component': 'component structure and organization',
        'static': 'static properties and behavior',
        'lifecycle': 'component lifecycle management',
        'state': 'state handling',
        'props': 'component properties',
        'render': 'rendering process'
    }
    
    # Find missing important concepts
    missing = []
    for concept, description in key_concepts.items():
        if not any(concept in word for word in user_words):
            missing.append(description)
    
    return ', '.join(missing[:2])

@login_required
def save_answer(request, mock_id):
    """Save the transcribed answer for a specific question"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_index = data.get('questionIndex')
            transcribed_answer = data.get('answer')
            
            if question_index is None:
                return JsonResponse({'status': 'error', 'message': 'Question index is required'}, status=400)
            if transcribed_answer is None:
                return JsonResponse({'status': 'error', 'message': 'Answer is required'}, status=400)
            
            # Get the interview
            interview = get_object_or_404(MockInterview, mock_id=mock_id)
            questions = interview.json_mock_resp if isinstance(interview.json_mock_resp, dict) else json.loads(interview.json_mock_resp)
            
            # Validate question index
            if not (0 <= question_index < len(questions['questions'])):
                return JsonResponse({'status': 'error', 'message': 'Invalid question index'}, status=400)
            
            # Update the answer for the specific question
            questions['questions'][question_index]['UserAnswer'] = transcribed_answer
            
            # Save back to database
            interview.json_mock_resp = questions
            interview.save()
            
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def how_it_works(request):
    return render(request, 'dashboard/howit.html')

@login_required
def save_recording(request, mock_id):
    if request.method == 'POST' and request.FILES.get('audio'):
        try:
            interview = get_object_or_404(MockInterview, mock_id=mock_id)
            audio_file = request.FILES['audio']
            
            # Save the audio file to your preferred storage
            # Example using default storage:
            fs = FileSystemStorage()
            filename = fs.save(f'recordings/{mock_id}_{uuid.uuid4()}.webm', audio_file)
            
            return JsonResponse({'status': 'success', 'path': filename})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400) 