from google.generativeai import GenerativeModel, configure
from django.conf import settings
import json

# Configure API key
configure(api_key=settings.GEMINI_API_KEY)

# Initialize model
model = GenerativeModel('gemini-2.0-flash')

def create_interview_prompt(job_position, job_desc, job_experience):
    return f"""
    Create a mock interview for the following position:
    Job Position: {job_position}
    Job Description: {job_desc}
    Years of Experience: {job_experience}
    
    Please provide exactly 5 technical interview questions with answers in the following JSON format, with no additional text:
    {{
      "questions": [
        {{
          "Question": "question text here",
          "Answer": "detailed answer here"
        }}
      ]
    }}
    """

def process_ai_response(response):
    # Clean up the response
    clean_response = response.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_response)

def generate_interview(job_position, job_desc, job_experience):
    try:
        # Create prompt
        prompt = create_interview_prompt(job_position, job_desc, job_experience)
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Process and validate response
        parsed_response = process_ai_response(response.text)
        
        if not parsed_response.get('questions') or not isinstance(parsed_response['questions'], list):
            raise ValueError("Invalid response format")
            
        return parsed_response
        
    except Exception as e:
        raise Exception(f"Failed to generate interview: {str(e)}") 