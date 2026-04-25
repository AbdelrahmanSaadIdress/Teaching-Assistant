from fastapi import APIRouter, Body, BackgroundTasks, HTTPException
import uuid
import asyncio

from langgraph.types import Command
from helpers import get_settings, Settings
from controllers import TextStorageService
from models.ExamsGeneration.BulkGraph import BulkQG_Graph

BulkQGRoute = APIRouter(
    prefix="/api/TA",
    tags=["bulk_question_generation_routes"]
)


def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# ─────────────────────────────────────────
# Start Bulk Question Generation
# ─────────────────────────────────────────

@BulkQGRoute.post("/start_bulk_session")
async def start_bulk_question_generation(
    question_type: str = Body(..., embed=True),   # "MCQ", "T/F", or "Both"
    num_questions: int = Body(..., embed=True),
    clean_text_file_path: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True),
):
    if question_type not in ["MCQ", "T/F", "Both"]:
        raise HTTPException(status_code=400, detail="question_type must be 'MCQ', 'T/F', or 'Both'")

    if not (1 <= num_questions <= 50):
        raise HTTPException(status_code=400, detail="num_questions must be between 1 and 50")

    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    thread_id = str(uuid.uuid4())
    initial_state = {
        "context": context,
        "question_type": question_type,
        "num_questions": num_questions,
        "questions": [],
        "history": [],
    }
    config = {"configurable": {"thread_id": thread_id}}

    try:
        graph_response = await run_in_thread(BulkQG_Graph.invoke, initial_state, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

    return {
        "message": "Bulk question generation session started.",
        "thread_id": thread_id,
        "questions": graph_response.get("questions", []),
        "num_questions": num_questions,
        "question_type": question_type,
    }


# ─────────────────────────────────────────
# Continue with Feedback
# ─────────────────────────────────────────

@BulkQGRoute.post("/bulk_continue")
async def continue_bulk_after_feedback(
    background_tasks: BackgroundTasks,
    thread_id: str = Body(..., embed=True),
    user_feedback: str = Body(..., embed=True),
):
    config = {"configurable": {"thread_id": thread_id}}
    resume_command = Command(resume=user_feedback)

    try:
        graph_response = await run_in_thread(BulkQG_Graph.invoke, resume_command, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

    return {
        "message": "Bulk question generation continued.",
        "thread_id": thread_id,
        "questions": graph_response.get("questions", []),
    }