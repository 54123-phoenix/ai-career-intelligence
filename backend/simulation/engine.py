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
                # Allow one prepare cycle; force advance to screened on second attempt
                # Prevents infinite prepare loop that causes timeout at MAX_STEPS
                if state.step_count >= 2:
                    state.current_step = "screened"
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


# ============================================================================
# Standalone runner — python -m backend.simulation.engine
# ============================================================================


def _print_separator(title: str = "", char: str = "=", width: int = 70) -> None:
    if title:
        side = (width - len(title) - 2) // 2
        print(f"\n{char * side} {title} {char * side}")
    else:
        print(char * width)


def _print_simulation_result(result, verbose: bool = False) -> None:
    """Print a human-readable summary of one simulation run."""
    from .product_view import to_product_view

    pv = to_product_view(result)

    _print_separator()
    print(f"Simulation: {result.simulation_id}")
    print(f"Strategy:   {result.strategy_name}")
    print(f"Outcome:    {result.outcome.upper()}")
    print(f"P(offer):   {result.success_probability:.3f}  "
          f"CI: [{result.confidence_interval[0]:.3f}, {result.confidence_interval[1]:.3f}]")
    print(f"Steps:      {result.final_state.step_count} / {result.final_state.max_steps}")
    print(f"Time-to-offer: {result.time_to_offer} steps")
    print()

    # Match score summary
    ms = pv["match_score"]
    print(f"Match Score: {ms['overall']}% ({ms['gauge']['label']})")
    print(f"  Skill match:     {ms['breakdown']['skill_match']}%")
    print(f"  Experience fit:  {ms['breakdown']['experience_fit']}%")
    print(f"  Keyword overlap: {ms['breakdown']['keyword_overlap']}%")
    print()

    # HR & Interview scores
    scores = result.final_state.scores
    if scores:
        print("Gate Scores:")
        for k, v in scores.items():
            print(f"  {k}: {v:.3f}")
        print()

    # Recommendation
    print(f"Recommendation: {result.recommendation}")

    # Failure points (if any)
    if verbose:
        from .explanation import explain
        expl = explain(result)
        fp = expl.get("failure_points", [])
        if fp:
            print("\n--- Failure Points ---")
            for pt in fp:
                print(f"  [{pt.get('severity', '?')}] {pt.get('stage', '?')}: {pt.get('cause', '?')}")
                print(f"    Fix: {pt.get('remediation', 'N/A')}")

        # Key decisions timeline
        kd = result.key_decisions
        if kd:
            print("\n--- Key Decisions ---")
            for i, d in enumerate(kd):
                print(f"  {i + 1}. [{d.agent_name}] {d.action}: {d.reasoning[:100]}")


