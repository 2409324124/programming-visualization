"""Line-level execution tracing for learner Solution methods via sys.settrace.

Only traces inside the target method (e.g. 'twoSum'), not module/class body.
Emits 'line', 'return', and 'exception' events.
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LineTraceEvent:
    step: int
    event_type: str = "line"       # "line" | "return" | "exception"
    filename: str = ""
    lineno: int = 0
    function: str = ""
    locals_summary: str = ""
    return_value_summary: str = ""  # only for return events
    error_summary: str = ""         # only for exception events


class LineTracer:
    """sys.settrace-based tracer that only records events inside *target_function*
    of *solution_path*.  Module-level code, class definitions, and stdlib/harness
    frames are silently ignored.
    """

    def __init__(
        self,
        solution_path: str,
        target_function: str,
        max_events: int = 1000,
    ):
        self.solution_path = str(Path(solution_path).resolve())
        self.target_function = target_function
        self.max_events = max_events
        self.events: list[LineTraceEvent] = []
        self.step = 0
        self.truncated = False
        self._inside_target = False  # set True when we enter the target function frame

    # ── public API ─────────────────────────────────────────────────────

    def start(self) -> None:
        sys.settrace(self._trace)

    def stop(self) -> None:
        sys.settrace(None)

    def to_dict(self) -> dict:
        return {
            "total_steps": self.step,
            "truncated": self.truncated,
            "events": [asdict(e) for e in self.events],
        }

    # ── internal ───────────────────────────────────────────────────────

    def _trace(self, frame, event, arg):
        if self.truncated:
            return None

        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name

        # Only care about frames in the user's solution file
        if Path(filename).resolve() != Path(self.solution_path).resolve():
            return self._trace  # keep tracing sub-calls that might re-enter solution

        # ── Entering / leaving the target function ─────────────────
        if event == "call" and func_name == self.target_function:
            self._inside_target = True
            return self._trace

        if event == "return" and func_name == self.target_function:
            if self._inside_target:
                self._record("return", frame, return_value=arg)
            self._inside_target = False
            return None  # stop tracing after target returns

        # ── Ignore everything outside the target function ──────────
        if not self._inside_target:
            return None

        # ── Exception inside target function ───────────────────────
        if event == "exception":
            self._record("exception", frame, error_value=arg)
            return self._trace

        # ── Line event inside target function ──────────────────────
        if event == "line" and func_name == self.target_function:
            self._record("line", frame)
            return self._trace

        return None

    def _record(
        self,
        event_type: str,
        frame,
        return_value: Any = None,
        error_value: Any = None,
    ) -> None:
        self.step += 1
        if self.step > self.max_events:
            self.truncated = True
            sys.settrace(None)
            return

        code = frame.f_code
        locals_summary = _safe_locals_summary(frame, event_type)
        return_summary = ""
        error_summary = ""

        if event_type == "return" and return_value is not None:
            try:
                return_summary = _safe_repr(return_value)
            except Exception:
                return_summary = "<unprintable>"

        if event_type == "exception" and error_value is not None:
            try:
                error_summary = f"{type(error_value[0]).__name__}: {error_value[1]}"
            except Exception:
                error_summary = str(error_value)

        self.events.append(LineTraceEvent(
            step=self.step,
            event_type=event_type,
            filename=Path(code.co_filename).name,
            lineno=frame.f_lineno,
            function=code.co_name,
            locals_summary=locals_summary,
            return_value_summary=return_summary,
            error_summary=error_summary,
        ))


# ── helpers ───────────────────────────────────────────────────────────


def _safe_locals_summary(frame, event_type: str) -> str:
    """Build a compact, safe locals summary string."""
    parts: list[str] = []
    for k, v in sorted(frame.f_locals.items()):
        if k == "self":
            continue
        try:
            parts.append(f"{k}={_safe_repr(v)}")
        except Exception:
            parts.append(f"{k}=<?>")
    return ", ".join(parts)


def _safe_repr(v: Any) -> str:
    if isinstance(v, (int, float, str, bool, type(None))):
        return repr(v)
    if isinstance(v, (list, tuple)):
        if len(v) <= 10:
            return repr(v)
        return f"{type(v).__name__}[{len(v)}]"
    if isinstance(v, dict):
        if len(v) <= 5:
            return repr({str(kk): vv for kk, vv in v.items()})
        return f"dict[{len(v)}]"
    return f"<{type(v).__name__}>"
