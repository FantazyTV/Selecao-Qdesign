from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RunState:
    run_id: str
    status: str
    created_at: str
    data: dict = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)


class InMemoryStateManager:
    def __init__(self):
        self._runs: dict[str, RunState] = {}

    def create_run(self, run_id: str) -> RunState:
        ts = datetime.now(timezone.utc).isoformat()
        state = RunState(run_id, "CREATED", ts)
        self._runs[run_id] = state
        return state

    def get_run(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def update_run(self, run_id: str, **kwargs) -> None:
        state = self._runs[run_id]
        for key, value in kwargs.items():
            setattr(state, key, value)

    def add_audit(self, run_id: str, entry: dict) -> None:
        self._runs[run_id].audit.append(entry)
