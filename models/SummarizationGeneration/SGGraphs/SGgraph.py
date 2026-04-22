import os
from dotenv import load_dotenv
load_dotenv()

from helpers import get_settings, Settings, save_graph_png
from stores.llm import LLMProviderFactory

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


from ..SGStates import SummaryGenState
from ..SGPrompts import MainpointsSummaryPrompt as mainpoints_summarization_prompt
from ..SGPrompts import SummaryWriterPrompt as summary_writer_prompt
from ..SGPrompts import SummaryRewriterPrompt as summary_rewriter_prompt



async def main_point_summarizer(state:SummaryGenState)->SummaryGenState:
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
        )
    chain = mainpoints_summarization_prompt | model
    response =  await chain.ainvoke({"context":state["context"]})
    state["Main_Points"] = response.content
    return state

async def summary_writer(state:SummaryGenState)->SummaryGenState:
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
    )
    chain = summary_writer_prompt | model
    response = await chain.ainvoke({"context":state["context"], "table_of_contents":state["Main_Points"]})
    state["summary"] = response.content
    return state

async def human_feedback(state:SummaryGenState)->SummaryGenState:
    feedback_payload = {
        "context":state["context"],
        "summary":state["summary"],
        "Main_Points":state["Main_Points"],
        "history":state["history"] if hasattr(state, "history") else None,
        "feedback_requesting_message":"please enter your feedback"
    }
    user_feedback = interrupt(feedback_payload)
    state["feedback"] = user_feedback
    return state

def Router(state: SummaryGenState) -> str:
    if state["feedback"].lower() == "save":
        return "save"
    else:
        return "feedback"

async def summary_rewriter(state:SummaryGenState)->SummaryGenState:
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
    )
    state["old_summary"] = state["summary"]
    chain = summary_rewriter_prompt | model
    response = await chain.ainvoke({"context":state["context"], "original_summary":state["summary"], "user_feedback":state["feedback"]})
    state["summary"] = response.content
    return state



app_settings = get_settings()


graph = StateGraph(SummaryGenState)

graph.add_node("main_point_summarizer", main_point_summarizer)
graph.add_node("summary_writer", summary_writer)
graph.add_node("human_feedback", human_feedback)
graph.add_node("summary_rewriter", summary_rewriter)

graph.add_edge(START, "main_point_summarizer")
graph.add_edge("main_point_summarizer", "summary_writer")
graph.add_edge("summary_writer", "human_feedback")

graph.add_conditional_edges("human_feedback", Router, {"save":END, "feedback":"summary_rewriter"})

graph.add_edge("summary_rewriter", "human_feedback")

memory = MemorySaver()  
SG_Graph = graph.compile(checkpointer=memory)


# save_graph_png(QG_Graph, filename="qg_graph")