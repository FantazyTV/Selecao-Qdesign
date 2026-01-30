from pydantic import BaseModel


class HumanFeedback(BaseModel):
    run_id: str
    stage: str
    action: str
    notes: str | None = None
