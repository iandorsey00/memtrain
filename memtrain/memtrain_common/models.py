from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass
class ProgressRecord:
    current_stage: int = 0
    mastery_score: float = 0.0
    success_streak: int = 0
    failure_count: int = 0
    lapse_count: int = 0
    average_response_time: float = 0.0
    reviews: int = 0
    last_seen_at: str | None = None
    next_due_at: str | None = None

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None = None) -> "ProgressRecord":
        if values is None:
            return cls()

        return cls(
            current_stage=int(values.get("current_stage", 0)),
            mastery_score=float(values.get("mastery_score", 0.0)),
            success_streak=int(values.get("success_streak", 0)),
            failure_count=int(values.get("failure_count", 0)),
            lapse_count=int(values.get("lapse_count", 0)),
            average_response_time=float(values.get("average_response_time", 0.0)),
            reviews=int(values.get("reviews", 0)),
            last_seen_at=values.get("last_seen_at"),
            next_due_at=values.get("next_due_at"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "current_stage": self.current_stage,
            "mastery_score": self.mastery_score,
            "success_streak": self.success_streak,
            "failure_count": self.failure_count,
            "lapse_count": self.lapse_count,
            "average_response_time": self.average_response_time,
            "reviews": self.reviews,
            "last_seen_at": self.last_seen_at,
            "next_due_at": self.next_due_at,
        }


@dataclass
class SessionItem:
    item_id: str
    cue: str
    response: str
    cue_id: int
    response_id: int
    placement: int
    progress: ProgressRecord = field(default_factory=ProgressRecord)
    current_stage: int = 0
    level: str = "1"
    stage_label: str = "New"
    is_new: bool = True
    next_due_at: datetime | None = None
    is_due: bool = False
    is_weak: bool = False
    session_stage: int = 0
