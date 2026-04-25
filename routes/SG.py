from fastapi import APIRouter, Body, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import uuid, json, asyncio
from typing import AsyncGenerator, Literal

from langgraph.types import Command
from helpers import get_settings, Settings
from controllers import TextStorageService
from models.SummarizationGeneration.SGGraphs import SG_Graph

SGRoute = APIRouter(
    prefix="/api/TA",
    tags=["summarization_generation_routes"]
)


def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# ─────────────────────────────────────────
# SSE helpers
# ─────────────────────────────────────────

# Map graph node names → which state field they are streaming into
NODE_TO_SECTION = {
    "extract_key_terms":     "key_terms",
    "write_tldr":            "tldr",
    "write_structured_notes":"structured_notes",
    "write_paragraph_summary":"paragraph_summary",
    "summary_rewriter":      "rewriter",   # rewriter touches all sections
}

SECTION_LABELS = {
    "key_terms":        "🔑 Key Terms",
    "tldr":             "⚡ Quick Recap",
    "structured_notes": "📋 Structured Notes",
    "paragraph_summary":"📖 Paragraph Summary",
    "rewriter":         "✏️ Rewriting...",
}


def _process_event_data(raw_data):
    """Safely serialize event data to a JSON-able dict."""
    if not isinstance(raw_data, dict):
        return {"value": str(raw_data)}
    result = {}
    for k, v in raw_data.items():
        if k == "input" and isinstance(v, Command):
            result[k] = {"resume_value": getattr(v, "resume", str(v))}
        elif k == "chunk" and hasattr(v, "content"):
            result[k] = v          # handled separately below
        elif hasattr(v, "__dict__"):
            result[k] = str(v)
        else:
            try:
                json.dumps(v)
                result[k] = v
            except (TypeError, OverflowError):
                result[k] = str(v)
    return result


async def _stream_graph(graph_input, config, thread_id) -> AsyncGenerator[str, None]:
    """
    Core streaming logic shared by start and continue endpoints.
    Emits SSE events:
        - section_start  { section, label }
        - token          { section, token }
        - section_end    { section }
        - interrupt      { payload }   ← when graph hits human_feedback
        - stream_end
        - error
    """
    current_section = None

    try:
        async for event in SG_Graph.astream_events(graph_input, config=config, version="v2"):
            etype = event["event"]
            ename = event.get("name", "")
            edata = _process_event_data(event.get("data", {}))

            # Track which node is active → which section we're streaming
            if etype == "on_chain_start" and ename in NODE_TO_SECTION:
                current_section = NODE_TO_SECTION[ename]
                yield f'data: {json.dumps({"event": "section_start", "section": current_section, "label": SECTION_LABELS[current_section], "thread_id": thread_id})}\n\n'

            elif etype == "on_chain_end" and ename in NODE_TO_SECTION:
                yield f'data: {json.dumps({"event": "section_end", "section": current_section, "thread_id": thread_id})}\n\n'
                current_section = None

            # Stream tokens
            elif etype == "on_chat_model_stream" and current_section:
                chunk = edata.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield f'data: {json.dumps({"event": "token", "section": current_section, "token": chunk.content, "thread_id": thread_id})}\n\n'

            # Interrupt = graph hit human_feedback node
            elif etype == "on_chain_end" and ename == "human_feedback":
                # The interrupt payload is embedded in the state snapshot
                state_snap = SG_Graph.get_state(config)
                if state_snap:
                    vals = state_snap.values
                    interrupt_payload = {
                        "depth": vals.get("depth"),
                        "key_terms": vals.get("key_terms"),
                        "tldr": vals.get("tldr"),
                        "structured_notes": vals.get("structured_notes"),
                        "paragraph_summary": vals.get("paragraph_summary"),
                    }
                    yield f'data: {json.dumps({"event": "interrupt", "payload": interrupt_payload, "thread_id": thread_id})}\n\n'

    except Exception as e:
        import traceback
        yield f'data: {json.dumps({"event": "error", "detail": traceback.format_exc(), "error_type": e.__class__.__name__, "thread_id": thread_id})}\n\n'
    finally:
        yield f'data: {json.dumps({"event": "stream_end", "thread_id": thread_id})}\n\n'


# ─────────────────────────────────────────
# Start Summarization Session
# ─────────────────────────────────────────

@SGRoute.post("/start_SG_session")
async def start_summarization_generation_session(
    clean_text_file_path: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True),
    depth: str = Body("standard", embed=True),   # "brief" | "standard" | "detailed"
):
    if depth not in ("brief", "standard", "detailed"):
        raise HTTPException(status_code=400, detail="depth must be 'brief', 'standard', or 'detailed'")

    try:
        context = await TextStorageService.load_text(clean_text_file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {clean_text_file_path}")

    thread_id = str(uuid.uuid4())
    initial_state = {
        "context": context,
        "depth": depth,
        "key_terms": "",
        "tldr": "",
        "structured_notes": "",
        "paragraph_summary": "",
        "feedback": "",
        "old_output": "",
    }
    config = {"configurable": {"thread_id": thread_id}}

    # Yield thread_id first so client can store it before streaming starts
    async def event_stream():
        yield f'data: {json.dumps({"event": "session_start", "thread_id": thread_id, "depth": depth})}\n\n'
        async for chunk in _stream_graph(initial_state, config, thread_id):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ─────────────────────────────────────────
# Continue with Feedback
# ─────────────────────────────────────────

@SGRoute.post("/SG_continue")
async def continue_after_feedback(
    background_tasks: BackgroundTasks,
    project_id: str = Body(..., embed=True),
    clean_text_file_path: str = Body(..., embed=True),
    user_feedback: str = Body(..., embed=True),
    thread_id: str = Body(..., embed=True),
):
    config = {"configurable": {"thread_id": thread_id}}
    resume_command = Command(resume=user_feedback)

    async def event_stream():
        yield f'data: {json.dumps({"event": "session_continue", "thread_id": thread_id})}\n\n'
        async for chunk in _stream_graph(resume_command, config, thread_id):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")