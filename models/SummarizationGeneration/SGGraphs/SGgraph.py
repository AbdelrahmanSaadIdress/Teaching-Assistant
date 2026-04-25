import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

from helpers import get_settings
from stores.llm import LLMProviderFactory

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from ..SGStates import SummaryGenState
from ..SGPrompts import (
    DEPTH_GUIDE,
    KeyTermsPrompt,
    TLDRPrompt,
    StructuredNotesPrompt,
    ParagraphSummaryPrompt,
    SummaryRewriterPrompt,
)

app_settings = get_settings()


def _make_model():
    return LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE,
    )


def _depth_guide(depth: str) -> str:
    return DEPTH_GUIDE.format(depth=depth)


# ─────────────────────────────────────────
# Node 1 — Key Terms
# ─────────────────────────────────────────

async def extract_key_terms(state: SummaryGenState) -> SummaryGenState:
    model = _make_model()
    chain = KeyTermsPrompt | model
    response = await chain.ainvoke({
        "context": state["context"],
        "depth": state["depth"],
        "depth_guide": _depth_guide(state["depth"]),
    })
    # Store raw JSON string; UI will parse it
    state["key_terms"] = response.content.strip()
    return state


# ─────────────────────────────────────────
# Node 2 — TL;DR
# ─────────────────────────────────────────

async def write_tldr(state: SummaryGenState) -> SummaryGenState:
    model = _make_model()
    chain = TLDRPrompt | model
    response = await chain.ainvoke({
        "context": state["context"],
        "depth": state["depth"],
        "depth_guide": _depth_guide(state["depth"]),
    })
    state["tldr"] = response.content.strip()
    return state


# ─────────────────────────────────────────
# Node 3 — Structured Notes
# ─────────────────────────────────────────

async def write_structured_notes(state: SummaryGenState) -> SummaryGenState:
    model = _make_model()
    chain = StructuredNotesPrompt | model
    response = await chain.ainvoke({
        "context": state["context"],
        "depth": state["depth"],
        "depth_guide": _depth_guide(state["depth"]),
    })
    state["structured_notes"] = response.content.strip()
    return state


# ─────────────────────────────────────────
# Node 4 — Paragraph Summary
# ─────────────────────────────────────────

async def write_paragraph_summary(state: SummaryGenState) -> SummaryGenState:
    model = _make_model()
    chain = ParagraphSummaryPrompt | model
    response = await chain.ainvoke({
        "context": state["context"],
        "structured_notes": state["structured_notes"],
        "depth": state["depth"],
        "depth_guide": _depth_guide(state["depth"]),
    })
    state["paragraph_summary"] = response.content.strip()
    return state


# ─────────────────────────────────────────
# Node 5 — Human Feedback (interrupt)
# ─────────────────────────────────────────

async def human_feedback(state: SummaryGenState) -> SummaryGenState:
    payload = {
        "depth": state["depth"],
        "key_terms": state["key_terms"],
        "tldr": state["tldr"],
        "structured_notes": state["structured_notes"],
        "paragraph_summary": state["paragraph_summary"],
        "feedback_requesting_message": (
            "Review your study materials. Type 'save' to keep them, "
            "'auto' to auto-improve, or give specific feedback."
        ),
    }
    user_feedback = interrupt(payload)
    state["feedback"] = user_feedback
    return state


# ─────────────────────────────────────────
# Node 6 — Rewriter
# ─────────────────────────────────────────

def _parse_rewriter_output(raw: str) -> dict:
    """Parse the ===SECTION=== delimited rewriter output."""
    sections = {
        "key_terms": "",
        "tldr": "",
        "structured_notes": "",
        "paragraph_summary": "",
    }
    markers = {
        "===KEY_TERMS===": "key_terms",
        "===TLDR===": "tldr",
        "===STRUCTURED_NOTES===": "structured_notes",
        "===PARAGRAPH_SUMMARY===": "paragraph_summary",
    }
    current_key = None
    lines = raw.split("\n")
    buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped in markers:
            if current_key and buffer:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = markers[stripped]
            buffer = []
        else:
            if current_key:
                buffer.append(line)

    # flush last section
    if current_key and buffer:
        sections[current_key] = "\n".join(buffer).strip()

    return sections


async def summary_rewriter(state: SummaryGenState) -> SummaryGenState:
    model = _make_model()

    # Snapshot before rewrite
    state["old_output"] = json.dumps({
        "key_terms": state.get("key_terms", ""),
        "tldr": state.get("tldr", ""),
        "structured_notes": state.get("structured_notes", ""),
        "paragraph_summary": state.get("paragraph_summary", ""),
    })

    chain = SummaryRewriterPrompt | model
    response = await chain.ainvoke({
        "context": state["context"],
        "depth": state["depth"],
        "depth_guide": _depth_guide(state["depth"]),
        "key_terms": state.get("key_terms", ""),
        "tldr": state.get("tldr", ""),
        "structured_notes": state.get("structured_notes", ""),
        "paragraph_summary": state.get("paragraph_summary", ""),
        "user_feedback": state["feedback"],
    })

    parsed = _parse_rewriter_output(response.content)
    state["key_terms"] = parsed["key_terms"] or state["key_terms"]
    state["tldr"] = parsed["tldr"] or state["tldr"]
    state["structured_notes"] = parsed["structured_notes"] or state["structured_notes"]
    state["paragraph_summary"] = parsed["paragraph_summary"] or state["paragraph_summary"]

    return state


# ─────────────────────────────────────────
# Router
# ─────────────────────────────────────────

def Router(state: SummaryGenState) -> str:
    if state["feedback"].strip().lower() == "save":
        return "save"
    return "rewrite"


# ─────────────────────────────────────────
# Graph construction
# ─────────────────────────────────────────

graph = StateGraph(SummaryGenState)

graph.add_node("extract_key_terms", extract_key_terms)
graph.add_node("write_tldr", write_tldr)
graph.add_node("write_structured_notes", write_structured_notes)
graph.add_node("write_paragraph_summary", write_paragraph_summary)
graph.add_node("human_feedback", human_feedback)
graph.add_node("summary_rewriter", summary_rewriter)

# Pipeline
graph.add_edge(START, "extract_key_terms")
graph.add_edge("extract_key_terms", "write_tldr")
graph.add_edge("write_tldr", "write_structured_notes")
graph.add_edge("write_structured_notes", "write_paragraph_summary")
graph.add_edge("write_paragraph_summary", "human_feedback")

# Feedback loop
graph.add_conditional_edges(
    "human_feedback",
    Router,
    {"save": END, "rewrite": "summary_rewriter"},
)
graph.add_edge("summary_rewriter", "human_feedback")

memory = MemorySaver()
SG_Graph = graph.compile(checkpointer=memory)