from typing import TypedDict, Literal, List, Optional

class SummaryGenState(TypedDict):
    # Input
    context: str
    depth: Literal["brief", "standard", "detailed"]   # student-controlled depth

    # Pipeline outputs
    key_terms: str          # JSON string: list of {term, definition}
    tldr: str               # 3-5 sentence quick recap
    structured_notes: str   # hierarchical headings + bullets
    paragraph_summary: str  # flowing prose

    # Feedback loop
    feedback: str
    old_output: str         # snapshot before rewrite (for diffing)
