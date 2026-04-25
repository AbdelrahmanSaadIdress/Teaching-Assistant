import os
from dotenv import load_dotenv
load_dotenv()

from helpers import get_settings, Settings
from stores.llm import LLMProviderFactory

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate

from typing import TypedDict, Literal, Union, List

# ─────────────────────────────────────────
# State
# ─────────────────────────────────────────

class BulkQuestionItem(TypedDict):
    question: str
    question_type: str
    complexity: str
    options: Union[List[str], None]
    answer: str
    explanation: str


class BulkQuestionGenState(TypedDict):
    context: str
    question_type: Literal["T/F", "MCQ", "Both"]
    num_questions: int
    questions: List[BulkQuestionItem]
    feedback: str
    history: list


# ─────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────

BULK_GENERATION_SYSTEM = """
You are an expert educational question generator.

Given a transcript/context, generate exactly {num_questions} questions of type: {question_type}.

Rules:
- Distribute complexity naturally: roughly 1/3 easy, 1/3 medium, 1/3 hard (adjust for small counts).
- Every question must be answerable ONLY from the provided context.
- For MCQ: provide exactly 4 options as a JSON array ["A. ...", "B. ...", "C. ...", "D. ..."], answer must be a single letter A/B/C/D.
- For T/F: options must be null, answer must be exactly "True" or "False".
- If question_type is "Both", mix MCQ and T/F questions.
- Avoid repeating concepts across questions.
- Each question must be clear, unambiguous, and academically appropriate.

Return a JSON object with a "questions" array. Each item must have:
  question, question_type, complexity (easy/medium/hard), options, answer, explanation.
"""

BULK_REWRITE_SYSTEM = """
You are an expert educational question rewriter.

The user provided feedback on a set of questions. Rewrite ALL questions incorporating the feedback.
Keep questions that were good, fix or replace ones with issues.
Maintain the same count ({num_questions}) and type ({question_type}).

Previous generation history:
{history}

User feedback: {feedback}

Original questions:
{original_questions}

Rules (same as before):
- For MCQ: options as JSON array ["A. ...", "B. ...", "C. ...", "D. ..."], answer = single letter.
- For T/F: options = null, answer = "True" or "False".
- Distribute complexity: easy / medium / hard.
- All answers must be supported by the context.

Return a JSON object with a "questions" array.
"""


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _questions_to_text(questions: List[BulkQuestionItem]) -> str:
    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i} [{q['complexity'].upper()}] ({q['question_type']}): {q['question']}")
        if q.get("options"):
            for opt in q["options"]:
                lines.append(f"   {opt}")
        lines.append(f"   Answer: {q['answer']}")
        lines.append(f"   Explanation: {q['explanation']}")
        lines.append("")
    return "\n".join(lines)


def _history_to_text(history: list) -> str:
    result = []
    for item in history:
        if isinstance(item, str):
            result.append(item)
        elif hasattr(item, "content"):
            result.append(item.content)
        else:
            result.append(str(item))
    return "\n".join(result)


def _parse_questions(raw_questions) -> List[BulkQuestionItem]:
    """Convert pydantic BulkQuestion objects to plain dicts."""
    result = []
    for q in raw_questions:
        options = q.options
        if isinstance(options, str):
            options = [o.strip() for o in options.split("\n") if o.strip()]
        result.append({
            "question": q.question,
            "question_type": q.question_type,
            "complexity": q.complexity,
            "options": options,
            "answer": q.answer,
            "explanation": q.explanation,
        })
    return result


# ─────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────

app_settings = get_settings()


def bulk_question_generation(state: BulkQuestionGenState) -> BulkQuestionGenState:
    # Import here to avoid circular imports in your project
    from .schema import BulkQuestionSet

    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", BULK_GENERATION_SYSTEM),
        ("user", "Context:\n{context}"),
    ])

    chain = prompt | model.with_structured_output(BulkQuestionSet)
    response = chain.invoke({
        "num_questions": state["num_questions"],
        "question_type": state["question_type"],
        "context": state["context"],
    })

    state["questions"] = _parse_questions(response.questions)
    if state.get("history") is None:
        state["history"] = []
    return state


def human_feedback(state: BulkQuestionGenState) -> BulkQuestionGenState:
    feedback_payload = {
        "questions": state["questions"],
        "question_type": state["question_type"],
        "num_questions": state["num_questions"],
        "feedback_requesting_message": "Review the questions. Type 'save' to accept, or provide feedback to improve them.",
    }
    user_feedback = interrupt(feedback_payload)
    state["feedback"] = user_feedback
    return state


def bulk_question_rewriter(state: BulkQuestionGenState) -> BulkQuestionGenState:
    from .schema import BulkQuestionSet

    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE,
    )

    original_questions_text = _questions_to_text(state["questions"])
    history_text = _history_to_text(state.get("history", []))

    prompt = ChatPromptTemplate.from_messages([
        ("system", BULK_REWRITE_SYSTEM),
        ("user", "Context:\n{context}"),
    ])

    chain = prompt | model.with_structured_output(BulkQuestionSet)
    response = chain.invoke({
        "num_questions": state["num_questions"],
        "question_type": state["question_type"],
        "history": history_text,
        "feedback": state["feedback"],
        "original_questions": original_questions_text,
        "context": state["context"],
    })

    # Append to history
    entry = (
        f"Feedback: {state['feedback']}\n"
        f"Previous questions:\n{original_questions_text}\n"
    )
    state["history"] = state.get("history", []) + [entry]
    state["questions"] = _parse_questions(response.questions)
    return state


def Router(state: BulkQuestionGenState) -> str:
    if state["feedback"].strip().lower() == "save":
        return "save"
    return "rewrite"


# ─────────────────────────────────────────
# Graph
# ─────────────────────────────────────────

graph = StateGraph(BulkQuestionGenState)

graph.add_node("bulk_question_generation", bulk_question_generation)
graph.add_node("human_feedback", human_feedback)
graph.add_node("bulk_question_rewriter", bulk_question_rewriter)

graph.add_edge(START, "bulk_question_generation")
graph.add_edge("bulk_question_generation", "human_feedback")

graph.add_conditional_edges(
    "human_feedback",
    Router,
    {"save": END, "rewrite": "bulk_question_rewriter"},
)
graph.add_edge("bulk_question_rewriter", "human_feedback")

memory = MemorySaver()
BulkQG_Graph = graph.compile(checkpointer=memory)