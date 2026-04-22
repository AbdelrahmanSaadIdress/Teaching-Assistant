from typing import TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document

class QuestionAnsweringState(TypedDict):
    message: list[BaseMessage]
    relevant_text: list[Document]
    on_topic: str
    context: str
    conversation_history: list[BaseMessage]

