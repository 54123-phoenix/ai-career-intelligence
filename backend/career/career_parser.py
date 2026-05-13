"""CareerParser — parse raw user behavior into standardized CareerEvent JSON (T007 Step 1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from backend.career.schemas import CareerEvent


class CareerParser:
    """Parse raw user behavior input into standardized CareerEvent objects.

    Handles both structured dict input and free-text descriptions.
    Extracts event_type, skills, outcome, company, and job metadata.

    Usage:
        parser = CareerParser()
        event = parser.parse({"type": "interview", "company": "Google", ...})
        events = parser.parse_batch([...])
    """

    # Known event type mappings from raw text/aliases
    _EVENT_ALIASES: dict[str, str] = {
        "view": "job_view", "viewed": "job_view", "browse": "job_view",
        "apply": "application_sent", "applied": "application_sent", "application": "application_sent",
        "phone": "phone_screen", "hr_screen": "phone_screen", "screening": "phone_screen",
        "interview": "interview", "interviewed": "interview", "onsite": "interview",
        "tech": "technical_test", "technical": "technical_test", "coding_test": "technical_test",
        "offer": "offer_received", "got_offer": "offer_received",
        "accept": "offer_accepted", "accepted": "offer_accepted",
        "decline": "offer_declined", "declined": "offer_declined", "rejected_offer": "offer_declined",
        "reject": "rejection", "rejected": "rejection", "rejection": "rejection",
        "learn": "skill_acquired", "learned": "skill_acquired", "skill": "skill_acquired",
        "course": "course_completed", "completed": "course_completed",
        "promotion": "promotion", "promoted": "promotion",
        "job_change": "job_change", "switch": "job_change", "new_job": "job_change",
        "resume": "resume_updated", "updated_resume": "resume_updated",
        "network": "networking_event", "networking": "networking_event", "meetup": "networking_event",
    }

    _OUTCOME_MAP: dict[str, str] = {
        "offer_received": "success", "offer_accepted": "success",
        "promotion": "success", "job_change": "success",
        "rejection": "failure",
        "application_sent": "pending", "interview": "pending",
        "phone_screen": "pending", "technical_test": "pending",
        "skill_acquired": "success", "course_completed": "success",
        "job_view": "neutral", "resume_updated": "neutral",
        "networking_event": "neutral",
        "offer_declined": "neutral",
    }

    def parse(self, raw: dict | str, user_id: str = "default") -> CareerEvent:
        """Parse a single raw input into a CareerEvent.

        Args:
            raw: Dict with event fields, or free-text string
            user_id: Owning user identifier

        Returns:
            Standardized CareerEvent
        """
        if isinstance(raw, str):
            return self._parse_text(raw, user_id)

        event_type = self._normalize_event_type(raw.get("type") or raw.get("event_type", "job_view"))
        outcome = raw.get("outcome") or self._OUTCOME_MAP.get(event_type, "pending")

        return CareerEvent(
            event_id=raw.get("event_id") or f"evt-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            event_type=event_type,
            timestamp=raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            job_id=raw.get("job_id"),
            job_title=raw.get("job_title") or raw.get("title"),
            company=raw.get("company"),
            location=raw.get("location"),
            salary_range=self._parse_salary(raw.get("salary")),
            skills_involved=self._parse_list(raw.get("skills") or raw.get("skills_involved", [])),
            skills_acquired=self._parse_list(raw.get("skills_acquired") or raw.get("learned", [])),
            outcome=outcome,
            confidence=float(raw.get("confidence", 1.0)),
            notes=str(raw.get("notes") or raw.get("description", "")),
            source=raw.get("source", "manual"),
        )

    def parse_batch(self, raw_list: list, user_id: str = "default") -> list[CareerEvent]:
        """Parse multiple raw inputs. Sorted by timestamp ascending."""
        events = [self.parse(item, user_id) for item in raw_list]
        events.sort(key=lambda e: e.timestamp)
        return events

    # ── Internal ──────────────────────────────────────────────────────────

    def _parse_text(self, text: str, user_id: str) -> CareerEvent:
        """Best-effort parse from free text."""
        text_lower = text.lower().strip()
        # Try to match event type — check longer aliases first (avoids "view" matching "interviewed")
        event_type = "job_view"
        sorted_aliases = sorted(self._EVENT_ALIASES.items(), key=lambda x: -len(x[0]))
        for alias, mapped in sorted_aliases:
            if alias in text_lower:
                event_type = mapped
                break

        # Try to extract company name (simple heuristic)
        company = None
        for prefix in ["at ", "@", "with "]:
            if prefix in text:
                rest = text.split(prefix, 1)[1].strip().split()[0]
                company = rest.rstrip(",.;!")
                break

        return CareerEvent(
            user_id=user_id,
            event_type=event_type,
            notes=text,
            company=company,
            outcome=self._OUTCOME_MAP.get(event_type, "pending"),
            source="import",
        )

    @staticmethod
    def _normalize_event_type(raw_type: str | None) -> str:
        """Map raw type strings to standard CareerEvent.event_type."""
        if not raw_type:
            return "job_view"
        normalized = raw_type.lower().strip().replace(" ", "_")
        return CareerParser._EVENT_ALIASES.get(normalized, normalized)

    @staticmethod
    def _parse_list(value) -> list[str]:
        """Normalize list input (comma-separated str, list, or single value)."""
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if isinstance(value, str):
            return [s.strip() for s in value.split(",") if s.strip()]
        return []

    @staticmethod
    def _parse_salary(value) -> tuple[int, int] | None:
        """Parse salary input into (min, max) tuple."""
        if value is None:
            return None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return (int(value[0]), int(value[1]))
        return None
