import uuid, os, asyncio, json
from typing import AsyncGenerator

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from helpers import get_settings
from controllers import TextStorageService
from models.QuestionAnswering.QAGraphs import QA_Graph
from models.QuestionAnswering.QAStates import QuestionAnsweringState
from stores.llm import EmbeddingProviderFactory

from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter


app_settings = get_settings()



QARoute = APIRouter(
    prefix="/api/TA",
    tags=["question_answering_routes"]
)


# -----------------------------
# Utility: Run blocking function in thread pool
# -----------------------------
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# -----------------------------
# Start Question Answering Session
# -----------------------------
@QARoute.post("/start_QA_session")
async def start_question_answering_session(
    clean_text_file_path: str = Body(..., embed=True),
    user_question: str = Body(..., embed=True)):
    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    thread_id = str(uuid.uuid4())
    initial_state = QuestionAnsweringState({"context": context, "message": [HumanMessage(user_question)]})
    config = {"configurable": {"thread_id": "a"}}


    embedding_function = EmbeddingProviderFactory(app_settings).create(
        provider=app_settings.EMBEDDING_BACKEND,
        model_name=app_settings.EMBEDDING_MODEL_ID
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    chunks = splitter.split_text(initial_state["context"])

    if not os.path.exists(os.path.join("assets/vector_dB",app_settings.VECTOR_DB_PATH)):
        os.makedirs(os.path.join("assets/vector_dB",app_settings.VECTOR_DB_PATH), exist_ok=True )
    db = Chroma.from_texts(
        chunks, embedding_function,
        persist_directory=os.path.join("assets/vector_dB",app_settings.VECTOR_DB_PATH)
        )
    
    async def event_stream() -> AsyncGenerator[str, None]:
        global_events = ["question_grading", "retriever", "question_answer"]
        current_global_event = None

        # Initial payload
        yield f'data: {json.dumps({"thread_id": thread_id, "status": "starting_session"})}\n\n'

        try:
            async for event in QA_Graph.astream_events(initial_state, config=config, version="v2"):
                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Simplified event_data handling
                if isinstance(event_data, dict):
                    processed_data = {}
                    for k, v in event_data.items():
                        if k == "input" and isinstance(v, Command):
                            processed_data[k] = {"resume_value": getattr(v, "resume", str(v))}
                        elif k == "chunk" and hasattr(v, "content"):
                            processed_data[k] = v
                        elif hasattr(v, "__dict__"):
                            processed_data[k] = str(v)
                        else:
                            try:
                                json.dumps(v)
                                processed_data[k] = v
                            except (TypeError, OverflowError):
                                processed_data[k] = str(v)
                    event_data = processed_data
                else:
                    event_data = {"value": str(event_data)}

                payload_to_yield = {"event": event_type, "name": event_name, "thread_id": thread_id}

                # Chain start
                if event_type == "on_chain_start":
                    payload_to_yield.update({
                        "status_update": f"Starting: {event_name}",
                        "data": event_data.get("input")
                    })
                    if event_name in global_events:
                        current_global_event = event_name
                    yield f'data: {json.dumps(payload_to_yield)}\n\n'

                # Streaming LLM tokens
                elif event_type == "on_chat_model_stream" and current_global_event in global_events:
                    chunk = event_data.get("chunk")
                    if chunk and chunk.content:
                        yield f'data: {json.dumps({"event": "token", "token": chunk.content, "status_update": current_global_event, "thread_id": thread_id})}\n\n'

                # Handle off-topic response token streaming
                if event_name == "off_topic_response":
                    fixed_response = "Sorry, I cannot answer this question because it is off-topic."
                    for token in fixed_response.split():
                        yield f'data: {json.dumps({"event": "token", "token": token + " ", "status_update": "off_topic_response", "thread_id": thread_id})}\n\n'

        except Exception as e:
            import traceback
            yield f'data: {json.dumps({"event": "error", "thread_id": thread_id, "detail": traceback.format_exc(), "error_type": e.__class__.__name__})}\n\n'
        finally:
            yield f'data: {json.dumps({"event": "stream_end", "thread_id": thread_id, "status_update": "Stream ended"})}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -----------------------------
# Continue Question Answering Session
# -----------------------------
@QARoute.post("/QA_continue")
async def continue_after_feedback(user_question: str = Body(..., embed=True), thread_id: str = Body(..., embed=True)):
    config = {"configurable": {"thread_id": "a"}}

    # Retrieve last state
    state_snapshot = QA_Graph.get_state(config)
    if state_snapshot is None:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    current_state = state_snapshot.values
    if current_state is None:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    current_state["message"].append(HumanMessage(content=user_question))

    async def event_stream() -> AsyncGenerator[str, None]:
        global_events = ["question_grading", "retriever", "question_answer"]
        current_global_event = None

        yield f'data: {json.dumps({"thread_id": thread_id, "status": "starting_session"})}\n\n'

        try:
            async for event in QA_Graph.astream_events(current_state, config=config, version="v2"):
                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Process event_data
                if isinstance(event_data, dict):
                    processed_data = {}
                    for k, v in event_data.items():
                        if k == "input" and isinstance(v, Command):
                            processed_data[k] = {"resume_value": getattr(v, "resume", str(v))}
                        elif k == "chunk" and hasattr(v, "content"):
                            processed_data[k] = v
                        elif hasattr(v, "__dict__"):
                            processed_data[k] = str(v)
                        else:
                            try:
                                json.dumps(v)
                                processed_data[k] = v
                            except (TypeError, OverflowError):
                                processed_data[k] = str(v)
                    event_data = processed_data
                else:
                    event_data = {"value": str(event_data)}

                payload_to_yield = {"event": event_type, "name": event_name, "thread_id": thread_id}

                # Chain start
                if event_type == "on_chain_start":
                    payload_to_yield.update({
                        "status_update": f"Starting: {event_name}",
                        "data": event_data.get("input")
                    })
                    if event_name in global_events:
                        current_global_event = event_name
                    yield f'data: {json.dumps(payload_to_yield)}\n\n'

                # Streaming LLM tokens
                elif event_type == "on_chat_model_stream" and current_global_event in global_events:
                    chunk = event_data.get("chunk")
                    if chunk and chunk.content:
                        yield f'data: {json.dumps({"event": "token", "token": chunk.content, "status_update": current_global_event, "thread_id": thread_id})}\n\n'

                # Off-topic response
                if event_name == "off_topic_response":
                    fixed_response = "Sorry, I cannot answer this question because it is off-topic."
                    for token in fixed_response.split():
                        yield f'data: {json.dumps({"event": "token", "token": token + " ", "status_update": "off_topic_response", "thread_id": thread_id})}\n\n'

        except Exception as e:
            import traceback
            yield f'data: {json.dumps({"event": "error", "thread_id": thread_id, "detail": traceback.format_exc(), "error_type": e.__class__.__name__})}\n\n'
        finally:
            yield f'data: {json.dumps({"event": "stream_end", "thread_id": thread_id, "status_update": "Stream ended"})}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
