from openai import OpenAI
import json

client = OpenAI()


def analyze_resume(resume_text, user_goal):
    # 1. Properly formatted prompt string
    prompt = f"""
    You are a career counselor. Analyze the following resume and provide feedback based on the user's goal: {user_goal}. 
    
    Resume: {resume_text}
    
    Strict Rules:
    1. Provide specific feedback on how to improve the resume based on the user's goal.
    2. Highlight any missing skills or experiences that are relevant to the user's goal.
    3. Suggest any additional sections or information that could enhance the resume.
    4. Provide actionable advice on how to tailor the resume for the user's desired job or industry.
    
    Return only JSON in this format:
    {{
        "feedback": "Your feedback here",
        "missing_skills": ["List of missing skills"],
        "additional_sections": ["List of additional sections"],
        "tailoring_advice": "Your tailoring advice here"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            # Note: response_format ensures the model actually returns valid JSON
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful career counselor that outputs JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # 2. Extract and parse the content
        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        # 3. Clean error handling with a consistent structure
        return {
            "feedback": f"Error analyzing resume: {str(e)}",
            "missing_skills": [],
            "additional_sections": [],
            "tailoring_advice": "",
            "error": str(e),
        }
