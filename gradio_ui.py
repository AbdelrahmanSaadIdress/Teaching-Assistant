import gradio as gr
import requests
import mimetypes
import json

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
FASTAPI_BASE_URL = "http://localhost:5000/api/TA"
MAX_EXAM_QUESTIONS = 50

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
custom_css = """
body { background: linear-gradient(135deg, #0f172a, #3b0764, #6366f1); }

.gradio-container {
    max-width: 1200px !important;
    margin: auto;
    font-family: Inter, system-ui, sans-serif;
}
.block {
    background: rgba(15, 23, 42, 0.95) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid #1e293b !important;
}
h1 {
    background: linear-gradient(90deg, #6366f1, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
h3 {
    color: #22d3ee !important;
}
p {
    color: #c7d2fe;
}
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
textarea, input[type="text"] {
    background: #0f172a !important;
    color: #e5e7eb !important;
    border-radius: 12px !important;
    border: 1px solid #1e293b !important;
}
.tab-nav button { color: #c7d2fe !important; font-weight: 600; }
.tab-nav button.selected { background: #1e293b !important; border-radius: 12px; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #6366f1; border-radius: 10px; }

/* Summary section labels */
.section-label {
    font-size: 13px;
    font-weight: 700;
    color: #a5b4fc;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}

.exam-results h2 {
    color: #22d3ee;
    font-weight: 800;
}

.exam-results h3 {
    color: #a5b4fc;
}

.exam-results p {
    color: #e5e7eb;
}

.exam-results strong {
    color: #c7d2fe;
}
"""

# ──────────────────────────────────────────────────────────────────────────────
# Module-level exam state
# ──────────────────────────────────────────────────────────────────────────────
_exam_questions = []
_exam_thread_id = None

# Module-level summary thread id
_sg_thread_id = None

# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 1: File Processing ────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def upload_file_to_fastapi(file, project_id):
    if file is None or not project_id.strip():
        return "❌ Error: File and Project ID are required.", None, None
    with open(file.name, "rb") as f:
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        files = {"file": (file.name, f, mime_type)}
        data  = {"project_id": project_id}
        try:
            resp = requests.post(f"{FASTAPI_BASE_URL}/fileProcessing", files=files, data=data)
            if resp.status_code == 200:
                j = resp.json()
                return (
                    f"✅ File processed successfully!\n"
                    f"Thread ID     : {j.get('thread_id')}\n"
                    f"Uploaded File : {j.get('uploaded_file')}\n"
                    f"Extracted to  : {j.get('text_file')}",
                    j.get("thread_id"),
                    j.get("text_file"),
                )
            return f"❌ Error {resp.status_code}: {resp.text}", None, None
        except Exception as e:
            return f"❌ Exception: {e}", None, None


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 2: Question Generation (one-by-one) ───────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

_qg_active = False   # track whether a session is open

def start_question_generation(project_id, qg_thread_id, question_type, clean_text_file_path):
    global _qg_active
    # If a session is already open, close it first
    if _qg_active and qg_thread_id:
        try:
            requests.post(f"{FASTAPI_BASE_URL}/continue", json={
                "project_id": project_id,
                "thread_id": qg_thread_id,
                "user_feedback": "save",
                "question_type": question_type,
                "clean_text_file_path": clean_text_file_path,
            })
        except Exception:
            pass

    if not clean_text_file_path:
        return "❌ Please upload and process a file first.", None
    payload = {
        "project_id": project_id,
        "question_type": question_type,
        "clean_text_file_path": clean_text_file_path,
    }
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/start_session", json=payload)
        if resp.status_code == 200:
            j = resp.json()
            q = j.get("graph_response", {})
            opts = q.get("options")
            opts_str = "\n".join(opts) if isinstance(opts, list) else (opts or "—")
            _qg_active = True
            return (
                f"Question : {q.get('question')}\n\n"
                f"Options  :\n{opts_str}\n\n"
                f"{'─'*50}\n"
                f"Answer   : {q.get('answer')}\n"
                f"Explain  : {q.get('explanation')}",
                j.get("thread_id"),
            )
        return f"❌ Error {resp.status_code}: {resp.text}", None
    except Exception as e:
        return f"❌ Exception: {e}", None


