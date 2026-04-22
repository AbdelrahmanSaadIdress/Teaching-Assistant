from pydantic import BaseModel, Field

class GradeQuestion(BaseModel):
    """Represents the grading information for a question."""

    score: str = Field(
        description="The score assigned to the question based on its relevance and quality. Must be 'Yes' or 'No'."
    )