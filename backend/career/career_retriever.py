"""CareerRetriever — retrieve historical career data for a user (T007 Step 2).

Output: CareerTimeline with recent events, skill trajectory, interview history,
and application distribution.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from backend.career.schemas import CareerEvent, CareerTimeline, SkillSnapshot


class CareerRetriever:
    """Retrieve and structure historical career data for a user.

    In-memory event store. In production, replace with database-backed storage.

    Usage:
        retriever = CareerRetriever()
        retriever.ingest(event)
        timeline = retriever.retrieve("user-1")
    """

    def __init__(self):
        self._events: dict[str, list[CareerEvent]] = defaultdict(list)

    # ── Public API ────────────────────────────────────────────────────────

    def ingest(self, event: CareerEvent) -> None:
        """Store a career event."""
        self._events[event.user_id].append(event)
        self._events[event.user_id].sort(key=lambda e: e.timestamp)

    def ingest_batch(self, events: list[CareerEvent]) -> None:
        """Store multiple events."""
        for e in events:
            self._events[e.user_id].append(e)
        for uid in {e.user_id for e in events}:
            self._events[uid].sort(key=lambda e: e.timestamp)

    def retrieve(self, user_id: str) -> CareerTimeline:
        """Retrieve structured career history for a user.

        Returns CareerTimeline with:
          - Last 10 events
          - Skill trajectory over time
          - Interview success/failure records
          - Application distribution
        """
        events = self._events.get(user_id, [])
        if not events:
            return CareerTimeline(user_id=user_id)

        events.sort(key=lambda e: e.timestamp)

        # Recent 10 events
        recent = events[-10:][::-1]  # newest first

        # Skill trajectory
        skill_traj = self._build_skill_trajectory(events)

        # Interview outcomes
        interview_successes = [
            e for e in events
            if e.event_type in ("interview", "phone_screen", "technical_test")
            and e.outcome == "success"
        ]
        interview_failures = [
            e for e in events
            if e.event_type in ("interview", "phone_screen", "technical_test")
            and e.outcome == "failure"
        ]

        # Application distribution
        app_dist = self._build_application_distribution(events)

        # Stats
        total = len(events)
        active_days = self._compute_active_days(events)
        avg_per_week = (total / (active_days / 7)) if active_days > 0 else 0.0

        return CareerTimeline(
            user_id=user_id,
            recent_events=recent,
            skill_trajectory=skill_traj,
            interview_successes=interview_successes,
            interview_failures=interview_failures,
            application_distribution=app_dist,
            total_events=total,
            active_days=active_days,
            average_events_per_week=round(avg_per_week, 2),
        )

    def get_events(self, user_id: str, limit: int = 50) -> list[CareerEvent]:
        """Get raw events for a user, newest first."""
        events = sorted(
            self._events.get(user_id, []),
            key=lambda e: e.timestamp,
            reverse=True,
        )
        return events[:limit]

    def clear(self, user_id: str | None = None) -> None:
        """Clear events. If user_id is None, clears all."""
        if user_id:
            self._events.pop(user_id, None)
        else:
            self._events.clear()

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_skill_trajectory(events: list[CareerEvent]) -> list[SkillSnapshot]:
        """Build month-by-month skill trajectory from events."""
        # Group events by month
        by_month: dict[str, list[CareerEvent]] = defaultdict(list)
        for e in events:
            month_key = e.timestamp[:7]  # "2026-05"
            by_month[month_key].append(e)

        snapshots: list[SkillSnapshot] = []
        cumulative_skills: dict[str, float] = {}

        for month_key in sorted(by_month.keys()):
            month_events = by_month[month_key]
            new_skills: list[str] = []

            for e in month_events:
                # Add acquired skills at proficiency 0.7
                for skill in e.skills_acquired:
                    skill_lower = skill.lower().strip()
                    if skill_lower not in cumulative_skills:
                        new_skills.append(skill_lower)
                    cumulative_skills[skill_lower] = max(
                        cumulative_skills.get(skill_lower, 0.0), 0.7
                    )
                # Increment involved skills slightly
                for skill in e.skills_involved:
                    skill_lower = skill.lower().strip()
                    current = cumulative_skills.get(skill_lower, 0.3)
                    cumulative_skills[skill_lower] = min(current + 0.1, 1.0)

            snapshots.append(
                SkillSnapshot(
                    date=month_key,
                    skills=dict(cumulative_skills),
                    new_skills=new_skills,
                )
            )

        return snapshots

    @staticmethod
    def _build_application_distribution(events: list[CareerEvent]) -> dict[str, int]:
        """Count events by type for distribution breakdown."""
        counter: Counter = Counter(e.event_type for e in events)
        return dict(counter.most_common())

    @staticmethod
    def _compute_active_days(events: list[CareerEvent]) -> int:
        """Count unique days with at least one event."""
        if not events:
            return 0
        days = {e.timestamp[:10] for e in events}
        return len(days)
