import gradio as gr
import requests
import mimetypes
import json

# ----------------------
# Configuration
# ----------------------
FASTAPI_BASE_URL = "http://localhost:5000/api/TA"

# ======================
# 🎨 ADD THIS CSS (NEW)
# ======================
custom_css = """
/* New vibrant background */
body {
    background: linear-gradient(135deg, #0f172a, #3b0764, #6366f1);
}

/* Container */
.gradio-container {
    max-width: 1200px !important;
    margin: auto;
    font-family: Inter, system-ui, sans-serif;
}

/* Card feel */
.block {
    background: rgba(15, 23, 42, 0.95) !important; /* slightly darker for contrast */
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid #1e293b !important;
}

/* Titles */
h1 {
    background: linear-gradient(90deg, #6366f1, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Buttons */
button {
    background: linear-gradient(135deg, #6366f1, #a855f7) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(163, 94, 255, 0.4);
}

/* Inputs */
textarea, input {
    background: #0f172a !important;
    color: #e5e7eb !important;
    border-radius: 12px !important;
    border: 1px solid #1e293b !important;
}

/* Tabs */
.tab-nav button {
    color: #c7d2fe !important;
    font-weight: 600;
}

.tab-nav button.selected {
    background: #1e293b !important;
    border-radius: 12px;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #6366f1;
    border-radius: 10px;
}
"""


# ----------------------
# Helper Functions
# ----------------------
def upload_file_to_fastapi(file, project_id):
    if file is None or project_id.strip() == "":
        return "❌ Error: File and Project ID are required.", None, None
    with open(file.name, "rb") as f:
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        files = {"file": (file.name, f, mime_type)}
        data = {"project_id": project_id}
        try:
            response = requests.post(f"{FASTAPI_BASE_URL}/fileProcessing", files=files, data=data)
            if response.status_code == 200:
                json_resp = response.json()
                clean_text_path = json_resp.get("text_file")
                return (
                    f"✅ File processed successfully!\n"
                    f"Thread ID: {json_resp.get('thread_id')}\n"
                    f"Uploaded File: {json_resp.get('uploaded_file')}\n"
                    f"Extracted Text File: {clean_text_path}",
                    json_resp.get("thread_id"),
                    clean_text_path
                )
            else:
                return f"❌ Error {response.status_code}: {response.text}", None, None
        except Exception as e:
            return f"❌ Exception: {str(e)}", None, None


