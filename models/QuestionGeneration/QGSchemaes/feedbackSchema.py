from pydantic import BaseModel, Field
class Feedback(BaseModel):
    feedback: str = Field(
        description="feedback about the generated or refined question, such as accuracy, clarity, or educational value."
    )