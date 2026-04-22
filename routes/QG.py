from fastapi import APIRouter, Depends, Body, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import uuid
import asyncio

from langgraph.types import Command
from helpers import get_settings, Settings
from controllers import TextStorageService
from models.QuestionGeneration.QGGraphs import QG_Graph

QGRoute = APIRouter(
    prefix="/api/TA",
    tags=["question_generation_routes"]
)


# -----------------------------
# Utility: Run blocking function in thread pool
# -----------------------------
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# -----------------------------
# Start Question Generation Session
# -----------------------------
@QGRoute.post("/start_session")
async def start_question_generation_session(
    question_type: str = Body(..., embed=True),
    clean_text_file_path: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True)
):
    # Validate question type
    if question_type not in ["MCQ", "T/F"]:
        raise HTTPException(status_code=400, detail="question_type must be 'MCQ' or 'T/F'")

    # Load context
    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    # Unique thread/session ID
    thread_id = str(uuid.uuid4())

    # Initial graph state
    initial_state = {"context": context, "question_type": question_type}
    config = {"configurable": {"thread_id": thread_id}}

    # Run graph in thread pool
    try:
        graph_response = await run_in_thread(QG_Graph.invoke, initial_state, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

    return {
        "message": "Question generation session started successfully.",
        "thread_id": thread_id,
        "graph_response": graph_response
    }


# -----------------------------
# Continue Question Generation Session
# -----------------------------
@QGRoute.post("/continue")
async def continue_after_feedback(
    background_tasks: BackgroundTasks,
    project_id: str = Body(..., embed=True),
    question_type: str = Body(..., embed=True),
    clean_text_file_path: str = Body(..., embed=True),
    user_feedback: str = Body(..., embed=True),
    thread_id:str = Body(..., embed=True)
):
    # Validate question type
    if question_type not in ["MCQ", "T/F"]:
        raise HTTPException(status_code=400, detail="question_type must be 'MCQ' or 'T/F'")

    # Load context
    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    # Unique thread/session ID
    
    config = {"configurable": {"thread_id": thread_id}}

    # Prepare resume command
    resume_command = Command(resume=user_feedback)

    # Execute graph in thread pool
    try:
        graph_response = await run_in_thread(QG_Graph.invoke, resume_command, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

    # Post-process options for MCQ / T-F
    if isinstance(graph_response, dict) and "options" in graph_response:
        if question_type == "MCQ" and isinstance(graph_response["options"], str):
            graph_response["options"] = [
                opt.strip() for opt in graph_response["options"].split("\n") if opt.strip()
            ]
        elif question_type == "T/F":
            graph_response["options"] = None

    return {
        "message": "Question generation session continued successfully.",
        "thread_id": thread_id,
        "graph_response": graph_response
    }
