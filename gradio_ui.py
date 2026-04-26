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
# CSS — Dark premium theme with glassy cards and gradient accents
# ──────────────────────────────────────────────────────────────────────────────
custom_css = """
/* ── Global Reset & Base ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    background: #070b14 !important;
    color: #e2e8f0 !important;
    min-height: 100vh;
}

.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    padding: 24px 16px 48px !important;
}

/* ── Hero Header ─────────────────────────────────────────────────────────── */
.hero-header {
    text-align: center;
    padding: 48px 24px 32px;
    position: relative;
}

.hero-header::before {
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 600px; height: 300px;
    background: radial-gradient(ellipse at center, rgba(99,102,241,0.18) 0%, transparent 70%);
    pointer-events: none;
}

/* ── Panels & Cards ──────────────────────────────────────────────────────── */
.block, .gr-block, .gr-form, .gr-box {
    background: rgba(15, 20, 35, 0.85) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
}

/* ── Tab Navigation ──────────────────────────────────────────────────────── */
.tab-nav {
    background: rgba(10, 14, 26, 0.9) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 14px !important;
    padding: 6px !important;
    gap: 4px !important;
    display: flex !important;
    margin-bottom: 20px !important;
}

.tab-nav button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 18px !important;
    transition: all 0.25s ease !important;
    flex: 1 !important;
    white-space: nowrap !important;
}

.tab-nav button:hover {
    background: rgba(99,102,241,0.12) !important;
    color: #c7d2fe !important;
    transform: none !important;
    box-shadow: none !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.3)) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
button.gr-button, .gr-button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 11px 22px !important;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
    cursor: pointer !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.25) !important;
}

button.gr-button:hover, .gr-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.45) !important;
    background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
}

button.gr-button:active {
    transform: translateY(0) !important;
}

button.gr-button.secondary {
    background: rgba(99,102,241,0.12) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    color: #a5b4fc !important;
    box-shadow: none !important;
}

button.gr-button.secondary:hover {
    background: rgba(99,102,241,0.22) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.2) !important;
}

/* ── Inputs & Textareas ──────────────────────────────────────────────────── */
input[type="text"], textarea, .gr-text-input, .gr-textarea {
    background: rgba(8, 12, 24, 0.9) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    padding: 10px 14px !important;
}

input[type="text"]:focus, textarea:focus {
    border-color: rgba(99,102,241,0.55) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
    outline: none !important;
}

input[type="text"]::placeholder, textarea::placeholder {
    color: #475569 !important;
}

/* ── Labels ──────────────────────────────────────────────────────────────── */
label, .gr-block-label, span.svelte-1gfkn6j {
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin-bottom: 6px !important;
}

/* ── Markdown & Typography ───────────────────────────────────────────────── */
.gr-markdown h1 {
    font-size: 38px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 35%, #38bdf8 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.02em !important;
    line-height: 1.15 !important;
    margin-bottom: 8px !important;
}

.gr-markdown h3 {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-bottom: 12px !important;
}

.gr-markdown h2 {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
}

.gr-markdown h4, .gr-markdown h5, .gr-markdown h6 {
    color: #e2e8f0 !important;
}

/* Summary panel rendered markdown */
.summary-md-panel {
    background: rgba(6, 10, 20, 0.97) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    min-height: 80px !important;
}

.summary-md-panel p,
.summary-md-panel li,
.summary-md-panel span {
    color: #e2e8f0 !important;
    font-size: 14px !important;
    line-height: 1.75 !important;
}

.summary-md-panel h2 {
    color: #ffffff !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    margin: 18px 0 8px !important;
    padding-bottom: 6px !important;
    border-bottom: 1px solid rgba(99,102,241,0.2) !important;
}

.summary-md-panel h3 {
    color: #a5b4fc !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 14px 0 6px !important;
}

.summary-md-panel strong {
    color: #ffffff !important;
    font-weight: 700 !important;
}

.summary-md-panel ul, .summary-md-panel ol {
    padding-left: 20px !important;
    margin: 6px 0 !important;
}

.summary-md-panel li {
    margin: 4px 0 !important;
}

.summary-md-panel code {
    background: rgba(99,102,241,0.18) !important;
    color: #c7d2fe !important;
    padding: 1px 6px !important;
    border-radius: 4px !important;
    font-size: 13px !important;
}

/* Key terms panel */
.keyterms-panel {
    background: rgba(6, 10, 20, 0.97) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    min-height: 80px !important;
}

.keyterms-panel p,
.keyterms-panel li,
.keyterms-panel span {
    color: #e2e8f0 !important;
    font-size: 14px !important;
    line-height: 1.8 !important;
}

.keyterms-panel strong {
    color: #38bdf8 !important;
    font-weight: 700 !important;
}

/* TLDR panel */
.tldr-panel {
    background: rgba(6, 10, 20, 0.97) !important;
    border: 1px solid rgba(52, 211, 153, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    min-height: 60px !important;
}

.tldr-panel p,
.tldr-panel span {
    color: #d1fae5 !important;
    font-size: 15px !important;
    line-height: 1.8 !important;
}

.gr-markdown p {
    color: #94a3b8 !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
}

.gr-markdown strong {
    color: #c7d2fe !important;
}

/* ── Status / Output boxes ───────────────────────────────────────────────── */
.output-box textarea {
    background: rgba(6, 10, 20, 0.95) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(51, 65, 85, 0.6) !important;
    font-size: 13.5px !important;
    line-height: 1.7 !important;
}

/* ── Dropdowns ───────────────────────────────────────────────────────────── */
.gr-dropdown select, select {
    background: rgba(8, 12, 24, 0.9) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
}

/* ── Sliders ─────────────────────────────────────────────────────────────── */
input[type="range"] {
    accent-color: #6366f1 !important;
}

/* ── File Upload ─────────────────────────────────────────────────────────── */
.gr-file-upload, .upload-container {
    background: rgba(8, 12, 24, 0.7) !important;
    border: 2px dashed rgba(99,102,241,0.3) !important;
    border-radius: 14px !important;
    transition: border-color 0.2s ease !important;
}

.gr-file-upload:hover {
    border-color: rgba(99,102,241,0.6) !important;
}

/* ── Radio Buttons ───────────────────────────────────────────────────────── */
.gr-radio {
    background: rgba(15, 20, 35, 0.7) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 4px 0 !important;
    transition: all 0.2s ease !important;
}

.gr-radio:hover {
    border-color: rgba(99,102,241,0.4) !important;
    background: rgba(99,102,241,0.07) !important;
}

input[type="radio"]:checked + label {
    color: #a5b4fc !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.65); }

/* ── Status Badge ────────────────────────────────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #a5b4fc;
}

/* ── Exam Results Panel ──────────────────────────────────────────────────── */
.exam-results-box {
    background: rgba(6, 10, 20, 0.97) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 14px !important;
    padding: 20px !important;
    font-family: "Inter", sans-serif !important;
}

/* Force ALL text inside exam results to white */
.exam-results-box *,
.exam-results-box p,
.exam-results-box li,
.exam-results-box span,
.exam-results-box div {
    color: #f1f5f9 !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}

.exam-results-box h2 {
    font-size: 24px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin-bottom: 6px !important;
}

.exam-results-box h3 {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 24px 0 10px !important;
    padding: 10px 16px !important;
    background: rgba(99,102,241,0.15) !important;
    border-left: 4px solid #6366f1 !important;
    border-radius: 0 10px 10px 0 !important;
    display: block !important;
}

.exam-results-box strong {
    color: #ffffff !important;
    font-weight: 700 !important;
}

.exam-results-box em {
    color: #94a3b8 !important;
    font-style: italic !important;
}

.exam-results-box code {
    background: rgba(99,102,241,0.2) !important;
    color: #e2e8f0 !important;
    padding: 2px 8px !important;
    border-radius: 5px !important;
    font-family: monospace !important;
    font-size: 13px !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
}

.exam-results-box ul {
    padding-left: 12px !important;
    margin: 8px 0 !important;
}

.exam-results-box li {
    color: #f1f5f9 !important;
    font-size: 14px !important;
    margin: 5px 0 !important;
    list-style: none !important;
    padding-left: 4px !important;
}

/* Explanation blockquote — amber tint */
.exam-results-box blockquote {
    border-left: 3px solid rgba(251,191,36,0.6) !important;
    background: rgba(251,191,36,0.06) !important;
    margin: 12px 0 !important;
    padding: 10px 16px !important;
    border-radius: 0 8px 8px 0 !important;
}

.exam-results-box blockquote *,
.exam-results-box blockquote p {
    color: #fde68a !important;
    font-size: 13.5px !important;
}

/* ── Section Dividers ────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(99,102,241,0.15) !important;
    margin: 20px 0 !important;
}

/* ── Accordion ───────────────────────────────────────────────────────────── */
.gr-accordion {
    background: rgba(15, 20, 35, 0.6) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 12px !important;
}

/* ── Row gaps ────────────────────────────────────────────────────────────── */
.gr-row { gap: 12px !important; }

/* ── Info text ───────────────────────────────────────────────────────────── */
.gr-info {
    color: #64748b !important;
    font-size: 12px !important;
}

/* ── Tooltip ─────────────────────────────────────────────────────────────── */
.gr-tooltip {
    background: #1e293b !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Highlight box for summary panels ───────────────────────────────────── */
.summary-panel textarea {
    background: rgba(6, 10, 20, 0.97) !important;
    border-color: rgba(56, 189, 248, 0.2) !important;
}

/* ── Q&A panel ───────────────────────────────────────────────────────────── */
.qa-answer textarea {
    background: rgba(6, 10, 20, 0.97) !important;
    border-color: rgba(52, 211, 153, 0.2) !important;
    color: #d1fae5 !important;
}

/* ── Bulk preview ────────────────────────────────────────────────────────── */
.bulk-preview textarea {
    background: rgba(6, 10, 20, 0.97) !important;
    border-color: rgba(251, 191, 36, 0.2) !important;
    font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace !important;
    font-size: 12.5px !important;
}
"""

