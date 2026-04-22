from fastapi import APIRouter, Depends, Body, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import uuid, json, asyncio
from typing import AsyncGenerator

from langgraph.types import Command
from helpers import get_settings, Settings
from controllers import TextStorageService
from models.SummarizationGeneration.SGGraphs import SG_Graph

SGRoute = APIRouter(
    prefix="/api/TA",
    tags=["summarization_generation_routes"]
)

# -----------------------------
# Utility: Run blocking function in thread pool
# -----------------------------
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# -----------------------------
# Start Summarization Generation Session
# -----------------------------
@SGRoute.post("/start_SG_session")
async def start_summarization_generation_session(
    clean_text_file_path: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True)
):
    # Load context
    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    # Unique thread/session ID
    thread_id = str(uuid.uuid4())

    # Initial graph state
    initial_state = {"context": context}
    config = {"configurable": {"thread_id": thread_id}}

    async def event_stream() -> AsyncGenerator[str, None]:
        global_events = ["main_point_summarizer", "summary_writer", "summary_rewriter"]

        current_global_event = None
        initial_payload = {"thread_id": str(thread_id), "status": "starting_session"} 
        yield f'data: {json.dumps(initial_payload)}\n\n'    
        try:   
            async for event in SG_Graph.astream_events(initial_state, config=config, version="v2"):
                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = {}
                if "data" in event:
                    raw_data = event.get("data", {})
                    if isinstance(raw_data, dict):
                        for k, v in raw_data.items():
                            if k == "input" and isinstance(v, Command):
                                event_data[k] = {"resume_value": v.resume if hasattr(v, "resume") else str(v)}
                            elif k == "chunk" and hasattr(v, 'content'):
                                event_data[k] = v
                            elif hasattr(v, "__dict__"):
                                event_data[k] = str(v)
                            else:
                                try:
                                    json.dumps(v)
                                    event_data[k] = v
                                except (TypeError, OverflowError):
                                    event_data[k] = str(v)
                    else:
                        event_data = {"value": str(raw_data)}
                payload_to_yield = {"event": event_type, "name": event_name, "thread_id": thread_id}
                if event_type == "on_chain_start":
                    payload_to_yield["status_update"] = f"Starting: {event_name}"
                    payload_to_yield["data"] = event_data.get("input")
                    if event_name in global_events:
                        current_global_event = event_name
                    yield f'data: {json.dumps(payload_to_yield)}\n\n'
                elif event_type == "on_chat_model_stream" and current_global_event in global_events:
                    chunk = event_data.get("chunk")
                    if chunk and chunk.content:
                        payload_to_yield["event"] = "token" 
                        payload_to_yield["token"] = chunk.content
                        payload_to_yield["status_update"] = current_global_event
                        yield f'data: {json.dumps(payload_to_yield)}\n\n'
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_message = f"Error in summarization stream: {str(e)}"
            yield f'data: {json.dumps({"event": "error", "thread_id": thread_id, "detail": error_message, "error_type": e.__class__.__name__})}\n\n'
        finally:
            payload = {"event": "stream_end", "thread_id": str(thread_id), "status_update": "Stream ended"}
            yield f'data: {json.dumps(payload)}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")




# -----------------------------
# Continue Question Generation Session
# -----------------------------
@SGRoute.post("/SG_continue")
async def continue_after_feedback(
    background_tasks: BackgroundTasks,
    project_id: str = Body(..., embed=True),
    clean_text_file_path: str = Body(..., embed=True),
    user_feedback: str = Body(..., embed=True),
    thread_id:str = Body(..., embed=True)
):
    # Unique thread/session ID
    config = {"configurable": {"thread_id": thread_id}}

    # Prepare resume command
    resume_command = Command(resume=user_feedback)

    async def event_stream() -> AsyncGenerator[str, None]:
        global_events = ["main_point_summarizer", "summary_writer", "summary_rewriter"]
        current_global_event = None
        initial_payload = {"thread_id": str(thread_id), "status": "continue_session"} 
        yield f'data: {json.dumps(initial_payload)}\n\n'    
        try:   
            async for event in SG_Graph.astream_events(resume_command, config=config, version="v2"):
                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = {}
                if "data" in event:
                    raw_data = event.get("data", {})
                    if isinstance(raw_data, dict):
                        for k, v in raw_data.items():
                            if k == "input" and isinstance(v, Command):
                                event_data[k] = {"resume_value": v.resume if hasattr(v, "resume") else str(v)}
                            elif k == "chunk" and hasattr(v, 'content'):
                                event_data[k] = v
                            elif hasattr(v, "__dict__"):
                                event_data[k] = str(v)
                            else:
                                try:
                                    json.dumps(v)
                                    event_data[k] = v
                                except (TypeError, OverflowError):
                                    event_data[k] = str(v)
                    else:
                        event_data = {"value": str(raw_data)}
                payload_to_yield = {"event": event_type, "name": event_name, "thread_id": thread_id}
                if event_type == "on_chain_start":
                    payload_to_yield["status_update"] = f"Starting: {event_name}"
                    payload_to_yield["data"] = event_data.get("input")
                    if event_name in global_events:
                        current_global_event = event_name
                    yield f'data: {json.dumps(payload_to_yield)}\n\n'
                elif event_type == "on_chat_model_stream" and current_global_event in global_events:
                    chunk = event_data.get("chunk")
                    if chunk and chunk.content:
                        payload_to_yield["event"] = "token" 
                        payload_to_yield["token"] = chunk.content
                        payload_to_yield["status_update"] = current_global_event
                        yield f'data: {json.dumps(payload_to_yield)}\n\n'
                
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_message = f"Error in summarization stream: {str(e)}"
            yield f'data: {json.dumps({"event": "error", "thread_id": thread_id, "detail": error_message, "error_type": e.__class__.__name__})}\n\n'
        finally:
            payload = {"event": "stream_end", "thread_id": str(thread_id), "status_update": "Stream ended"}
            yield f'data: {json.dumps(payload)}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")

