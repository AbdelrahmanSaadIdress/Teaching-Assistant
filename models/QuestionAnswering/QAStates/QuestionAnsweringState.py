from typing import TypedDict
from langchain_core.messages import BaseMessage
from langchain.schema import Document

class QuestionAnsweringState(TypedDict):
    message: list[BaseMessage]
    relevant_text: list[Document]
    on_topic: str
    context: str
    conversation_history: list[BaseMessage]

