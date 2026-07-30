from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
import json
import time
from fastapi.staticfiles import StaticFiles
import csv

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key="ignite_secret_key"
)

BASE_DIR = Path(__file__).parent

# Load Questions



def load_questions(filename):

    questions = []

    csv_path = BASE_DIR / "data" / "quizzes" / filename

    with open(csv_path, newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            questions.append({

                "question": row["Question"],

                "options": [

                    row["Option A"],
                    row["Option B"],
                    row["Option C"],
                    row["Option D"]

                ],

                "answer": row["Correct Answer"]

            })

    return questions

questions = load_questions("General Knowledge.csv")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Temporary storage
participants = {}

# Quiz State

quiz_state = {
    "started": False,
    "ended": False,
    "current_question": 0,
    "question_locked": False,
    "show_results": False,
    "question_start_time": None
}

# Student Answers
answers = {}

#Homepage

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

#join page

@app.get("/join")
async def join(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="join.html"
    )
#Recive student name 

@app.post("/join")
async def join_student(request: Request, student_name: str = Form(...)):

    # Save student name in session
    request.session["student_name"] = student_name
    participants[student_name] = {
    "answered": False,
    "response_time": None,
    "score": 0
}


    print(f"Student Joined: {student_name}")

    return RedirectResponse(
        url="/waiting",
        status_code=303
    )

# waitting lobby

@app.get("/waiting", response_class=HTMLResponse)
async def waiting(request: Request):

    student_name = request.session.get("student_name")

    if participants[student_name]["answered"]:
        return templates.TemplateResponse(
        request=request,
        name="submitted.html",
        context={
            "request": request,
            "student_name": student_name,
            "message": "❌ You have already submitted your answer."
        }
    )

    if not student_name:
        return templates.TemplateResponse(
            request=request,
            name="join.html"
        )

    return templates.TemplateResponse(
        request=request,
        name="waiting.html",
        context={
            "request": request,
            "student_name": student_name
        }
    ) 

# Host Dashboard

@app.get("/host")
async def host(request: Request):

    global current_leaderboard

    # Count participants who have answered
    answered_count = sum(
        1
        for participant in participants.values()
        if participant.get("answered", False)
    )

    # Show live leaderboard only after question is locked
    leaderboard = current_leaderboard if quiz_state["show_results"] else []

    # Safe question start time for the timer
    question_start_time = quiz_state.get("question_start_time") or 0

    return templates.TemplateResponse(
        request=request,
        name="host.html",
        context={
            "request": request,

            "participants": participants,
            "questions": questions,

            "quiz_state": quiz_state,

            "leaderboard": leaderboard,

            "answered_count": answered_count,

            "question_start_time": question_start_time,
        },
    )

# Start quiz

@app.post("/start")
async def start_quiz():

    # Start new quiz
    quiz_state["started"] = True
    quiz_state["ended"] = False

    # First question
    quiz_state["current_question"] = 0

    # Reset round
    quiz_state["question_locked"] = False
    quiz_state["show_results"] = False

    # Start timer
    quiz_state["question_start_time"] = time.time()

    print("Question started at:", quiz_state["question_start_time"])

    return RedirectResponse(
        url="/host",
        status_code=303
    )

# next quetion
@app.post("/next-question")
async def next_question():

    # Check if another question exists
    if quiz_state["current_question"] < len(questions) - 1:

        quiz_state["current_question"] += 1

        quiz_state["question_locked"] = False
        quiz_state["show_results"] = False
        quiz_state["question_start_time"] = time.time()
        quiz_state["ended"] = False

        # Reset participants
        for student in participants:
            participants[student]["answered"] = False

        answers.clear()

        return RedirectResponse(
            url="/host",
            status_code=303
        )

    # Last question finished
    return RedirectResponse(
        url="/end-quiz",
        status_code=303
    )
# lock quetion 
@app.post("/lock-question")
async def lock_question():

    global current_leaderboard

    print("ANSWERS DICTIONARY")
    print(answers)

    quiz_state["question_locked"] = True
    quiz_state["show_results"] = True

    current_leaderboard = get_leaderboard()

    print("LEADERBOARD")
    print(current_leaderboard)

    return RedirectResponse("/host", status_code=303)


# status API

@app.get("/quiz-status")
async def quiz_status():

    return {
        "started": quiz_state["started"],
        "ended": quiz_state["ended"],          # <-- Add this
        "current_question": quiz_state["current_question"],
        "question_locked": quiz_state["question_locked"],
        "show_results": quiz_state["show_results"]
    }
 
#temp quetion 

@app.get("/question", response_class=HTMLResponse)
async def question(request: Request):

    # Don't allow access before quiz starts
    if not quiz_state["started"]:
        return RedirectResponse(
            url="/waiting",
            status_code=303
        )

    current_question = questions[quiz_state["current_question"]]

    return templates.TemplateResponse(
        request=request,
        name="question.html",
        context={
            "request": request,

            "question_number": quiz_state["current_question"] + 1,

            "total_questions": len(questions),

            "time_left": 30,

            "category": "General Knowledge",

            "question_text": current_question["question"],

            "options": current_question["options"]
        }
    )
# submit answer
@app.post("/submit-answer", response_class=HTMLResponse)
async def submit_answer(
    request: Request,
    answer: str = Form(...)
):

    student_name = request.session.get("student_name")
    if quiz_state["question_locked"]:
       return templates.TemplateResponse(
        request=request,
        name="submitted.html",
        context={
            "request": request,
            "student_name": student_name,
            "message": "🔒 This question has been locked."
        }
    )

    # Debug prints
    print("Before submission:", participants[student_name])

    # Check if already answered
    if participants[student_name]["answered"]:
        return templates.TemplateResponse(
            request=request,
            name="submitted.html",
            context={
                "request": request,
                "student_name": student_name,
                "message": "❌ You have already submitted your answer."
            }
        )

  # Save the answer
    current_question = questions[quiz_state["current_question"]]
    response_time = time.time() - quiz_state["question_start_time"]
    is_correct = answer == current_question["answer"]

    answers[student_name] = {
    "answer": answer,
    "response_time": round(response_time, 3),
    "correct": is_correct
}

    participants[student_name]["answered"] = True
    participants[student_name]["response_time"] = round(response_time, 3)

    print("After submission:", participants[student_name])
    print(answers[student_name])

    return templates.TemplateResponse(
        request=request,
        name="submitted.html",
        context={
            "request": request,
            "student_name": student_name,
            "message": "✅ Your answer has been submitted successfully!"
        }
    )

# Leader board 
POINTS = [10, 8, 6, 4, 2]
def get_leaderboard():

    correct_answers = []

    for student_name, data in answers.items():

        if data["correct"]:

            correct_answers.append(
                {
                    "student_name": student_name,
                    "response_time": data["response_time"]
                }
            )
    correct_answers.sort(
         key=lambda student: student["response_time"]
)
    correct_answers = correct_answers[:10]
    for i, student in enumerate(correct_answers):

     if i < len(POINTS):

        participants[student["student_name"]]["score"] += POINTS[i]

    return correct_answers

def get_final_leaderboard():

    leaderboard = []

    for student_name, data in participants.items():

        leaderboard.append({
            "student_name": student_name,
            "score": data["score"]
        })

    leaderboard.sort(
        key=lambda student: student["score"],
        reverse=True
    )

    return leaderboard

# Results
@app.get("/results")
async def results(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "request": request,
            "leaderboard": current_leaderboard,
            "student_name": request.session.get("student_name")
        }
    )
# End quiz

@app.get("/end-quiz")
async def end_quiz(request: Request):

    leaderboard = get_final_leaderboard()

    # Mark quiz as finished
    quiz_state["started"] = False
    quiz_state["ended"] = True

    return templates.TemplateResponse(
        request=request,
        name="final_results.html",
        context={
            "request": request,
            "leaderboard": leaderboard
        }
    )

# Reset route 
@app.post("/reset-quiz")
async def reset_quiz():

    participants.clear()
    answers.clear()

    quiz_state["started"] = False
    quiz_state["ended"] = False
    quiz_state["current_question"] = 0
    quiz_state["question_locked"] = False
    quiz_state["show_results"] = False
    quiz_state["question_start_time"] = None

    return RedirectResponse(
        url="/host",
        status_code=303
    )

# clear quiz data 
@app.post("/clear-quiz")
async def clear_quiz():

    global current_leaderboard

    participants.clear()
    answers.clear()
    current_leaderboard = []

    quiz_state["started"] = False
    quiz_state["ended"] = False
    quiz_state["current_question"] = 0
    quiz_state["question_locked"] = False
    quiz_state["show_results"] = False
    quiz_state["question_start_time"] = None

    return RedirectResponse(
        url="/host",
        status_code=303
    )