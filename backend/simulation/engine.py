"""SimulationEngine — multi-agent state machine orchestrator.

Pipeline:
  while not terminal:
    1. CandidateAgent(state)   → decision
    2. apply decision          → transition state
    3. HRAgent(state)          → gate evaluation (at screening / interview)
    4. update scores + step
    5. snapshot history

Terminal: accepted | rejected | step_count >= max_steps(5)
Output:   SimulationResult
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime

from backend.shared.types import StructuredJob, StructuredResume

from .candidate_agent import CandidateAgent
from .hr_agent import HRAgent
from .state import AgentDecision, SimulationResult, SimulationState

# MVP cap — simulation terminates after this many steps
MAX_STEPS = 5


class SimulationEngine:
    """Orchestrates a single-path simulation through the hiring pipeline.

    Usage:
        engine = SimulationEngine()
        result = engine.run(resume, job, strategy="balanced")
    """

    def __init__(self):
        self._candidate = CandidateAgent()
        self._hr = HRAgent()

    # ---- public API ---------------------------------------------------------

    def run(
        self,
        resume: StructuredResume,
        job: StructuredJob,
        strategy: str = "balanced",
    ) -> SimulationResult:
        """Run one simulation path from applied → terminal."""
        sim_id = f"sim-{uuid.uuid4().hex[:8]}"
        state = SimulationState(
            simulation_id=sim_id,
            strategy_name=strategy,
            candidate=resume,
            job=job,
            current_step="applied",
            max_steps=MAX_STEPS,
        )

        path: list[SimulationState] = [deepcopy(state)]
        key_decisions: list[AgentDecision] = []

        while not self._is_terminal(state):
            # 1. CandidateAgent decides
            c_decision = self._candidate.act(state)
            state.decisions.append(c_decision)
            state.step_count += 1

            # 2. Apply decision → transition
            self._transition(state, c_decision)
            if c_decision.action in ("apply", "pivot"):
                key_decisions.append(c_decision)

            # 3. Gate evaluation where applicable
            if state.current_step == "screened":
                hr_decision = self._hr.act(state)
                state.decisions.append(hr_decision)
                state.scores["hr_screen"] = hr_decision.params["score"]
                if hr_decision.params.get("hard_pass") or not hr_decision.params.get("passed"):
                    state.current_step = "rejected"
                key_decisions.append(hr_decision)

            elif state.current_step == "interview":
                # Simulated interview gate — combine hr_score + candidate confidence
                hr_score = state.scores.get("hr_screen", 0.5)
                candidate_confidence = c_decision.confidence
                interview_score = round((hr_score * 0.6 + candidate_confidence * 0.4), 3)
                state.scores["interview"] = interview_score
                if interview_score >= 0.45:
                    state.current_step = "offer"
                else:
                    state.current_step = "rejected"

            elif state.current_step == "offer":
                # Candidate decides to accept/reject
                final_score = state.scores.get("interview", 0.5)
                state.scores["final"] = final_score
                if c_decision.params.get("action") == "accept":
                    state.current_step = "accepted"
                else:
                    state.current_step = "rejected"

            # 4. Update timestamp
            state.timestamp = datetime.now().isoformat()

            # 5. Snapshot
            path.append(deepcopy(state))

            # Safety break
            if state.step_count >= MAX_STEPS:
                break

        # Post-loop: ensure terminal
        if state.current_step not in ("accepted", "rejected", "end"):
            state.current_step = "rejected"

        # Compute outcome
        outcome = "accepted" if state.current_step == "accepted" else "rejected"
        if state.step_count >= MAX_STEPS and outcome != "accepted":
            outcome = "timeout"

        # Probability estimate
        success_prob = self._estimate_success(state, outcome)

        return SimulationResult(
            simulation_id=sim_id,
            strategy_name=strategy,
            outcome=outcome,
            final_state=state,
            success_probability=round(success_prob, 3),
            confidence_interval=(round(max(0, success_prob - 0.1), 3), round(min(1, success_prob + 0.1), 3)),
            key_decisions=key_decisions[:5],
            time_to_offer=state.step_count if outcome == "accepted" else 0,
            path_history=path,
            recommendation=self._recommend(state, outcome),
        )

    # ---- state transition ---------------------------------------------------

    def _transition(self, state: SimulationState, decision: AgentDecision) -> None:
        """Advance current_step based on candidate action + current position."""
        action = decision.action
        step = state.current_step

        if step == "applied":
            if action == "apply":
                state.current_step = "screened"
            elif action == "prepare":
                pass  # stay in applied, skill up
            elif action == "pivot":
                state.current_step = "rejected"

        elif step == "screened":
            if action in ("apply", "prepare"):
                state.current_step = "interview"
            elif action == "pivot":
                state.current_step = "rejected"

        elif step == "interview":
            if action in ("apply", "prepare"):
                state.current_step = "offer"
            elif action == "pivot":
                state.current_step = "rejected"

        elif step == "offer":
            if decision.params.get("action") == "accept":
                state.current_step = "accepted"
            else:
                state.current_step = "rejected"

        elif step in ("accepted", "rejected", "end"):
            pass  # terminal

    # ---- helpers ------------------------------------------------------------

    @staticmethod
    def _is_terminal(state: SimulationState) -> bool:
        return (
            state.current_step in ("accepted", "rejected", "end")
            or state.step_count >= state.max_steps
        )

    @staticmethod
    def _estimate_success(state: SimulationState, outcome: str) -> float:
        """Crude P(offer) estimate from gate scores."""
        if outcome == "accepted":
            return 0.8
        hr = state.scores.get("hr_screen", 0.0)
        iv = state.scores.get("interview", 0.0)
        if hr > 0 and iv > 0:
            return round(hr * 0.5 + iv * 0.5, 3)
        if hr > 0:
            return round(hr * 0.7, 3)
        return 0.1

    @staticmethod
    def _recommend(state: SimulationState, outcome: str) -> str:
        if outcome == "accepted":
            return (
                f"Strategy '{state.strategy_name}' succeeded. "
                f"HR screen: {state.scores.get('hr_screen', 'N/A')}, "
                f"Interview: {state.scores.get('interview', 'N/A')}. "
                "Proceed with this approach."
            )
        gap_skills = []
        for d in state.decisions:
            if "gap_skills" in d.params:
                gap_skills = d.params["gap_skills"]
        if gap_skills:
            return (
                f"Strategy '{state.strategy_name}' failed. "
                f"Skill gaps: {', '.join(gap_skills[:3])}. "
                "Recommend upskilling before next application."
            )
        return (
            f"Strategy '{state.strategy_name}' did not result in an offer. "
            "Consider a different strategy or target role."
        )
