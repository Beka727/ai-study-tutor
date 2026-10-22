import json

def generate_quiz(module_text: str, num_questions: int = 3) -> list:
    """ከሞጁሉ ጽሑፍ ላይ በመነሳት የልምምድ ጥያቄዎችን (MCQs) ያመነጫል"""
    model = genai.GenerativeModel(GENERATIVE_MODEL)
    prompt = f"""You are an expert academic tutor. Based on the following study module, generate {num_questions} multiple-choice questions (MCQs) to test the student's understanding. 
    
    You must output the result STRICTLY as a JSON array of objects with the following format, with no extra markdown formatting or text outside the JSON:
    [
      {{
        "question": "Question text here?",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": "B) ...",
        "explanation": "Explanation of why this is correct."
      }}
    ]

    Module Text:
    {module_text[:10000]}
    """
    response = model.generate_content(prompt)
    
    # Clean response text to ensure valid JSON parsing
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)

def evaluate_answer(question: str, correct_answer: str, user_answer: str) -> dict:
    """ተማሪው የመለሰውን መልስ መገምገም እና ማብራሪያ መስጠት"""
    model = genai.GenerativeModel(GENERATIVE_MODEL)
    prompt = f"""You are an expert AI tutor. Evaluate the student's answer for the following question.
    
    Question: {question}
    Correct Answer: {correct_answer}
    Student's Answer: {user_answer}

    Provide feedback in JSON format strictly:
    {{
      "is_correct": true or false,
      "feedback": "Detailed explanation and feedback for the student."
    }}
    """
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)