def continue_question_generation(project_id, qg_thread_id, user_feedback, question_type, clean_text_file_path):
    if not qg_thread_id or not clean_text_file_path:
        return "❌ Start a session first.", None
    payload = {
        "project_id": project_id,
        "thread_id": qg_thread_id,
        "user_feedback": user_feedback,
        "question_type": question_type,
        "clean_text_file_path": clean_text_file_path,
    }
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/continue", json=payload)
        if resp.status_code == 200:
            j = resp.json()
            q = j.get("graph_response", {})
            opts = q.get("options")
            opts_str = "\n".join(opts) if isinstance(opts, list) else (opts or "—")
            return (
                f"Question : {q.get('question')}\n\n"
                f"Options  :\n{opts_str}\n\n"
                f"{'─'*50}\n"
                f"Answer   : {q.get('answer')}\n"
                f"Explain  : {q.get('explanation')}",
                j.get("thread_id"),
            )
        return f"❌ Error {resp.status_code}: {resp.text}", None
    except Exception as e:
        return f"❌ Exception: {e}", None


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 3: Bulk Question Generation / Exam ────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def _badge(level: str) -> str:
    return {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(
        level.lower(), level
    )


def _preview_questions(questions: list) -> str:
    if not questions:
        return ""
    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"── Q{i} | {_badge(q.get('complexity',''))} | {q.get('question_type','')} ──")
        lines.append(q.get("question", ""))
        for o in q.get("options") or []:
            lines.append(f"   {o}")
        lines.append("")
    return "\n".join(lines)


