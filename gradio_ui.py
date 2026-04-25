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


/* Exam card styles */
.exam-question-card {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.complexity-easy   { color: #4ade80; font-weight: 700; }
.complexity-medium { color: #facc15; font-weight: 700; }
.complexity-hard   { color: #f87171; font-weight: 700; }

/* Score panel */
.score-correct   { color: #4ade80; }
.score-incorrect { color: #f87171; }

"""

# These hold the current exam questions between Gradio callbacks.
_exam_questions = []   # list of question dicts from the backend
_exam_thread_id = None
_exam_global_flag = False

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
global_qg_flag = False

def start_question_generation(project_id, thread_id, question_type, clean_text_file_path):
    global global_qg_flag
    if  global_qg_flag:
        _ = continue_question_generation(project_id, thread_id, "save", question_type, clean_text_file_path)
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
                f"\n==================================================\n"
                f"Answer: {question_data.get('answer')}\n"
                f"Explanation: {question_data.get('explanation')}",
                json_resp.get("thread_id")
            )
        else:
            return f"❌ Error {response.status_code}: {response.text}", None
    except Exception as e:
        return f"❌ Exception: {str(e)}", None
    
    global_qg_flag = True

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


# ─────────────────────────────────────────
# Bulk Question Generation helpers
# ─────────────────────────────────────────

def _complexity_badge(level: str) -> str:
    icons = {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}
    return icons.get(level.lower(), level)

def _render_questions_preview(questions: list) -> str:
    """Render questions as readable text for the preview box."""
    if not questions:
        return ""
    lines = []
    for i, q in enumerate(questions, 1):
        badge = _complexity_badge(q.get("complexity", ""))
        qtype = q.get("question_type", "")
        lines.append(f"─── Q{i} | {badge} | {qtype} ───")
        lines.append(q.get("question", ""))
        opts = q.get("options")
        if opts:
            for o in opts:
                lines.append(f"  {o}")
        lines.append("")
    return "\n".join(lines)


def start_bulk_generation(project_id, clean_text_file_path, question_type, num_questions):
    global _exam_questions, _exam_thread_id

    if not clean_text_file_path:
        return "❌ Please upload and process a file first.", "", gr.update(visible=False), gr.update(visible=False)

    payload = {
        "project_id": project_id,
        "question_type": question_type,
        "num_questions": int(num_questions),
        "clean_text_file_path": clean_text_file_path,
    }
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/start_bulk_session", json=payload)
        if resp.status_code != 200:
            return f"❌ Error {resp.status_code}: {resp.text}", "", gr.update(visible=False), gr.update(visible=False)

        data = resp.json()
        _exam_questions = data.get("questions", [])
        _exam_thread_id = data.get("thread_id")

        preview = _render_questions_preview(_exam_questions)
        status_msg = f"✅ Generated {len(_exam_questions)} questions | Thread: {_exam_thread_id}"

        return (
            status_msg,
            preview,
            gr.update(visible=True),   # feedback row
            gr.update(visible=True),   # start exam button
        )
    except Exception as e:
        return f"❌ Exception: {str(e)}", "", gr.update(visible=False), gr.update(visible=False)


def apply_bulk_feedback(feedback_text):
    global _exam_questions, _exam_thread_id

    if not _exam_thread_id:
        return "❌ No active session. Generate questions first.", "", gr.update(visible=False), gr.update(visible=False)

    payload = {"thread_id": _exam_thread_id, "user_feedback": feedback_text}
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/bulk_continue", json=payload)
        if resp.status_code != 200:
            return f"❌ Error {resp.status_code}: {resp.text}", "", gr.update(visible=False), gr.update(visible=False)

        data = resp.json()
        _exam_questions = data.get("questions", [])

        preview = _render_questions_preview(_exam_questions)
        status_msg = f"✅ Questions updated ({len(_exam_questions)} total) | Thread: {_exam_thread_id}"
        return (
            status_msg,
            preview,
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌ Exception: {str(e)}", "", gr.update(visible=False), gr.update(visible=False)

# ─────────────────────────────────────────
# Exam rendering — dynamic radio components
# ─────────────────────────────────────────

def build_exam_ui():
    """
    Called when 'Start Exam' is pressed.
    Returns updates for all 50 possible question slots.
    """
    MAX_Q = 50
    updates = []

    for i in range(MAX_Q):
        if i < len(_exam_questions):
            q = _exam_questions[i]
            badge = _complexity_badge(q.get("complexity", ""))
            qtype = q.get("question_type", "")
            label = f"Q{i+1} | {badge} | {qtype}\n{q['question']}"
            opts = q.get("options") or ["True", "False"]
            updates += [
                gr.update(visible=True, label=label, choices=opts, value=None),  # radio
            ]
        else:
            updates += [
                gr.update(visible=False, choices=[], value=None),
            ]

    # also show submit row, hide start-exam btn
    updates.append(gr.update(visible=True))   # submit_row
    updates.append(gr.update(visible=False))  # start_exam_btn
    return updates


def score_exam(*user_answers):
    """
    Score all answers and produce a detailed results report.
    user_answers: tuple of answers (one per question slot, MAX_Q total)
    """
    if not _exam_questions:
        return "❌ No exam loaded."

    total = len(_exam_questions)
    correct = 0
    lines = ["# 📊 Exam Results\n"]

    for i, q in enumerate(_exam_questions):
        user_ans = user_answers[i] if i < len(user_answers) else None
        correct_ans = q["answer"]
        badge = _complexity_badge(q.get("complexity", ""))
        qtype = q.get("question_type", "")

        # Normalize MCQ: extract letter if user selected "A. Some text"
        normalized_user = ""
        if user_ans:
            normalized_user = user_ans.strip()
            if qtype == "MCQ" and len(normalized_user) > 1 and normalized_user[1] == ".":
                normalized_user = normalized_user[0].upper()

        is_correct = normalized_user.upper() == correct_ans.upper() if normalized_user else False
        if is_correct:
            correct += 1

        result_icon = "✅" if is_correct else "❌"
        lines.append(f"### {result_icon} Q{i+1} | {badge} | {qtype}")
        lines.append(f"**Question:** {q['question']}")

        if q.get("options"):
            for opt in q["options"]:
                lines.append(f"- {opt}")

        lines.append(f"**Your answer:** {user_ans or '(no answer)'}")
        if not is_correct:
            lines.append(f"**Correct answer:** {correct_ans}")
        lines.append(f"**Explanation:** {q['explanation']}")
        lines.append("")

    pct = round(correct / total * 100) if total else 0
    grade_emoji = "🏆" if pct >= 90 else "👍" if pct >= 70 else "📚" if pct >= 50 else "💪"
    summary = f"## {grade_emoji} Score: {correct}/{total} ({pct}%)\n\n"
    return summary + "\n".join(lines)


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
MAX_QUESTIONS = 50  # maximum supported questions in the exam UI
with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# 🧠 College Study Assistant (LLM-Powered)")
    gr.Markdown(
        "<h3 style='background: linear-gradient(90deg, #6366f1, #22d3ee); "
        "-webkit-background-clip: text; -webkit-text-fill-color: transparent;'>"
        "Upload documents, generate questions, take exams, ask questions, and summarize content."
        "</h3>"
    )

    # Shared state
    qg_thread_id = gr.State(None)
    qa_thread_id = gr.State(None)
    sg_thread_id = gr.State(None)
    clean_text_file_path_state = gr.State(None)

    with gr.Tabs():

        # ── Tab 1: File Processing ──────────────────────────────────────
        with gr.TabItem("📄 File Processing"):
            file_input = gr.File(label="Upload File")
            project_id_input = gr.Textbox(label="Project ID", placeholder="Enter Project ID")
            process_btn = gr.Button("Upload & Process")
            process_output = gr.Textbox(label="Output", lines=6)
            process_btn.click(
                upload_file_to_fastapi,
                inputs=[file_input, project_id_input],
                outputs=[process_output, qg_thread_id, clean_text_file_path_state],
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

        with gr.TabItem("❓ Question Generation & Exam"):
 
            gr.Markdown("## ⚙️ Configure Your Exam")
            with gr.Row():
                question_type_input = gr.Dropdown(
                    ["MCQ", "T/F", "Both"],
                    label="Question Type",
                    value="MCQ",
                )
                num_questions_input = gr.Slider(
                    minimum=1, maximum=50, step=1, value=5,
                    label="Number of Questions",
                )
 
            generate_bulk_btn = gr.Button("🎲 Generate Questions", variant="primary")
            generation_status = gr.Textbox(label="Status", lines=1, interactive=False)
            questions_preview = gr.Textbox(
                label="📋 Generated Questions Preview (read-only)",
                lines=15,
                interactive=False,
            )
 
            # Feedback row (hidden until questions exist)
            with gr.Row(visible=False) as feedback_row:
                with gr.Column():
                    gr.Markdown("### 💬 Not happy with these questions?")
                    bulk_feedback_input = gr.Textbox(
                        label="Feedback",
                        placeholder="e.g. 'Make the hard questions harder' or 'Focus more on chapter 3'",
                        lines=2,
                    )
                    apply_feedback_btn = gr.Button("🔄 Apply Feedback & Regenerate")
 
            start_exam_btn = gr.Button("🚀 Start Exam!", variant="primary", visible=False)
 
            # ── Exam UI ─────────────────────────────────────────────────
            gr.Markdown("---")
            gr.Markdown("## 📝 Exam")
 
            # Pre-create MAX_QUESTIONS radio groups (hidden by default)
            question_radios = []
            for idx in range(MAX_QUESTIONS):
                r = gr.Radio(
                    choices=[],
                    label=f"Q{idx+1}",
                    visible=False,
                    interactive=True,
                )
                question_radios.append(r)
 
            with gr.Row(visible=False) as submit_row:
                submit_exam_btn = gr.Button("✅ Submit Exam & See Results", variant="primary")
 
            exam_results = gr.Markdown(label="Results", value="")
 
            # ── Callbacks ───────────────────────────────────────────────
 
            generate_bulk_btn.click(
                start_bulk_generation,
                inputs=[project_id_input, clean_text_file_path_state, question_type_input, num_questions_input],
                outputs=[generation_status, questions_preview, feedback_row, start_exam_btn],
            )
 
            apply_feedback_btn.click(
                apply_bulk_feedback,
                inputs=[bulk_feedback_input],
                outputs=[generation_status, questions_preview, feedback_row, start_exam_btn],
            )
 
            # Start exam: build radio components
            start_exam_btn.click(
                build_exam_ui,
                inputs=[],
                outputs=question_radios + [submit_row, start_exam_btn],
            )
 
            # Submit exam: collect all radio answers and score
            submit_exam_btn.click(
                score_exam,
                inputs=question_radios,
                outputs=[exam_results],
            )
 
        # ── Tab 3: Question Answering ───────────────────────────────────
        with gr.TabItem("🗨️ Question Answering"):
            user_question_input = gr.Textbox(label="Your Question", placeholder="Type a question here")
            qa_output = gr.Textbox(label="Answer", lines=8)
            qa_btn = gr.Button("Ask Question")
            qa_btn.click(
                start_qa_streaming,
                inputs=[clean_text_file_path_state, user_question_input],
                outputs=[qa_output, qa_thread_id],
            )
 
        # ── Tab 4: Summarization ────────────────────────────────────────
        with gr.TabItem("📝 Summarization"):
            summarize_output = gr.Textbox(label="Summary", lines=8)
            summarize_btn = gr.Button("Summarize Text")
            summarize_btn.click(
                start_summarization_stream,
                inputs=[clean_text_file_path_state, project_id_input],
                outputs=[summarize_output, sg_thread_id],
                queue=True,
            )
 
            sg_feedback_input = gr.Textbox(
                label="Feedback on Summary",
                placeholder="Type feedback to improve summary",
            )
            sg_continue_btn = gr.Button("Apply Summary Feedback")
            sg_continue_output = gr.Textbox(label="Updated Summary", lines=8)
            sg_continue_btn.click(
                continue_summarization_feedback_stream,
                inputs=[project_id_input, clean_text_file_path_state, sg_thread_id, sg_feedback_input],
                outputs=[sg_continue_output],
                queue=True,
            )
 
 
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,
    css=custom_css,
)
 