# ──────────────────────────────────────────────────────────────────────────────
# Module-level state
# ──────────────────────────────────────────────────────────────────────────────
_exam_questions = []
_exam_thread_id = None
_sg_thread_id   = None
_qg_active      = False

# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 1: File Processing ────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def upload_file_to_fastapi(file, project_id):
    if file is None or not project_id.strip():
        return "❌  File and Project ID are required.", None, None
    with open(file.name, "rb") as f:
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        files = {"file": (file.name, f, mime_type)}
        data  = {"project_id": project_id}
        try:
            resp = requests.post(f"{FASTAPI_BASE_URL}/fileProcessing", files=files, data=data)
            if resp.status_code == 200:
                j = resp.json()
                out = (
                    f"✅  File processed successfully!\n\n"
                    f"  Thread ID     →  {j.get('thread_id')}\n"
                    f"  Uploaded File →  {j.get('uploaded_file')}\n"
                    f"  Extracted to  →  {j.get('text_file')}\n\n"
                    f"  The document has been parsed and saved as clean text.\n"
                    f"  You can now use any feature below."
                )
                return out, j.get("thread_id"), j.get("text_file")
            return f"❌  Error {resp.status_code}: {resp.text}", None, None
        except Exception as e:
            return f"❌  Exception: {e}", None, None


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 2: Question Generation ────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def start_question_generation(project_id, qg_thread_id, question_type, clean_text_file_path):
    global _qg_active
    if _qg_active and qg_thread_id:
        try:
            requests.post(f"{FASTAPI_BASE_URL}/continue", json={
                "project_id": project_id, "thread_id": qg_thread_id,
                "user_feedback": "save", "question_type": question_type,
                "clean_text_file_path": clean_text_file_path,
            })
        except Exception:
            pass

    if not clean_text_file_path:
        return "❌  Please upload and process a file first.", None

    payload = {"project_id": project_id, "question_type": question_type,
               "clean_text_file_path": clean_text_file_path}
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/start_session", json=payload)
        if resp.status_code == 200:
            j = resp.json()
            q = j.get("graph_response", {})
            opts = q.get("options")
            opts_str = "\n".join(f"  {o}" for o in opts) if isinstance(opts, list) else (opts or "—")
            _qg_active = True
            return (
                f"❓  {q.get('question')}\n\n"
                f"{'─'*52}\n\n"
                f"{opts_str}\n\n"
                f"{'─'*52}\n\n"
                f"✅  Correct Answer:  {q.get('answer')}\n\n"
                f"💡  Explanation:  {q.get('explanation')}",
                j.get("thread_id"),
            )
        return f"❌  Error {resp.status_code}: {resp.text}", None
    except Exception as e:
        return f"❌  Exception: {e}", None


