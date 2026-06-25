import json
import time
from dataclasses import dataclass, asdict


@dataclass
class TraceEvent:
    step: int
    event_type: str
    message: str
    phase: str = "execute"
    highlight: dict | None = None
    before: dict | None = None
    after: dict | None = None
    pedagogy: dict | None = None
    line: dict | None = None
    timestamp_ms: int = 0


class TraceBuilder:
    def __init__(self, problem_meta: dict, case: dict, max_events: int = 10000):
        self._problem_meta = problem_meta
        self._case = case
        self._max_events = max_events
        self._events: list[TraceEvent] = []
        self._step = 0
        self._truncated = False
        self._finished = False
        self._result_status = "running"
        self._result_actual = None

    def event(
        self,
        event_type: str,
        message: str,
        highlight: dict = None,
        before: dict = None,
        after: dict = None,
        pedagogy: dict = None,
        line: dict = None,
    ):
        """Record a trace event."""
        if self._finished:
            return
        if self._step >= self._max_events:
            self._truncated = True
            return
        self._step += 1
        self._events.append(
            TraceEvent(
                step=self._step,
                event_type=event_type,
                message=message,
                highlight=highlight,
                before=before,
                after=after,
                pedagogy=pedagogy,
                line=line,
                timestamp_ms=int(time.time() * 1000),
            )
        )

    def finish(self, status: str, actual):
        """Mark trace as finished."""
        self._finished = True
        self._result_status = status
        self._result_actual = actual

    def to_dict(self) -> dict:
        """Return complete trace envelope dict."""
        return {
            "trace_version": "0.1.0",
            "problem": self._problem_meta,
            "run": {
                "language": "python",
                "entry": self._problem_meta.get("entry", {}),
                "input": self._case.get("args", {}),
                "expected": self._case.get("expected"),
                "actual": self._result_actual,
                "status": self._result_status,
                "total_steps": self._step,
                "truncated": self._truncated,
            },
            "events": [asdict(e) for e in self._events],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise to JSON string."""
        return json.dumps(
            self.to_dict(), ensure_ascii=False, indent=indent, default=str
        )

    @property
    def step_count(self) -> int:
        return self._step
