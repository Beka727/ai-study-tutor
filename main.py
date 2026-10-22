from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from firebase_setup import db
from services.pdf_service import extract_text_from_pdf, chunk_text
from services.rag_service import get_embedding, generate_short_notes, answer_question, generate_quiz, evaluate_answer
from firebase_admin import firestore
import uuid
import numpy as np
import os

app = FastAPI(title="AI Interactive Tutor API")[span_2](start_span)[span_2](end_span)

# Request Models
class QuestionRequest(BaseModel):
    module_id: str
    question: str

class QuizGenRequest(BaseModel):
    module_id: str

class QuizSubmitRequest(BaseModel):
    user_id: str
    quiz_id: str
    question: str
    correct_answer: str
    user_answer: str

@app.get("/", response_class=HTMLResponse)
def read_frontend():
    """የፊት ለፊት (Frontend) ገጽን ከ templates/index.html ጫኖ ያሳያል"""
    html_path = os.path.join("templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3 style='text-align:center; margin-top:50px;'>Frontend template not found. Please check templates/index.html</h3>"

@app.post("/upload-module/")
async def upload_module(user_id: str, file: UploadFile = File(...)):[span_3](start_span)[span_3](end_span)
    if not file.filename.endswith(".pdf"):[span_4](start_span)[span_4](end_span)
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")[span_5](start_span)[span_5](end_span)

    try:
        # 1. Read PDF bytes[span_6](start_span)[span_6](end_span)
        pdf_bytes = await file.read()[span_7](start_span)[span_7](end_span)
        
        # 2. Extract Text[span_8](start_span)[span_8](end_span)
        raw_text = extract_text_from_pdf(pdf_bytes)[span_9](start_span)[span_9](end_span)
        if not raw_text.strip():[span_10](start_span)[span_10](end_span)
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")[span_11](start_span)[span_11](end_span)

        module_id = str(uuid.uuid4())[span_12](start_span)[span_12](end_span)

        # 3. Generate Short Notes via LLM
        short_notes = generate_short_notes(raw_text)

        # 4. Create Module Record in Firestore[span_13](start_span)[span_13](end_span)
        module_ref = db.collection("modules").document(module_id)[span_14](start_span)[span_14](end_span)
        module_ref.set({
            "module_id": module_id,
            "user_id": user_id,
            "title": file.filename,
            "short_notes": short_notes,
            "created_at": firestore.SERVER_TIMESTAMP[span_15](start_span)[span_15](end_span)
        })

        # 5. Chunk Text & Generate Embeddings
        chunks = chunk_text(raw_text)[span_16](start_span)[span_16](end_span)

        batch = db.batch()[span_17](start_span)[span_17](end_span)
        for idx, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            chunk_ref = db.collection("module_chunks").document()[span_18](start_span)[span_18](end_span)
            batch.set(chunk_ref, {
                "chunk_id": chunk_ref.id,[span_19](start_span)[span_19](end_span)
                "module_id": module_id,[span_20](start_span)[span_20](end_span)
                "chunk_index": idx,[span_21](start_span)[span_21](end_span)
                "content": chunk,[span_22](start_span)[span_22](end_span)
                "embedding": embedding
            })
        
        batch.commit()[span_23](start_span)[span_23](end_span)

        return {
            "status": "success",
            "module_id": module_id,
            "total_chunks": len(chunks),
            "short_notes": short_notes,
            "message": "Module uploaded, embedded, and summarized successfully!"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))[span_24](start_span)[span_24](end_span)

@app.post("/ask-question/")
async def ask_question(req: QuestionRequest):
    """ተማሪው ጥያቄ ሲጠይቅ በ RAG Vector Similarity አማካኝነት መልስ የሚሰጥ"""
    try:
        q_embedding = np.array(get_embedding(req.question))
        chunks_ref = db.collection("module_chunks").where("module_id", "==", req.module_id).stream()
        
        best_chunk = ""
        highest_similarity = -1

        for doc in chunks_ref:
            data = doc.to_dict()
            chunk_embedding = np.array(data["embedding"])
            
            # Cosine similarity calculation
            similarity = np.dot(q_embedding, chunk_embedding) / (np.linalg.norm(q_embedding) * np.linalg.norm(chunk_embedding))
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_chunk = data["content"]

        if not best_chunk:
            return {"answer": "No relevant content found in this module."}

        final_answer = answer_question(best_chunk, req.question)
        return {"status": "success", "answer": final_answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz/")
async def create_quiz(req: QuizGenRequest):
    """ከሞጁሉ ጽሑፍ ላይ የፈተና ጥያቄዎችን የሚያመነጭ"""
    try:
        chunks_ref = db.collection("module_chunks").where("module_id", "==", req.module_id).stream()
        full_text = " ".join([doc.to_dict()["content"] for doc in chunks_ref])
        
        if not full_text:
            raise HTTPException(status_code=404, detail="Module chunks not found.")

        quizzes = generate_quiz(full_text, num_questions=3)
        
        quiz_ids = []
        batch = db.batch()
        for q in quizzes:
            q_ref = db.collection("quizzes").document()
            batch.set(q_ref, {
                "quiz_id": q_ref.id,
                "module_id": req.module_id,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"]
            })
            quiz_ids.append(q_ref.id)
        batch.commit()

        return {"status": "success", "quizzes": quizzes, "quiz_ids": quiz_ids}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-quiz/")
async def submit_quiz(req: QuizSubmitRequest):
    """ተማሪው የመለሰውን መልስ ገምግሞ ግብረ-መልስ (Feedback) የሚሰጥ"""
    try:
        eval_result = evaluate_answer(req.question, req.correct_answer, req.user_answer)
        
        attempt_ref = db.collection("user_attempts").document()
        attempt_ref.set({
            "attempt_id": attempt_ref.id,
            "user_id": req.user_id,
            "quiz_id": req.quiz_id,
            "user_answer": req.user_answer,
            "is_correct": eval_result["is_correct"],
            "feedback": eval_result["feedback"],
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        return {
            "status": "success",
            "is_correct": eval_result["is_correct"],
            "feedback": eval_result["feedback"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