def start_bulk_generation(project_id, clean_text_file_path, question_type, num_questions):
    global _exam_questions, _exam_thread_id
    if not clean_text_file_path:
        return "❌ Upload a file first.", "", gr.update(visible=False), gr.update(visible=False)
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
        return (
            f"✅ {len(_exam_questions)} questions generated  |  Thread: {_exam_thread_id}",
            _preview_questions(_exam_questions),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌ Exception: {e}", "", gr.update(visible=False), gr.update(visible=False)


def apply_bulk_feedback(feedback_text):
    global _exam_questions
    if not _exam_thread_id:
        return "❌ No active session.", "", gr.update(visible=False), gr.update(visible=False)
    try:
        resp = requests.post(
            f"{FASTAPI_BASE_URL}/bulk_continue",
            json={"thread_id": _exam_thread_id, "user_feedback": feedback_text},
        )
        if resp.status_code != 200:
            return f"❌ Error {resp.status_code}: {resp.text}", "", gr.update(visible=False), gr.update(visible=False)
        data = resp.json()
        _exam_questions = data.get("questions", [])
        return (
            f"✅ Updated — {len(_exam_questions)} questions  |  Thread: {_exam_thread_id}",
            _preview_questions(_exam_questions),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌ Exception: {e}", "", gr.update(visible=False), gr.update(visible=False)


def build_exam_ui():
    updates = []
    for i in range(MAX_EXAM_QUESTIONS):
        if i < len(_exam_questions):
            q     = _exam_questions[i]
            label = f"Q{i+1}  |  {_badge(q.get('complexity',''))}  |  {q.get('question_type','')}\n\n{q['question']}"
            opts  = q.get("options") or ["True", "False"]
            updates.append(gr.update(visible=True, label=label, choices=opts, value=None))
        else:
            updates.append(gr.update(visible=False, choices=[], value=None))
    updates.append(gr.update(visible=True))   # submit_row
    updates.append(gr.update(visible=False))  # start_exam_btn
    return updates


def score_exam(*user_answers):
    if not _exam_questions:
        return "❌ No exam loaded."
    total, correct = len(_exam_questions), 0
    lines = ["# 📊 Exam Results\n"]
    for i, q in enumerate(_exam_questions):
        user_ans    = user_answers[i] if i < len(user_answers) else None
        correct_ans = q["answer"]
        qtype       = q.get("question_type", "")
        norm        = ""
        if user_ans:
            norm = user_ans.strip()
            if qtype == "MCQ" and len(norm) > 1 and norm[1] == ".":
                norm = norm[0].upper()
        is_correct = norm.upper() == correct_ans.upper() if norm else False
        if is_correct:
            correct += 1
        icon = "✅" if is_correct else "❌"
        lines.append(f"### {icon} Q{i+1}  |  {_badge(q.get('complexity',''))}  |  {qtype}")
        lines.append(f"**{q['question']}**")
        for opt in (q.get("options") or []):
            lines.append(f"- {opt}")
        lines.append(f"\n**Your answer:** {user_ans or '*(no answer)*'}")
        if not is_correct:
            lines.append(f"**Correct answer:** {correct_ans}")
        lines.append(f"**Explanation:** {q['explanation']}\n")
    pct   = round(correct / total * 100) if total else 0
    emoji = "🏆" if pct >= 90 else "👍" if pct >= 70 else "📚" if pct >= 50 else "💪"
    return f"## {emoji}  Score: {correct}/{total}  ({pct}%)\n\n" + "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 4: Question Answering ─────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def start_qa_streaming(clean_text_file_path, user_question):
    payload = {"clean_text_file_path": clean_text_file_path, "user_question": user_question}
    resp    = requests.post(f"{FASTAPI_BASE_URL}/start_QA_session", json=payload, stream=True)
    answer, thread_id = "", None
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            d = json.loads(line[6:])
            thread_id = d.get("thread_id", thread_id)
            if d.get("event") == "token":
                answer += d.get("token", "")
                yield answer, thread_id
    yield answer, thread_id


def continue_qa_streaming(clean_text_file_path, user_question, qa_thread_id):
    payload = {"user_question": user_question, "thread_id": qa_thread_id}
    resp    = requests.post(f"{FASTAPI_BASE_URL}/QA_continue", json=payload, stream=True)
    answer  = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            d = json.loads(line[6:])
            if d.get("event") == "token":
                answer += d.get("token", "")
                yield answer, qa_thread_id
    yield answer, qa_thread_id


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 5: Summarization (updated) ───────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def _parse_key_terms(raw: str) -> str:
    """Turn JSON key-terms array into a readable bullet list."""
    try:
        terms = json.loads(raw)
        lines = []
        for t in terms:
            lines.append(f"• **{t['term']}** — {t['definition']}")
        return "\n".join(lines)
    except Exception:
        return raw   # fallback: show raw if parsing fails


def start_summarization_stream(clean_text_file_path, project_id, depth):
    global _sg_thread_id
    if not clean_text_file_path:
        yield "❌ Upload a file first.", "", "", "", None
        return

    payload = {
        "clean_text_file_path": clean_text_file_path,
        "project_id": project_id,
        "depth": depth,
    }
    resp = requests.post(f"{FASTAPI_BASE_URL}/start_SG_session", json=payload, stream=True)

    key_terms_buf = tldr_buf = notes_buf = para_buf = ""
    thread_id = None

    # which buffer is currently receiving tokens
    active_section = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        d = json.loads(line[6:])
        evt = d.get("event")

        if evt == "session_start":
            thread_id   = d.get("thread_id")
            _sg_thread_id = thread_id

        elif evt == "section_start":
            active_section = d.get("section")

        elif evt == "token":
            section = d.get("section", active_section)
            token   = d.get("token", "")
            if section == "key_terms":
                key_terms_buf += token
            elif section == "tldr":
                tldr_buf += token
            elif section == "structured_notes":
                notes_buf += token
            elif section in ("paragraph_summary", "rewriter"):
                para_buf += token
            yield (
                _parse_key_terms(key_terms_buf),
                tldr_buf,
                notes_buf,
                para_buf,
                thread_id,
            )

        elif evt == "section_end":
            active_section = None

        elif evt == "interrupt":
            # Graph is waiting for feedback — yield final state
            payload_data = d.get("payload", {})
            key_terms_buf = _parse_key_terms(payload_data.get("key_terms", key_terms_buf))
            tldr_buf      = payload_data.get("tldr", tldr_buf)
            notes_buf     = payload_data.get("structured_notes", notes_buf)
            para_buf      = payload_data.get("paragraph_summary", para_buf)
            yield key_terms_buf, tldr_buf, notes_buf, para_buf, thread_id

        elif evt == "stream_end":
            break

    yield key_terms_buf, tldr_buf, notes_buf, para_buf, thread_id


def continue_summarization_stream(project_id, clean_text_file_path, sg_thread_id, user_feedback):
    global _sg_thread_id
    if not sg_thread_id:
        yield "", "", "", ""
        return

    payload = {
        "project_id": project_id,
        "clean_text_file_path": clean_text_file_path,
        "thread_id": sg_thread_id,
        "user_feedback": user_feedback,
    }
    resp = requests.post(f"{FASTAPI_BASE_URL}/SG_continue", json=payload, stream=True)

    key_terms_buf = tldr_buf = notes_buf = para_buf = ""
    active_section = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        d   = json.loads(line[6:])
        evt = d.get("event")

        if evt == "section_start":
            active_section = d.get("section")

        elif evt == "token":
            section = d.get("section", active_section)
            token   = d.get("token", "")
            if section == "key_terms":
                key_terms_buf += token
            elif section == "tldr":
                tldr_buf += token
            elif section == "structured_notes":
                notes_buf += token
            elif section in ("paragraph_summary", "rewriter"):
                para_buf += token
            yield (
                _parse_key_terms(key_terms_buf),
                tldr_buf,
                notes_buf,
                para_buf,
            )

        elif evt == "section_end":
            active_section = None

        elif evt == "interrupt":
            payload_data  = d.get("payload", {})
            key_terms_buf = _parse_key_terms(payload_data.get("key_terms", key_terms_buf))
            tldr_buf      = payload_data.get("tldr", tldr_buf)
            notes_buf     = payload_data.get("structured_notes", notes_buf)
            para_buf      = payload_data.get("paragraph_summary", para_buf)
            yield key_terms_buf, tldr_buf, notes_buf, para_buf

        elif evt == "stream_end":
            break

    yield key_terms_buf, tldr_buf, notes_buf, para_buf


# ──────────────────────────────────────────────────────────────────────────────
# Gradio Layout
# ──────────────────────────────────────────────────────────────────────────────

with gr.Blocks(css=custom_css) as demo:

    gr.Markdown("# 🧠 College Study Assistant")
    gr.Markdown(
        "<h3 style='background:linear-gradient(90deg,#6366f1,#22d3ee);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
        "Upload documents · Generate questions · Take exams · Ask questions · Summarize content"
        "</h3>"
    )

    # ── Shared state ──────────────────────────────────────────────────────────
    qg_thread_id_state         = gr.State(None)
    qa_thread_id_state         = gr.State(None)
    sg_thread_id_state         = gr.State(None)
    clean_text_file_path_state = gr.State(None)

    with gr.Tabs():

        # ─────────────────────────────────────────────────────────────────────
        # Tab 1 — File Processing
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📄 File Processing"):
            gr.Markdown("### Upload and extract your document")
            file_input      = gr.File(label="Upload File (PDF, TXT, DOCX, Audio)")
            project_id_input = gr.Textbox(label="Project ID", placeholder="e.g. bio101")
            process_btn     = gr.Button("⬆️ Upload & Process")
            process_output  = gr.Textbox(label="Status", lines=5, interactive=False)

            process_btn.click(
                upload_file_to_fastapi,
                inputs=[file_input, project_id_input],
                outputs=[process_output, qg_thread_id_state, clean_text_file_path_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 2 — Question Generation (one-by-one)
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("✏️ Question Generation"):
            gr.Markdown(
                "### Generate questions one at a time\n"
                "Provide feedback to refine, or type **`save`** to finish the session."
            )
            qg_type_input   = gr.Dropdown(["MCQ", "T/F"], label="Question Type", value="MCQ")
            qg_generate_btn = gr.Button("🎯 Generate Question")
            qg_output       = gr.Textbox(label="Generated Question", lines=10, interactive=False)

            qg_generate_btn.click(
                start_question_generation,
                inputs=[project_id_input, qg_thread_id_state, qg_type_input, clean_text_file_path_state],
                outputs=[qg_output, qg_thread_id_state],
            )

            gr.Markdown("---")
            gr.Markdown("#### 💬 Refine this question")
            with gr.Row():
                qg_feedback_input = gr.Textbox(
                    label="Feedback",
                    placeholder="Type feedback, 'auto' to auto-improve, or 'save' to end session",
                    scale=4,
                )
                qg_continue_btn = gr.Button("🔄 Apply", scale=1)
            qg_continue_output = gr.Textbox(label="Refined Question", lines=10, interactive=False)

            qg_continue_btn.click(
                continue_question_generation,
                inputs=[project_id_input, qg_thread_id_state, qg_feedback_input, qg_type_input, clean_text_file_path_state],
                outputs=[qg_continue_output, qg_thread_id_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 3 — Bulk Generation / Exam
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📝 Exam Mode"):
            gr.Markdown("### Configure and take an AI-generated exam")

            with gr.Row():
                bulk_type_input = gr.Dropdown(
                    ["MCQ", "T/F", "Both"], label="Question Type", value="MCQ", scale=1
                )
                num_q_slider = gr.Slider(
                    minimum=1, maximum=50, step=1, value=5,
                    label="Number of Questions", scale=3,
                )

            bulk_generate_btn  = gr.Button("🎲 Generate Questions", variant="primary")
            bulk_status        = gr.Textbox(label="Status", lines=1, interactive=False)
            bulk_preview       = gr.Textbox(
                label="📋 Questions Preview", lines=14, interactive=False
            )

            # Feedback section (hidden until questions are ready)
            with gr.Group(visible=False) as bulk_feedback_group:
                gr.Markdown("#### 💬 Not satisfied? Refine the questions")
                with gr.Row():
                    bulk_feedback_input = gr.Textbox(
                        label="Feedback",
                        placeholder="e.g. 'Make hard questions harder' or 'Focus on chapter 2'",
                        scale=4,
                    )
                    bulk_feedback_btn = gr.Button("🔄 Regenerate", scale=1)

            start_exam_btn = gr.Button("🚀 Start Exam", variant="primary", visible=False)

            # ── Exam questions (pre-created, shown dynamically) ─────────────
            gr.Markdown("---")
            question_radios = []
            for idx in range(MAX_EXAM_QUESTIONS):
                r = gr.Radio(choices=[], label=f"Q{idx+1}", visible=False, interactive=True)
                question_radios.append(r)

            with gr.Row(visible=False) as submit_row:
                submit_exam_btn = gr.Button("✅ Submit & See Results", variant="primary")

            exam_results = gr.Markdown(value="")

            # Callbacks
            bulk_generate_btn.click(
                start_bulk_generation,
                inputs=[project_id_input, clean_text_file_path_state, bulk_type_input, num_q_slider],
                outputs=[bulk_status, bulk_preview, bulk_feedback_group, start_exam_btn],
            )
            bulk_feedback_btn.click(
                apply_bulk_feedback,
                inputs=[bulk_feedback_input],
                outputs=[bulk_status, bulk_preview, bulk_feedback_group, start_exam_btn],
            )
            start_exam_btn.click(
                build_exam_ui,
                inputs=[],
                outputs=question_radios + [submit_row, start_exam_btn],
            )
            submit_exam_btn.click(
                score_exam,
                inputs=question_radios,
                outputs=[exam_results],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 4 — Question Answering
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("🗨️ Question Answering"):
            gr.Markdown(
                "### Ask anything about your document\n"
                "The assistant answers strictly from the uploaded content."
            )
            qa_question_input = gr.Textbox(
                label="Your Question", placeholder="Type your question here…", lines=2
            )
            qa_ask_btn  = gr.Button("🔍 Ask")
            qa_output   = gr.Textbox(label="Answer", lines=10, interactive=False)

            qa_ask_btn.click(
                start_qa_streaming,
                inputs=[clean_text_file_path_state, qa_question_input],
                outputs=[qa_output, qa_thread_id_state],
            )

            gr.Markdown("---")
            gr.Markdown("#### 💬 Ask a follow-up question")
            with gr.Row():
                qa_followup_input = gr.Textbox(
                    label="Follow-up Question",
                    placeholder="Continue the conversation…",
                    scale=4,
                )
                qa_followup_btn = gr.Button("🔍 Ask", scale=1)
            qa_followup_output = gr.Textbox(label="Follow-up Answer", lines=8, interactive=False)

            qa_followup_btn.click(
                continue_qa_streaming,
                inputs=[clean_text_file_path_state, qa_followup_input, qa_thread_id_state],
                outputs=[qa_followup_output, qa_thread_id_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 5 — Summarization (updated)
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📚 Summarization"):
            gr.Markdown("### Generate a professional, student-friendly summary")

            with gr.Row():
                depth_selector = gr.Radio(
                    ["brief", "standard", "detailed"],
                    value="standard",
                    label="📏 Summary Depth",
                    info="Brief = essentials only  |  Standard = balanced  |  Detailed = full coverage",
                )
                summarize_btn = gr.Button("✨ Generate Summary", variant="primary", scale=1)

            # ── Four output panels ─────────────────────────────────────────
            with gr.Row():
                sg_tldr_output = gr.Textbox(
                    label="⚡ Quick Recap (TL;DR)",
                    lines=4,
                    interactive=False,
                    placeholder="Your quick recap will appear here…",
                )

            with gr.Row():
                sg_terms_output = gr.Textbox(
                    label="🔑 Key Terms & Definitions",
                    lines=10,
                    interactive=False,
                    placeholder="Key terms will appear here…",
                )

            with gr.Row():
                sg_notes_output = gr.Textbox(
                    label="📋 Structured Notes",
                    lines=16,
                    interactive=False,
                    placeholder="Structured notes will appear here…",
                )

            with gr.Row():
                sg_para_output = gr.Textbox(
                    label="📖 Paragraph Summary (Study Guide)",
                    lines=14,
                    interactive=False,
                    placeholder="Paragraph summary will appear here…",
                )

            summarize_btn.click(
                start_summarization_stream,
                inputs=[clean_text_file_path_state, project_id_input, depth_selector],
                outputs=[sg_terms_output, sg_tldr_output, sg_notes_output, sg_para_output, sg_thread_id_state],
                queue=True,
            )

            # ── Feedback & refinement ──────────────────────────────────────
            gr.Markdown("---")
            gr.Markdown(
                "#### 💬 Refine your summary\n"
                "Type specific feedback (e.g. *'Add more examples to the notes'*) "
                "or **`auto`** to auto-improve, **`save`** to finish."
            )
            with gr.Row():
                sg_feedback_input = gr.Textbox(
                    label="Feedback",
                    placeholder="Your feedback here… or type 'auto' / 'save'",
                    lines=2,
                    scale=4,
                )
                sg_continue_btn = gr.Button("🔄 Apply Feedback", scale=1)

            sg_continue_btn.click(
                continue_summarization_stream,
                inputs=[project_id_input, clean_text_file_path_state, sg_thread_id_state, sg_feedback_input],
                outputs=[sg_terms_output, sg_tldr_output, sg_notes_output, sg_para_output],
                queue=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,
    css=custom_css,
)