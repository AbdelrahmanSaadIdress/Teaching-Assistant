from typing import TypedDict, Literal, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.schema import Document

class SummaryGenState(TypedDict):
    context: str
    summary: str
    old_summary: str
    feedback: str
    Main_Points: str