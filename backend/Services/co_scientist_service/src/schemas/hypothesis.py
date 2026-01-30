from pydantic import BaseModel


class Hypothesis(BaseModel):
    background: str
    hypothesis: str
    mechanisms: str
    expected_outcomes: str
    validation: str
    novelty: str
    citations: list[str]
