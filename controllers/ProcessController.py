import os
import fitz  # PyMuPDF for PDFs
import docx
import logging

logger = logging.getLogger(__name__)

# -------------------------
# Whisper model lazy loader
# -------------------------
WHISPER_MODEL = None

def get_whisper_model():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        logger.info("Loading Whisper model...")
        import whisper
        WHISPER_MODEL = whisper.load_model("base")
        logger.info("Whisper model loaded.")
    return WHISPER_MODEL


# -------------------------
# File loaders
# -------------------------
def load_txt_file(path: str) -> str:
    logger.info(f"Loading TXT file: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def load_pdf_file(path: str) -> str:
    logger.info(f"Extracting PDF: {path}")
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def load_docx_file(path: str) -> str:
    logger.info(f"Extracting DOCX: {path}")
    document = docx.Document(path)
    return "\n".join([p.text for p in document.paragraphs]).strip()

def load_audio_file(path: str) -> str:
    logger.info(f"Transcribing audio: {path}")
    model = get_whisper_model()

    import tempfile, subprocess
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    subprocess.run(
        ["ffmpeg", "-y", "-i", path, wav_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    result = model.transcribe(wav_path)
    os.remove(wav_path)

    return result.get("text", "").strip()


# =======================================================
# PROCESS CONTROLLER WITH PURE PYTHON CHUNKING
# =======================================================
class ProcessController:

    @staticmethod
    def extract_content(file_path: str) -> str:
        """Extract raw text from supported file types."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Processing file: {file_path} (ext={ext})")

        if ext == ".txt":
            return load_txt_file(file_path)
        elif ext == ".pdf":
            return load_pdf_file(file_path)
        elif ext == ".docx":
            return load_docx_file(file_path)
        elif ext in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]:
            return load_audio_file(file_path)

        raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def process_file_content(raw_text: str, file_id: str, chunk_size: int, overlap_size: int):
        """
        Pure Python chunking, no LangChain.
        Returns: list of {page_content, metadata}
        """
        logger.info("Chunking text with pure Python...")

        chunks = []
        start = 0
        text_len = len(raw_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = raw_text[start:end]

            chunks.append({
                "page_content": chunk_text,
                "metadata": {"file_id": file_id}
            })

            start += chunk_size - overlap_size

        logger.info(f"Created {len(chunks)} chunks.")
        return chunks