def continue_question_generation(project_id, qg_thread_id, user_feedback, question_type, clean_text_file_path):
    if not qg_thread_id or not clean_text_file_path:
        return "❌  Start a session first.", None
    payload = {"project_id": project_id, "thread_id": qg_thread_id,
               "user_feedback": user_feedback, "question_type": question_type,
               "clean_text_file_path": clean_text_file_path}
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/continue", json=payload)
        if resp.status_code == 200:
            j = resp.json()
            q = j.get("graph_response", {})
            opts = q.get("options")
            opts_str = "\n".join(f"  {o}" for o in opts) if isinstance(opts, list) else (opts or "—")
            return (
                f"❓  {q.get('question')}\n\n"
                f"{'─'*52}\n\n"
                f"{opts_str}\n\n"
                f"{'─'*52}\n\n"
                f"✅  Correct Answer:  {q.get('answer')}\n\n"
                f"💡  Explanation:  {q.get('explanation')}",
                j.get("thread_id"),
            )
        return f"❌  Error {resp.status_code}: {resp.text}", None
    except Exception as e:
        return f"❌  Exception: {e}", None


# ──────────────────────────────────────────────────────────────────────────────
# ── Tab 3: Bulk / Exam Mode ───────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def _badge(level: str) -> str:
    return {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(level.lower(), level)


def _preview_questions(questions: list) -> str:
    if not questions:
        return ""
    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"── Q{i}  {_badge(q.get('complexity',''))}  ·  {q.get('question_type','')} ──")
        lines.append(f"   {q.get('question', '')}")
        for o in q.get("options") or []:
            lines.append(f"   {o}")
        lines.append("")
    return "\n".join(lines)


