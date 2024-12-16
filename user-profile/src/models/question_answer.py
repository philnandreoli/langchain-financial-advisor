from pydantic import BaseModel, Field

class QuestionAnswer(BaseModel):
    question: int = Field(..., title="Question Number", description="The number of the question that was answered")
    answer: str = Field (..., title="Answer", description="The answer to the question that was asked")