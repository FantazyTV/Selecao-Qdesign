from pydantic import BaseModel


class RunRequest(BaseModel):
    project_description: str
    concept_a: str
    concept_b: str


class RunResponse(BaseModel):
    run_id: str
    status: str


class StatusResponse(BaseModel):
    run_id: str
    status: str
    data: dict


class FeedbackRequest(BaseModel):
    run_id: str
    stage: str
    action: str
    notes: str | None = None


class HypothesisResponse(BaseModel):
    run_id: str
    hypothesis: dict | None