def main() -> None:
    """Run simulation engine standalone with demo data.

    Demonstrates:
      - 10 resumes × 15 jobs with all 3 strategies
      - Weak match (junior vs principal) → should fail
      - Strong match (senior vs matching senior role) → should succeed
      - All rule-based, zero LLM dependency
    """
    from .demo_data import JOBS, RESUMES

    _print_separator("AI Career Intelligence — Simulation Engine Demo", "=", 70)
    print(f"Resumes loaded: {len(RESUMES)}")
    print(f"Jobs loaded:    {len(JOBS)}")
    print(f"Strategies:     aggressive, balanced, conservative")
    print(f"Max steps:      {MAX_STEPS}")
    print()

    engine = SimulationEngine()

    # ── Demo 1: Strong match (P7 Go/K8s engineer vs ByteDance Go backend role) ──
    _print_separator("Demo 1: Strong Match — P7 Go/K8s Engineer vs ByteDance Backend JD", "-")
    resume = RESUMES["res-zhao-min"]
    job = JOBS["job-bytedance-backend"]
    print(f"Candidate: {resume.name} | Skills: {', '.join(resume.skills[:8])}...")
    print(f"Job:       {job.title} @ {job.company} | Required: {', '.join(job.required_skills)}")
    for strategy in ("aggressive", "balanced", "conservative"):
        result = engine.run(resume, job, strategy=strategy)
        _print_simulation_result(result)

    # ── Demo 2: Weak match (P5 junior vs P9 principal architect role) ──
    _print_separator("Demo 2: Weak Match — P5 Junior Engineer vs P8 Expert Architect", "-")
    resume = RESUMES["res-zhang-wei"]
    job = JOBS["job-ali-staff-architect"]
    print(f"Candidate: {resume.name} | Skills: {', '.join(resume.skills)}")
    print(f"Job:       {job.title} @ {job.company} | Required: {', '.join(job.required_skills)}")
    for strategy in ("aggressive", "balanced", "conservative"):
        result = engine.run(resume, job, strategy=strategy)
        _print_simulation_result(result)

    # ── Demo 3: Cross-domain match (NLP engineer vs ML Platform role) ──
    _print_separator("Demo 3: Cross-Domain — NLP Engineer vs ML Platform Engineer", "-")
    resume = RESUMES["res-sun-yang"]
    job = JOBS["job-bytedance-ml-platform"]
    print(f"Candidate: {resume.name} | Skills: {', '.join(resume.skills[:8])}...")
    print(f"Job:       {job.title} @ {job.company} | Required: {', '.join(job.required_skills)}")
    for strategy in ("aggressive", "balanced", "conservative"):
        result = engine.run(resume, job, strategy=strategy)
        _print_simulation_result(result)

    # ── Demo 4: P9 expert vs matching expert role ──
    _print_separator("Demo 4: Expert Match — P9 Principal vs Alibaba P8 Architect", "-")
    resume = RESUMES["res-lin-tao"]
    job = JOBS["job-ali-staff-architect"]
    print(f"Candidate: {resume.name} | Skills: {', '.join(resume.skills[:8])}...")
    print(f"Job:       {job.title} @ {job.company} | Required: {', '.join(job.required_skills)}")
    for strategy in ("aggressive", "balanced", "conservative"):
        result = engine.run(resume, job, strategy=strategy)
        _print_simulation_result(result)

    # ── Batch run: all resumes against all jobs ──
    _print_separator(f"Batch Summary: All {len(RESUMES)} resumes × All {len(JOBS)} jobs", "-")
    print(f"{'Resume':<20} {'Job':<35} {'Strategy':<14} {'Outcome':<10} {'P(offer)':<10} {'Steps':<7}")
    print("-" * 96)
    accept_count = 0
    reject_count = 0
    timeout_count = 0
    total = 0

    for rid, resume in RESUMES.items():
        for jid, job in JOBS.items():
            for strategy in ("aggressive", "balanced", "conservative"):
                result = engine.run(resume, job, strategy=strategy)
                total += 1
                if result.outcome == "accepted":
                    accept_count += 1
                elif result.outcome == "rejected":
                    reject_count += 1
                else:
                    timeout_count += 1
                print(
                    f"{resume.name:<20} "
                    f"{job.title[:33]:<35} "
                    f"{strategy:<14} "
                    f"{result.outcome:<10} "
                    f"{result.success_probability:<10.3f} "
                    f"{result.final_state.step_count:<7}"
                )

    print("-" * 96)
    print(f"TOTAL: {total} | Accepted: {accept_count} ({accept_count / total:.1%}) | "
          f"Rejected: {reject_count} ({reject_count / total:.1%}) | "
          f"Timeout: {timeout_count} ({timeout_count / total:.1%})")

    _print_separator("Done", "=")
    print("To run with verbose output: python -m backend.simulation.engine --verbose")
    print("To run tests:              pytest tests/test_simulation.py -v")
    print("To pre-compute embeddings:  python -m backend.retrieval.seed_qdrant")


if __name__ == "__main__":
    import sys

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python -m backend.simulation.engine [--verbose] [--help]")
        print()
        print("  --verbose    Show failure points and key decision details")
        print("  --help       Show this message")
        print()
        print("Runs simulation engine standalone with demo data.")
        print("No API server, LLM, or database dependency required.")
        sys.exit(0)

    main()
