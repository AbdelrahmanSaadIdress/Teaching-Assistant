import os
from dotenv import load_dotenv
load_dotenv()

from helpers import get_settings, Settings, save_graph_png
from stores.llm import LLMProviderFactory, EmbeddingProviderFactory

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..QAStates import QuestionAnsweringState
from ..QAPrompts import GradeQuestionPrompt as question_grading_prompt
from ..QASchemaes import GradeQuestion as grade_question_schema


# ===========================
# Nodes for QA Graph
# ===========================

async def question_grading(state: QuestionAnsweringState) -> QuestionAnsweringState:
    """
    Grades the user question as on-topic or off-topic,
    performs retrieval of relevant context.
    """
    model = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
    )

    chain = question_grading_prompt | model.with_structured_output(grade_question_schema)
    response = await chain.ainvoke({
        "docs": state["context"], 
        "question": state["message"][-1].content
    })

    state["on_topic"] = response.score
    state.setdefault("conversation_history", [])

    # Prepare retriever
    embedding_function = EmbeddingProviderFactory(app_settings).create(
        provider=app_settings.EMBEDDING_BACKEND,
        model_name=app_settings.EMBEDDING_MODEL_ID
    )
    db = Chroma(persist_directory=os.path.join("assets/vector_dB",app_settings.VECTOR_DB_PATH), embedding_function=embedding_function)
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5,"score_threshold": 0.6}
    )
    retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 5})
    state["relevant_text"] = retriever.invoke(state["message"][-1].content)

    return state


def Router(state: QuestionAnsweringState) -> str:
    """Decides next node based on whether the question is on-topic."""
    if state["on_topic"].lower() == "yes":
        return "retriever"
    return "off_topic_response"


async def retriever(state: QuestionAnsweringState) -> QuestionAnsweringState:
    """Simply passes the state forward; context is already retrieved."""
    return state


async def question_answer(state: QuestionAnsweringState) -> QuestionAnsweringState:
    """Generates an answer based on retrieved context and conversation history."""
    question = state["message"][-1].content
    documents = state["relevant_text"]
    chat_history = state.get("conversation_history", [])

    template = """
        Answer the question based only on the following context: {context},
        chat history: {chat_history},
        Question: {question}
    """

    llm = LLMProviderFactory(app_settings).create(
        provider=app_settings.GENERATION_BACKEND,
        model_id=app_settings.GENERATION_MODEL_ID,
        model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
    )

    prompt = ChatPromptTemplate.from_template(template)
    rag_chain = prompt | llm
    res = await rag_chain.ainvoke({
        "context": documents,
        "chat_history": chat_history,
        "question": question
    })

    # Append messages and response to conversation history
    state["conversation_history"] += state["message"] + [res]
    state["message"] = []
    return state


async def off_topic_response(state: QuestionAnsweringState) -> QuestionAnsweringState:
    """
    Handles questions determined to be off-topic.
    Streams a fixed response.
    """
    fixed_reply = AIMessage(
        content="I'm sorry, this question seems unrelated to the topic. Please ask something relevant."
    )

    # Append user message and fixed response to conversation history
    state["conversation_history"] += state["message"] + [fixed_reply]
    state["message"] = []
    state["relevant_text"] = []
    state["on_topic"] = "No"

    return state


# ===========================
# Graph Construction
# ===========================

app_settings = get_settings()
graph = StateGraph(QuestionAnsweringState)

# Nodes
graph.add_node("question_grading", question_grading)
graph.add_node("retriever", retriever)
graph.add_node("question_answer", question_answer)
graph.add_node("off_topic_response", off_topic_response)

# Edges
graph.add_edge(START, "question_grading")
graph.add_conditional_edges(
    "question_grading",
    Router,
    {"retriever": "retriever", "off_topic_response": "off_topic_response"}
)
graph.add_edge("retriever", "question_answer")
graph.add_edge("question_answer", END)
graph.add_edge("off_topic_response", END)

# Memory and compiled graph
memory = MemorySaver()
QA_Graph = graph.compile(checkpointer=memory)

# Optional: save visual graph
# save_graph_png(QA_Graph, filename="qa_graph.png")
