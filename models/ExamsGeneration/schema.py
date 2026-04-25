from typing import Literal, Union, List
from pydantic import BaseModel, Field


class BulkQuestion(BaseModel):
    question: str = Field(description="The generated question based on the given context.")
    question_type: Literal["T/F", "MCQ"] = Field(
        description="The type of question. Must be either 'T/F' (True/False) or 'MCQ' (Multiple Choice Question)."
    )
    complexity: Literal["easy", "medium", "hard"] = Field(
        description="The complexity level of the question determined by the LLM."
    )
    options: Union[List[str], None] = Field(
        description="List of answer choices for MCQ as an array like ['A. ...', 'B. ...', 'C. ...', 'D. ...']. Use null for T/F questions."
    )
    answer: str = Field(
        description="The correct answer. Must be 'True' or 'False' for T/F, or a single letter like 'A', 'B', 'C', 'D' for MCQ."
    )
    explanation: str = Field(
        description="A concise explanation of why the selected answer is correct, based on the provided context."
    )


class BulkQuestionSet(BaseModel):
    questions: List[BulkQuestion] = Field(
        description="The list of generated questions."
    )