# ----------------------
# Question Generation
# ----------------------
def start_question_generation(project_id, thread_id, question_type, clean_text_file_path):
    if not thread_id or not clean_text_file_path:
        return "❌ Error: Please upload and process a file first.", None
    payload = {
        "project_id": project_id,
        "question_type": question_type,
        "clean_text_file_path": clean_text_file_path
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/start_session", json=payload)
        if response.status_code == 200:
            json_resp = response.json()
            question_data = json_resp.get("graph_response", {})
            options = question_data.get('options')
            if isinstance(options, list):
                options = "\n".join(options)
            return (
                f"✅ Question Generated Successfully!\n\n"
                f"Question: {question_data.get('question')}\n"
                f"Options:\n{options}\n"
                f"Answer: {question_data.get('answer')}\n"
                f"Explanation: {question_data.get('explanation')}",
                json_resp.get("thread_id")
            )
        else:
            return f"❌ Error {response.status_code}: {response.text}", None
    except Exception as e:
        return f"❌ Exception: {str(e)}", None

def continue_question_generation(project_id, thread_id, user_feedback, question_type, clean_text_file_path):
    if not thread_id or not clean_text_file_path:
        return "❌ Error: Please start a question generation session first.", None
    payload = {
        "project_id": project_id,
        "thread_id": thread_id,
        "user_feedback": user_feedback,
        "question_type": question_type,
        "clean_text_file_path": clean_text_file_path
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/continue", json=payload)
        if response.status_code == 200:
            json_resp = response.json()
            question_data = json_resp.get("graph_response", {})
            options = question_data.get('options')
            if isinstance(options, list):
                options = "\n".join(options)
            return (
                f"✅ Question Updated!\n\n"
                f"Question: {question_data.get('question')}\n"
                f"Options:\n{options}\n"
                f"Answer: {question_data.get('answer')}\n"
                f"Explanation: {question_data.get('explanation')}",
                json_resp.get("thread_id")
            )
        else:
            return f"❌ Error {response.status_code}: {response.text}", None
    except Exception as e:
        return f"❌ Exception: {str(e)}", None

# ----------------------
# Streaming QA
# ----------------------
def start_qa_streaming(clean_text_file_path, user_question):
    payload = {"clean_text_file_path": clean_text_file_path, "user_question": user_question}
    resp = requests.post(f"{FASTAPI_BASE_URL}/start_QA_session", json=payload, stream=True)
    answer = ""
    thread_id = None
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            data_json = json.loads(line[6:])
            thread_id = data_json.get("thread_id", thread_id)
            if data_json.get("event") == "token":
                answer += data_json.get("token", "")
                yield answer, thread_id
    yield answer, thread_id

# ----------------------
# Streaming Summarization
# ----------------------
def start_summarization_stream(clean_text_file_path, project_id):
    payload = {"clean_text_file_path": clean_text_file_path, "project_id": project_id}
    resp = requests.post(f"{FASTAPI_BASE_URL}/start_SG_session", json=payload, stream=True)
    summary = ""
    thread_id = None
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            data_json = json.loads(line[6:])
            thread_id = data_json.get("thread_id", thread_id)
            if data_json.get("event") == "token":
                summary += data_json.get("token", "")
                yield summary, thread_id
    yield summary, thread_id

# ----------------------
# Continue Summarization with Feedback (Streaming)
# ----------------------
def continue_summarization_feedback_stream(project_id, clean_text_file_path, thread_id, user_feedback):
    payload = {
        "project_id": project_id,
        "clean_text_file_path": clean_text_file_path,
        "thread_id": thread_id,
        "user_feedback": user_feedback
    }
    resp = requests.post(f"{FASTAPI_BASE_URL}/SG_continue", json=payload, stream=True)
    summary = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            data_json = json.loads(line[6:])
            if data_json.get("event") == "token":
                summary += data_json.get("token", "")
                yield summary
    yield summary

# ----------------------
# Gradio Interface
# ----------------------
with gr.Blocks() as demo:
    gr.Markdown("# 🧠 College Study Assistant (LLM-Powered)")
    gr.Markdown(
    "<h3 style='background: linear-gradient(90deg, #6366f1, #22d3ee); "
    "-webkit-background-clip: text; -webkit-text-fill-color: transparent;'>"
    "Upload documents, generate questions, ask questions, and summarize content interactively."
    "</h3>"
    )
    qg_thread_id = gr.State(None)
    qa_thread_id = gr.State(None)
    sg_thread_id = gr.State(None)
    clean_text_file_path_state = gr.State(None)

    with gr.Tabs():

        with gr.TabItem("📄 File Processing"):
            file_input = gr.File(label="Upload File")
            project_id_input = gr.Textbox(label="Project ID", placeholder="Enter Project ID")
            process_btn = gr.Button("Upload & Process")
            process_output = gr.Textbox(label="Output", lines=6)
            process_btn.click(
                upload_file_to_fastapi,
                inputs=[file_input, project_id_input],
                outputs=[process_output, qg_thread_id, clean_text_file_path_state]
            )

        with gr.TabItem("❓ Question Generation"):
            question_type_input = gr.Dropdown(["MCQ", "T/F"], label="Question Type", value="MCQ")
            generate_btn = gr.Button("Generate Question")
            question_output = gr.Textbox(label="Generated Question", lines=8)
            generate_btn.click(
                start_question_generation,
                inputs=[project_id_input, qg_thread_id, question_type_input, clean_text_file_path_state],
                outputs=[question_output, qg_thread_id]
            )

            feedback_input = gr.Textbox(label="Feedback", placeholder="Type feedback, 'auto' or 'save'")
            continue_btn = gr.Button("Apply Feedback")
            continue_output = gr.Textbox(label="Updated Question", lines=8)
            continue_btn.click(
                continue_question_generation,
                inputs=[project_id_input, qg_thread_id, feedback_input, question_type_input, clean_text_file_path_state],
                outputs=[continue_output, qg_thread_id]
            )

        with gr.TabItem("🗨️ Question Answering"):
            user_question_input = gr.Textbox(label="Your Question", placeholder="Type a question here")
            qa_output = gr.Textbox(label="Answer", lines=8)
            qa_btn = gr.Button("Ask Question")
            qa_btn.click(
                start_qa_streaming,
                inputs=[clean_text_file_path_state, user_question_input],
                outputs=[qa_output, qa_thread_id]
            )

        with gr.TabItem("📝 Summarization"):
            summarize_output = gr.Textbox(label="Summary", lines=8)
            summarize_btn = gr.Button("Summarize Text")
            summarize_btn.click(
                start_summarization_stream,
                inputs=[clean_text_file_path_state, project_id_input],
                outputs=[summarize_output, sg_thread_id],
                queue=True
            )

            sg_feedback_input = gr.Textbox(label="Feedback on Summary", placeholder="Type feedback to improve summary")
            sg_continue_btn = gr.Button("Apply Summary Feedback")
            sg_continue_output = gr.Textbox(label="Updated Summary", lines=8)
            sg_continue_btn.click(
                continue_summarization_feedback_stream,
                inputs=[project_id_input, clean_text_file_path_state, sg_thread_id, sg_feedback_input],
                outputs=[sg_continue_output],
                queue=True
            )

# ======================
# 🎨 ADD CSS HERE (NEW)
# ======================
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,
    css=custom_css
)
