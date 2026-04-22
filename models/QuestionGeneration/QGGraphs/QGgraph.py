import os
from dotenv import load_dotenv
load_dotenv()

from helpers import get_settings, Settings, save_graph_png
from stores.llm import LLMProviderFactory

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate


from ..QGStates import QuestionGenState
from ..QGPrompts import QuestionGenPrompt as question_generation_prompt
from ..QGPrompts import QuestionRefinerPrompt as question_refiner_prompt
from ..QGPrompts import QuestionRewriterPrompt as question_rewriter_prompt

from ..QGSchemaes import Question as question_schema
from ..QGSchemaes import Feedback as feedback_schema


app_settings = get_settings()
def history_to_text(history):
    """Convert mixed history (str or AIMessage) to plain string list"""
    result = []
    for item in history:
        if isinstance(item, str):
            result.append(item)
        elif hasattr(item, "content"):  # AIMessage or HumanMessage
            result.append(item.content)
        else:
            result.append(str(item))
    return result


def question_generation(state:QuestionGenState)->QuestionGenState:
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
        )
    chain = question_generation_prompt | model.with_structured_output(question_schema)
    response = chain.invoke({"question_type":state["question_type"], "context":state["context"]})
    state["question"] = response.question
    state["options"] = response.options
    state["answer"] = response.answer
    state["explanation"] = response.explanation
    if state.get("history") is None:
        state["history"] = []
    return state

def human_feedback(state:QuestionGenState)->QuestionGenState:
    feedback_payload = {
        "context":state["context"],
        "question_type":state["question_type"],
        "question":state["question"],
        "options":state["options"],
        "answer":state["answer"],
        "explanation":state["explanation"],
        "history":state["history"],
        "feedback_requesting_message":"please enter you feedback"
    }
    user_feedback = interrupt(feedback_payload)
    state["feedback"] = user_feedback
    return state

def question_refiner(state:QuestionGenState)->QuestionGenState:
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
        )
    chain = question_refiner_prompt | model.with_structured_output(feedback_schema)
    response = chain.invoke({"question":state["question"], "options":state["options"], "answer":state["answer"], "explanation":state["explanation"] })
    state["feedback"] = response.feedback
    return state

def question_rewriter(state:QuestionGenState)->QuestionGenState:

    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
        )
    
    GeneratedQuestionFormat = """Question_Type: {Question_Type}, Transcript: {Context}, Question: {Question}\nOptions: {Options}\nAnswer: {Answer}\nExplanation: {Explanation}"""
    NewQuestionFormat = """Question_Type: {Question_Type}, Question: {Question}\nOptions: {Options}\nAnswer: {Answer}\nExplanation: {Explanation}"""
    if state["question_type"] == "MCQ" and isinstance(state["options"], str):
        state["options"] = [opt.strip() for opt in state["options"].split("\n") if opt.strip()]
    elif state["question_type"] == "T/F":
        state["options"] = None
    Original_Question = GeneratedQuestionFormat.format(
        Question_Type=state["question_type"],
        Context=state["context"],
        Question=state["question"],
        Options=state["options"],
        Answer=state["answer"],
        Explanation=state["explanation"]
    )
    chain = question_rewriter_prompt | model.with_structured_output(question_schema)
    response = chain.invoke({"original_question":Original_Question, "feedback":state["feedback"], "history":state["history"]})
    state["question_type"] = state["question_type"] 
    state["question"] = response.question
    state["options"] = response.options
    state["answer"] = response.answer
    state["explanation"] = response.explanation
    
    New_Question = NewQuestionFormat.format(
        Question_Type=response.question_type,
        Question=response.question,
        Options=response.options,
        Answer=response.answer,
        Explanation=response.explanation
    )

    from langchain_core.prompts import ChatPromptTemplate

    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert assistant. Summarize the following history of question generations and refinements into a concise summary, keeping all important decisions, feedback, and changes."),
        ("user", "{history_text}"),
        ("system", "Return a short, clear summary suitable for storing in state['history'].")
    ])
    if len(state["history"]) > 0:
        new_entry = f"Original Question: {Original_Question}\nFeedback: {state['feedback']}\nNew Question: {New_Question}\nGenerate only new question\n"
        # Combine into single text for summarization
        history_strings = history_to_text(state.get("history", []))
        history_text = "\n".join(history_strings + [new_entry])

        summary_chain = summary_prompt | model
        summary_result = summary_chain.invoke({"history_text": history_text})
        state["history"] = [summary_result]
    else:
        state["history"].append(f"Feedback: {state['feedback']}\n New question: {New_Question}\n Generate only new question\n")

    return state

def Router(state: QuestionGenState) -> str:
    if state["feedback"].lower() == "save":
        return "save"
    elif state["feedback"].lower() == "auto":
        return "auto"
    else:
        return "feedback"


graph = StateGraph(QuestionGenState)

graph.add_node("question_generation", question_generation)
graph.add_node("human_feedback", human_feedback)
graph.add_node("question_refiner", question_refiner)
graph.add_node("question_rewriter", question_rewriter)

graph.add_edge(START, "question_generation")
graph.add_edge("question_generation", "human_feedback")

graph.add_conditional_edges("human_feedback", Router, {"save": END, "auto": "question_refiner", "feedback": "question_rewriter"})

graph.add_edge("question_refiner", "question_rewriter")
graph.add_edge("question_rewriter", "human_feedback")


memory = MemorySaver()  
QG_Graph = graph.compile(checkpointer=memory)


# save_graph_png(QG_Graph, filename="qg_graph")