def start_bulk_generation(project_id, clean_text_file_path, question_type, num_questions):
    global _exam_questions, _exam_thread_id
    if not clean_text_file_path:
        return "❌  Upload a file first.", "", gr.update(visible=False), gr.update(visible=False)
    payload = {"project_id": project_id, "question_type": question_type,
               "num_questions": int(num_questions), "clean_text_file_path": clean_text_file_path}
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/start_bulk_session", json=payload)
        if resp.status_code != 200:
            return f"❌  Error {resp.status_code}: {resp.text}", "", gr.update(visible=False), gr.update(visible=False)
        data = resp.json()
        _exam_questions = data.get("questions", [])
        _exam_thread_id = data.get("thread_id")
        return (
            f"✅  {len(_exam_questions)} questions generated  ·  Thread: {_exam_thread_id}",
            _preview_questions(_exam_questions),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌  Exception: {e}", "", gr.update(visible=False), gr.update(visible=False)


def apply_bulk_feedback(feedback_text):
    global _exam_questions
    if not _exam_thread_id:
        return "❌  No active session.", "", gr.update(visible=False), gr.update(visible=False)
    try:
        resp = requests.post(f"{FASTAPI_BASE_URL}/bulk_continue",
                             json={"thread_id": _exam_thread_id, "user_feedback": feedback_text})
        if resp.status_code != 200:
            return f"❌  Error {resp.status_code}: {resp.text}", "", gr.update(visible=False), gr.update(visible=False)
        data = resp.json()
        _exam_questions = data.get("questions", [])
        return (
            f"✅  Updated — {len(_exam_questions)} questions  ·  Thread: {_exam_thread_id}",
            _preview_questions(_exam_questions),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌  Exception: {e}", "", gr.update(visible=False), gr.update(visible=False)


def build_exam_ui():
    updates = []
    for i in range(MAX_EXAM_QUESTIONS):
        if i < len(_exam_questions):
            q     = _exam_questions[i]
            label = f"Q{i+1}  ·  {_badge(q.get('complexity',''))}  ·  {q.get('question_type','')}\n\n{q['question']}"
            opts  = q.get("options") or ["True", "False"]
            updates.append(gr.update(visible=True, label=label, choices=opts, value=None))
        else:
            updates.append(gr.update(visible=False, choices=[], value=None))
    updates.append(gr.update(visible=True))
    updates.append(gr.update(visible=False))
    return updates


def score_exam(*user_answers):
    if not _exam_questions:
        return "❌  No exam loaded."
    total, correct = len(_exam_questions), 0
    lines = ["## 📊 Exam Results\n"]
    for i, q in enumerate(_exam_questions):
        user_ans    = user_answers[i] if i < len(user_answers) else None
        correct_ans = q["answer"]
        qtype       = q.get("question_type", "")
        norm = ""
        if user_ans:
            norm = user_ans.strip()
            if qtype == "MCQ" and len(norm) > 1 and norm[1] == ".":
                norm = norm[0].upper()
        is_correct = norm.upper() == correct_ans.upper() if norm else False
        if is_correct:
            correct += 1
        icon = "✅" if is_correct else "❌"
        lines.append(f"### {icon} Q{i+1}  ·  {_badge(q.get('complexity',''))}  ·  {qtype}")
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
# ── Tab 5: Summarization ──────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def _parse_key_terms(raw: str) -> str:
    """Convert JSON key-terms array into clean readable markdown."""
    try:
        # Strip any partial/incomplete JSON gracefully
        text = raw.strip()
        if not text or text == "[":
            return ""
        # Close incomplete JSON array for streaming
        if text.endswith(","):
            text = text[:-1]
        if not text.endswith("]"):
            text += "]"
        terms = json.loads(text)
        lines = []
        for t in terms:
            if isinstance(t, dict) and "term" in t and "definition" in t:
                lines.append(f"**{t['term']}**  \n{t['definition']}\n")
        return "\n---\n".join(lines) if lines else raw
    except Exception:
        # Return raw text as-is if JSON parse fails (still streaming)
        return raw


def start_summarization_stream(clean_text_file_path, project_id, depth):
    global _sg_thread_id
    if not clean_text_file_path:
        yield "❌  Upload a file first.", "", "", "", None
        return

    payload = {"clean_text_file_path": clean_text_file_path, "project_id": project_id, "depth": depth}
    resp = requests.post(f"{FASTAPI_BASE_URL}/start_SG_session", json=payload, stream=True)
    key_terms_buf = tldr_buf = notes_buf = para_buf = ""
    thread_id = None
    active_section = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        d = json.loads(line[6:])
        evt = d.get("event")

        if evt == "session_start":
            thread_id = d.get("thread_id")
            _sg_thread_id = thread_id
        elif evt == "section_start":
            active_section = d.get("section")
        elif evt == "token":
            section = d.get("section", active_section)
            token   = d.get("token", "")
            if section == "key_terms":         key_terms_buf += token
            elif section == "tldr":            tldr_buf += token
            elif section == "structured_notes": notes_buf += token
            elif section in ("paragraph_summary", "rewriter"): para_buf += token
            yield _parse_key_terms(key_terms_buf), tldr_buf, notes_buf, para_buf, thread_id
        elif evt == "section_end":
            active_section = None
        elif evt == "interrupt":
            pd = d.get("payload", {})
            key_terms_buf = _parse_key_terms(pd.get("key_terms", key_terms_buf))
            tldr_buf      = pd.get("tldr", tldr_buf)
            notes_buf     = pd.get("structured_notes", notes_buf)
            para_buf      = pd.get("paragraph_summary", para_buf)
            yield key_terms_buf, tldr_buf, notes_buf, para_buf, thread_id
        elif evt == "stream_end":
            break

    yield key_terms_buf, tldr_buf, notes_buf, para_buf, thread_id


def continue_summarization_stream(project_id, clean_text_file_path, sg_thread_id, user_feedback):
    global _sg_thread_id
    if not sg_thread_id:
        yield "", "", "", ""
        return

    payload = {"project_id": project_id, "clean_text_file_path": clean_text_file_path,
               "thread_id": sg_thread_id, "user_feedback": user_feedback}
    resp = requests.post(f"{FASTAPI_BASE_URL}/SG_continue", json=payload, stream=True)
    key_terms_buf = tldr_buf = notes_buf = para_buf = ""
    active_section = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        d   = json.loads(line[6:])
        evt = d.get("event")
        if evt == "section_start":    active_section = d.get("section")
        elif evt == "token":
            section = d.get("section", active_section)
            token   = d.get("token", "")
            if section == "key_terms":         key_terms_buf += token
            elif section == "tldr":            tldr_buf += token
            elif section == "structured_notes": notes_buf += token
            elif section in ("paragraph_summary", "rewriter"): para_buf += token
            yield _parse_key_terms(key_terms_buf), tldr_buf, notes_buf, para_buf
        elif evt == "section_end":    active_section = None
        elif evt == "interrupt":
            pd = d.get("payload", {})
            key_terms_buf = _parse_key_terms(pd.get("key_terms", key_terms_buf))
            tldr_buf      = pd.get("tldr", tldr_buf)
            notes_buf     = pd.get("structured_notes", notes_buf)
            para_buf      = pd.get("paragraph_summary", para_buf)
            yield key_terms_buf, tldr_buf, notes_buf, para_buf
        elif evt == "stream_end":
            break

    yield key_terms_buf, tldr_buf, notes_buf, para_buf


# ──────────────────────────────────────────────────────────────────────────────
# Gradio Layout
# ──────────────────────────────────────────────────────────────────────────────

with gr.Blocks(css=custom_css, title="StudyAI — College Study Assistant") as demo:

    # ── Hero ──────────────────────────────────────────────────────────────────
    gr.Markdown("""
# 🧠 StudyAI
""")
    gr.HTML("""
<div style="text-align:center;margin:-12px 0 8px;">
  <p style="font-size:18px;font-weight:600;color:#94a3b8;margin:0 0 8px;">
    Your AI-powered academic companion — upload once, learn smarter.
  </p>
  <p style="font-size:13px;color:#475569;margin:0 0 20px;">
    Upload any document &nbsp;·&nbsp; Generate exam questions &nbsp;·&nbsp;
    Take AI-built exams &nbsp;·&nbsp; Ask questions &nbsp;·&nbsp; Get instant summaries
  </p>
</div>
""")

    # ── Shared state ──────────────────────────────────────────────────────────
    qg_thread_id_state         = gr.State(None)
    qa_thread_id_state         = gr.State(None)
    sg_thread_id_state         = gr.State(None)
    clean_text_file_path_state = gr.State(None)

    with gr.Tabs():

        # ─────────────────────────────────────────────────────────────────────
        # Tab 1 — File Processing
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📄  Document Upload"):
            gr.HTML("<h3 style='font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;'>Upload your document</h3>")
            gr.Markdown("<p>Supported formats: <strong>PDF, TXT, DOCX, MP3, WAV</strong>. Max size per your `.env` config.</p>")

            with gr.Row():
                with gr.Column(scale=3):
                    file_input = gr.File(
                        label="Drop your file here or click to browse",
                        file_types=[".pdf", ".txt", ".docx", ".mp3", ".wav", ".m4a"]
                    )
                with gr.Column(scale=2):
                    project_id_input = gr.Textbox(
                        label="Project ID",
                        placeholder="e.g.  biology-101  or  nlp-lecture-3",
                        info="Used to organise your files — choose any unique name."
                    )
                    process_btn = gr.Button("⬆️  Upload & Process", variant="primary")

            process_output = gr.Textbox(
                label="Processing Status",
                lines=6,
                interactive=False,
                elem_classes=["output-box"]
            )

            process_btn.click(
                upload_file_to_fastapi,
                inputs=[file_input, project_id_input],
                outputs=[process_output, qg_thread_id_state, clean_text_file_path_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 2 — Question Generation
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("✏️  Question Gen"):
            gr.HTML("<h3 style='font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;'>Iterative Question Generation</h3>")
            gr.Markdown(
                "<p>Generate one question at a time from your document. "
                "Provide feedback to refine it, type <strong>auto</strong> for AI self-improvement, "
                "or <strong>save</strong> to finish the session.</p>"
            )

            with gr.Row():
                qg_type_input = gr.Dropdown(
                    ["MCQ", "T/F"],
                    label="Question Type",
                    value="MCQ",
                    scale=1
                )
                qg_generate_btn = gr.Button("🎯  Generate Question", variant="primary", scale=2)

            qg_output = gr.Textbox(
                label="Generated Question",
                lines=11,
                interactive=False,
                elem_classes=["output-box"]
            )

            qg_generate_btn.click(
                start_question_generation,
                inputs=[project_id_input, qg_thread_id_state, qg_type_input, clean_text_file_path_state],
                outputs=[qg_output, qg_thread_id_state],
            )

            gr.Markdown("---")
            gr.HTML("<h4 style='font-size:15px;font-weight:600;color:#c7d2fe;margin:16px 0 8px;'>💬  Refine this question</h4>")

            with gr.Row():
                qg_feedback_input = gr.Textbox(
                    label="Feedback",
                    placeholder="Type your feedback, 'auto' to auto-improve, or 'save' to end session",
                    scale=4,
                )
                qg_continue_btn = gr.Button("🔄  Apply", variant="secondary", scale=1)

            qg_continue_output = gr.Textbox(
                label="Refined Question",
                lines=11,
                interactive=False,
                elem_classes=["output-box"]
            )

            qg_continue_btn.click(
                continue_question_generation,
                inputs=[project_id_input, qg_thread_id_state, qg_feedback_input,
                        qg_type_input, clean_text_file_path_state],
                outputs=[qg_continue_output, qg_thread_id_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 3 — Exam Mode
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📝  Exam Mode"):
            gr.HTML("<h3 style='font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;'>AI-Generated Exam</h3>")
            gr.Markdown(
                "<p>Configure your exam, generate questions, give feedback to refine them, "
                "then take the full exam and get a detailed score breakdown.</p>"
            )

            with gr.Row():
                bulk_type_input = gr.Dropdown(
                    ["MCQ", "T/F", "Both"],
                    label="Question Type",
                    value="MCQ",
                    scale=1
                )
                num_q_slider = gr.Slider(
                    minimum=1, maximum=50, step=1, value=5,
                    label="Number of Questions",
                    scale=3
                )

            bulk_generate_btn = gr.Button("🎲  Generate Questions", variant="primary")

            with gr.Row():
                bulk_status = gr.Textbox(
                    label="Status",
                    lines=1,
                    interactive=False,
                    elem_classes=["output-box"],
                    scale=2
                )

            bulk_preview = gr.Textbox(
                label="📋  Questions Preview",
                lines=14,
                interactive=False,
                elem_classes=["output-box", "bulk-preview"]
            )

            with gr.Group(visible=False) as bulk_feedback_group:
                gr.HTML("<h4 style='font-size:15px;font-weight:600;color:#c7d2fe;margin:16px 0 8px;'>💬  Refine the questions</h4>")
                with gr.Row():
                    bulk_feedback_input = gr.Textbox(
                        label="Feedback",
                        placeholder="e.g.  'Make hard questions harder'  or  'Focus more on chapter 2'",
                        scale=4,
                    )
                    bulk_feedback_btn = gr.Button("🔄  Regenerate", variant="secondary", scale=1)

            gr.Markdown("---")
            start_exam_btn = gr.Button("🚀  Start Exam", variant="primary", visible=False)

            question_radios = []
            for idx in range(MAX_EXAM_QUESTIONS):
                r = gr.Radio(choices=[], label=f"Q{idx+1}", visible=False, interactive=True)
                question_radios.append(r)

            with gr.Row(visible=False) as submit_row:
                submit_exam_btn = gr.Button("✅  Submit & See Results", variant="primary")

            exam_results = gr.Markdown(value="", elem_classes=["exam-results-box"])

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
        with gr.TabItem("🗨️  Q&A"):
            gr.HTML("<h3 style='font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;'>Document Question Answering</h3>")
            gr.Markdown(
                "<p>Ask anything about your uploaded document. "
                "The model answers <strong>strictly from the document content</strong> — "
                "off-topic questions are gracefully rejected.</p>"
            )

            qa_question_input = gr.Textbox(
                label="Your Question",
                placeholder="What does the document say about …?",
                lines=2,
            )
            qa_ask_btn = gr.Button("🔍  Ask", variant="primary")
            qa_output  = gr.Textbox(
                label="Answer",
                lines=10,
                interactive=False,
                elem_classes=["output-box", "qa-answer"]
            )

            qa_ask_btn.click(
                start_qa_streaming,
                inputs=[clean_text_file_path_state, qa_question_input],
                outputs=[qa_output, qa_thread_id_state],
            )

            gr.Markdown("---")
            gr.HTML("<h4 style='font-size:15px;font-weight:600;color:#c7d2fe;margin:16px 0 8px;'>💬  Follow-up questions</h4>")
            with gr.Row():
                qa_followup_input = gr.Textbox(
                    label="Follow-up",
                    placeholder="Continue the conversation …",
                    scale=4,
                )
                qa_followup_btn = gr.Button("🔍  Ask", variant="secondary", scale=1)

            qa_followup_output = gr.Textbox(
                label="Follow-up Answer",
                lines=8,
                interactive=False,
                elem_classes=["output-box", "qa-answer"]
            )

            qa_followup_btn.click(
                continue_qa_streaming,
                inputs=[clean_text_file_path_state, qa_followup_input, qa_thread_id_state],
                outputs=[qa_followup_output, qa_thread_id_state],
            )

        # ─────────────────────────────────────────────────────────────────────
        # Tab 5 — Summarization
        # ─────────────────────────────────────────────────────────────────────
        with gr.TabItem("📚  Summarize"):
            gr.HTML("<h3 style='font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;'>AI Study Summary Generator</h3>")
            gr.Markdown(
                "<p>Generates four complementary study artefacts in one pass: "
                "<strong>Key Terms, Quick Recap, Structured Notes,</strong> and a "
                "<strong>Paragraph Study Guide</strong>. Control depth below.</p>"
            )

            with gr.Row():
                depth_selector = gr.Radio(
                    ["brief", "standard", "detailed"],
                    value="standard",
                    label="Summary Depth",
                    info="brief = essentials only  ·  standard = balanced  ·  detailed = full coverage",
                    scale=3,
                )
                summarize_btn = gr.Button("✨  Generate Summary", variant="primary", scale=1)

            gr.Markdown("<p style='color:#64748b;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 6px;'>⚡ Quick Recap (TL;DR)</p>")
            sg_tldr_output = gr.Markdown(
                value="<p style='color:#475569;font-style:italic;'>Quick recap will appear here after generation…</p>",
                elem_classes=["tldr-panel"],
            )

            gr.Markdown("<p style='color:#64748b;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 6px;'>🔑 Key Terms & Definitions</p>")
            sg_terms_output = gr.Markdown(
                value="<p style='color:#475569;font-style:italic;'>Key terms will appear here after generation…</p>",
                elem_classes=["keyterms-panel"],
            )

            gr.Markdown("<p style='color:#64748b;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 6px;'>📋 Structured Notes</p>")
            sg_notes_output = gr.Markdown(
                value="<p style='color:#475569;font-style:italic;'>Structured notes will appear here after generation…</p>",
                elem_classes=["summary-md-panel"],
            )

            gr.Markdown("<p style='color:#64748b;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 6px;'>📖 Paragraph Summary — Study Guide</p>")
            sg_para_output = gr.Markdown(
                value="<p style='color:#475569;font-style:italic;'>Paragraph summary will appear here after generation…</p>",
                elem_classes=["summary-md-panel"],
            )

            summarize_btn.click(
                start_summarization_stream,
                inputs=[clean_text_file_path_state, project_id_input, depth_selector],
                outputs=[sg_terms_output, sg_tldr_output, sg_notes_output,
                         sg_para_output, sg_thread_id_state],
                queue=True,
            )

            gr.Markdown("---")
            gr.Markdown(
                "#### 💬  Refine your summary\n"
                "Give specific feedback, type **`auto`** to auto-improve, or **`save`** to finish."
            )
            with gr.Row():
                sg_feedback_input = gr.Textbox(
                    label="Feedback",
                    placeholder="e.g.  'Add more examples to the structured notes'  or  'auto'",
                    lines=2,
                    scale=4,
                )
                sg_continue_btn = gr.Button("🔄  Apply Feedback", variant="secondary", scale=1)

            sg_continue_btn.click(
                continue_summarization_stream,
                inputs=[project_id_input, clean_text_file_path_state,
                        sg_thread_id_state, sg_feedback_input],
                outputs=[sg_terms_output, sg_tldr_output, sg_notes_output, sg_para_output],
                queue=True,
            )

    # ── Footer ────────────────────────────────────────────────────────────────
    gr.Markdown(
        "<p style='text-align:center;color:#334155;font-size:12px;margin-top:32px;'>"
        "StudyAI  ·  Powered by LangGraph · FastAPI · Gradio"
        "</p>"
    )


# ──────────────────────────────────────────────────────────────────────────────
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,
)