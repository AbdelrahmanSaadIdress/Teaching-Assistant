from typing import TypedDict, Literal, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.schema import Document

class QuestionGenState(TypedDict):
    context: str
    question_type: Literal["T/F", "MCQ"]
    question: str
    options: Union[list[str], None]
    answer: str
    explanation: str
    history: list = []
    feedback: str