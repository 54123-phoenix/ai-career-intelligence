"""HRAgent — simulates an HR screener evaluating a candidate against a job.

Input:  SimulationState (candidate + job)
Output: AgentDecision {action: screen, params: {score, hard_pass, rejection_reasons[]}}

Rules (no embedding, no LLM):
  1. Skill mismatch penalty     — 60% weight
  2. Experience vs job level    — 25% weight
  3. Keyword matching           — 15% weight
"""

from __future__ import annotations

from datetime import datetime

from backend.shared.types import StructuredJob, StructuredResume

from .state import AgentDecision, SimulationState

# ---------------------------------------------------------------------------
# Job level → expected years of experience
# ---------------------------------------------------------------------------
LEVEL_EXPECTATIONS: dict[str, int] = {
    "初级": 1,
    "中级": 3,
    "高级": 5,
    "专家": 8,
    "junior": 1,
    "mid": 3,
    "senior": 5,
    "lead": 7,
    "staff": 8,
    "principal": 10,
}

# Hard pass: reject if skill match below this AND no related skills
HARD_PASS_SKILL_THRESHOLD = 0.2

# Keywords for title/description matching bonus
TECH_KEYWORDS = {
    "backend", "frontend", "fullstack", "data", "ml", "ai", "devops",
    "cloud", "mobile", "embedded", "security", "qa", "test", "platform",
    "infrastructure", "sre", "architect",
}


class HRAgent:
    """Simulates HR resume screening.

    Scoring breakdown:
      skill_score  (0.60) — how many required skills the candidate has
      exp_score    (0.25) — does experience level match the job level?
      keyword_score(0.15) — title/description overlap with resume

    Hard pass triggers:
      - skill match < 20% AND no related skills in candidate's repertoire
      - zero experience for senior+ roles
    """

    def act(self, state: SimulationState) -> AgentDecision:
        candidate = state.candidate
        job = state.job

        # ── compute sub-scores ──────────────────────────────────────────
        skill_score = self._skill_match(candidate, job)
        exp_score = self._experience_match(candidate, job)
        keyword_score = self._keyword_match(candidate, job)

        # ── weighted total ──────────────────────────────────────────────
        total = round(
            0.60 * skill_score
            + 0.25 * exp_score
            + 0.15 * keyword_score,
            3,
        )

        # ── rejection reasons ───────────────────────────────────────────
        reasons: list[str] = []
        hard_pass = False

        required = job.required_skills
        c_skills = {s.lower().strip() for s in candidate.skills}
        matched_required = [s for s in required if s.lower().strip() in c_skills]
        missing_required = [s for s in required if s.lower().strip() not in c_skills]

        # Skill-based hard pass
        if skill_score < HARD_PASS_SKILL_THRESHOLD:
            # Check if ANY related skills exist (via optional_skills overlap)
            optional_overlap = [
                s for s in job.optional_skills if s.lower().strip() in c_skills
            ]
            if not optional_overlap:
                hard_pass = True
                reasons.append(
                    f"Skill match {skill_score:.0%}: missing {len(missing_required)}/{len(required)} "
                    f"required skills ({', '.join(missing_required[:3])}...). "
                    f"No related optional skills found."
                )

        # Experience-based hard pass (senior+ roles need some experience)
        job_level_lower = job.level.lower().strip()
        is_senior_plus = any(
            word in job_level_lower for word in ("senior", "高级", "lead", "staff", "principal", "专家")
        )
        if is_senior_plus and exp_score < 0.2:
            hard_pass = True
            reasons.append(
                f"Senior+ role requires demonstrated experience. "
                f"Candidate experience score: {exp_score:.0%}."
            )

        # Non-fatal skill gaps
        if missing_required and not hard_pass:
            gap_count = len(missing_required)
            gap_frac = gap_count / max(len(required), 1)
            if gap_frac > 0.5:
                reasons.append(
                    f"Significant skill gap: missing {gap_count}/{len(required)} "
                    f"required skills."
                )
            elif gap_frac > 0.3:
                reasons.append(
                    f"Moderate skill gap: missing {gap_frac:.0%} of required skills."
                )

        # Experience note
        if exp_score < 0.4:
            reasons.append(
                f"Experience level ({exp_score:.0%}) below expectations for {job.level} role."
            )

        # ── build decision ──────────────────────────────────────────────
        passed = not hard_pass and total >= 0.35

        return AgentDecision(
            agent_name="hr",
            action="screen",
            params={
                "score": total,
                "passed": passed,
                "hard_pass": hard_pass,
                "sub_scores": {
                    "skill": round(skill_score, 3),
                    "experience": round(exp_score, 3),
                    "keyword": round(keyword_score, 3),
                },
                "matched_required": matched_required,
                "missing_required": missing_required[:5],
                "rejection_reasons": reasons if not passed else [],
            },
            reasoning=(
                f"HR screen: {'PASS' if passed else 'FAIL'}"
                f"{' (HARD)' if hard_pass else ''}. "
                f"Score={total:.2f} (skill={skill_score:.0%}, exp={exp_score:.0%}, kw={keyword_score:.0%}). "
                + (f"Reasons: {'; '.join(reasons)}" if reasons else "No concerns.")
            ),
            confidence=round(1.0 - abs(0.5 - total), 2),  # higher confidence near extremes
            timestamp=datetime.now().isoformat(),
        )

    # ---- sub-scoring functions -----------------------------------------------

    def _skill_match(self, candidate: StructuredResume, job: StructuredJob) -> float:
        """Core skill match: |candidate ∩ required| / |required|.

        Bonus: +0.1 per optional_skill matched (capped at 1.0).
        """
        if not job.required_skills:
            return 1.0

        c_set = {s.lower().strip() for s in candidate.skills}
        matched = sum(1 for s in job.required_skills if s.lower().strip() in c_set)
        base = matched / len(job.required_skills)

        # Optional skill bonus
        if job.optional_skills:
            opt_matched = sum(1 for s in job.optional_skills if s.lower().strip() in c_set)
            bonus = min(opt_matched * 0.05, 0.15)
        else:
            bonus = 0.0

        return min(base + bonus, 1.0)

    def _experience_match(self, candidate: StructuredResume, job: StructuredJob) -> float:
        """Estimate experience relevance from resume.experience list.

        Factors:
          - Total years inferred from experience entries
          - Title keyword overlap with job title
          - Tech stack overlap with job requirements
        """
        if not candidate.experience:
            return 0.1  # entry-level baseline

        total_years = 0.0
        title_hits = 0
        tech_overlap = 0
        job_title_lower = job.title.lower()
        job_tech = {s.lower().strip() for s in job.required_skills}

        for exp in candidate.experience:
            # Duration estimation
            years = self._estimate_years(exp)
            total_years += years

            # Title relevance
            exp_title_lower = exp.title.lower()
            if any(word in exp_title_lower for word in job_title_lower.split()):
                title_hits += 1

            # Tech stack overlap
            exp_tech = {t.lower().strip() for t in exp.tech_stack}
            tech_overlap += len(exp_tech & job_tech)

        expected = LEVEL_EXPECTATIONS.get(job.level.lower().strip(), 3)
        years_score = min(total_years / max(expected, 1), 1.0)
        title_score = min(title_hits / max(len(candidate.experience), 1), 1.0)
        tech_score = min(tech_overlap / max(len(job_tech) * len(candidate.experience), 1), 1.0)

        return round(0.50 * years_score + 0.25 * title_score + 0.25 * tech_score, 3)

    def _keyword_match(self, candidate: StructuredResume, job: StructuredJob) -> float:
        """Keyword overlap between job text fields and resume text fields."""
        job_text = f"{job.title} {job.description} {' '.join(job.required_skills)} {job.level}".lower()
        resume_text = (
            f"{candidate.summary} {' '.join(candidate.skills)} "
            + " ".join(p.description for p in candidate.projects)
            + " ".join(e.description for e in candidate.experience)
        ).lower()

        job_words = set(job_text.split())
        resume_words = set(resume_text.split())
        if not job_words:
            return 0.5

        tech_job_words = job_words & TECH_KEYWORDS
        if tech_job_words:
            overlap = len(tech_job_words & resume_words)
            return min(overlap / len(tech_job_words), 1.0)

        overlap = len(job_words & resume_words)
        return min(overlap / len(job_words), 1.0)

    # ---- helpers -------------------------------------------------------------

    @staticmethod
    def _estimate_years(exp) -> float:
        """Estimate years from WorkExperience start/end dates."""
        if exp.start_date and exp.end_date:
            delta = exp.end_date - exp.start_date
            return max(delta.days / 365.0, 0.0)
        if exp.start_date:
            from datetime import date

            delta = date.today() - exp.start_date
            return max(delta.days / 365.0, 0.0)
        return 1.0  # default when no dates
