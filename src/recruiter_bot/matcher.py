"""
Core Matching Engine for Recruiter-Bot.
Computes multi-factor match scores, detailed breakdowns, and explainable recruitment reasons.
"""
from typing import Dict, Any, List, Tuple


def _normalize(text: str) -> str:
    """Normalizes skill/trait string for consistent comparison."""
    return text.lower().strip()


def compute_match(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a comprehensive match score between a candidate and a job opening.

    Score Breakdown (Total 100 points):
    1. Skill Fit (50 pts): Hard technical requirement coverage.
    2. Experience Fit (25 pts): Seniority alignment against minimum requirement.
    3. Availability Fit (15 pts): Immediacy and pipeline velocity.
    4. Culture & Trait Fit (10 pts): Alignment between candidate traits & culture keywords.
    """
    # -------------------------------------------------------------
    # 1. Skill Overlap (0 - 50 points)
    # -------------------------------------------------------------
    candidate_skills = {_normalize(s) for s in candidate.get("skills", [])}
    required_skills = [_normalize(s) for s in job.get("required_skills", [])]
    required_set = set(required_skills)

    matched_skills = [s for s in required_skills if s in candidate_skills]
    missing_skills = [s for s in required_skills if s not in candidate_skills]

    if not required_set:
        skill_score = 50.0
    else:
        coverage_ratio = len(matched_skills) / len(required_set)
        skill_score = coverage_ratio * 48.0
        # Small depth bonus for candidates with relevant adjacent skills
        extra_skills = len(candidate_skills - required_set)
        breadth_bonus = min(2.0, extra_skills * 0.5)
        skill_score = min(50.0, skill_score + (breadth_bonus if coverage_ratio > 0 else 0.0))

    # -------------------------------------------------------------
    # 2. Experience Fit (0 - 25 points)
    # -------------------------------------------------------------
    cand_exp = candidate.get("experience_years", 0)
    min_exp = job.get("min_experience_years", 0)

    if cand_exp < min_exp:
        # Deficit penalty: proportional to experience completed
        if min_exp > 0:
            exp_score = (cand_exp / min_exp) * 14.0
        else:
            exp_score = 14.0
        exp_status = f"Deficit: {cand_exp} yrs vs {min_exp} yrs required"
    else:
        # Baseline meeting the minimum experience is 20 points
        exp_score = 20.0
        years_above = cand_exp - min_exp
        if years_above <= 6:
            # Optimal sweet spot bonus
            exp_score += min(5.0, years_above * 1.0)
            exp_status = f"Solid fit: {cand_exp} yrs satisfies {min_exp} yrs min"
        else:
            # Overqualification assessment
            if cand_exp >= 15 and years_above >= 10:
                # Highly senior candidate for junior/mid role
                exp_score = 22.0
                exp_status = f"Highly seasoned: {cand_exp} yrs (watch for overqualification for {min_exp} yr role)"
            else:
                exp_score = 24.0
                exp_status = f"Experienced: {cand_exp} yrs exceeds {min_exp} yrs min"

    # -------------------------------------------------------------
    # 3. Availability Fit (0 - 15 points)
    # -------------------------------------------------------------
    avail_str = candidate.get("availability", "").strip().lower()
    if "immediate" in avail_str:
        avail_score = 15.0
        avail_status = "Available immediately"
    elif "2 weeks" in avail_str or "two weeks" in avail_str or "notice" in avail_str:
        avail_score = 12.0
        avail_status = "Available with 2 weeks notice"
    elif "not looking" in avail_str:
        avail_score = 4.0
        avail_status = "Passive candidate (currently not looking)"
    else:
        avail_score = 8.0
        avail_status = f"Availability: {candidate.get('availability')}"

    # -------------------------------------------------------------
    # 4. Culture & Trait Fit (0 - 10 points)
    # -------------------------------------------------------------
    cand_traits = {_normalize(t) for t in candidate.get("traits", [])}
    culture_keywords = [_normalize(k) for k in job.get("culture_keywords", [])]
    culture_set = set(culture_keywords)

    matched_culture = [k for k in culture_keywords if k in cand_traits]

    if not culture_set:
        culture_score = 10.0
    else:
        trait_ratio = len(matched_culture) / len(culture_set)
        if trait_ratio > 0:
            culture_score = round(trait_ratio * 10.0, 1)
        else:
            culture_score = 1.5 if cand_traits else 0.0

    # -------------------------------------------------------------
    # Overall Score & Reason Formulation
    # -------------------------------------------------------------
    total_score = round(skill_score + exp_score + avail_score + culture_score, 1)
    total_score = max(0.0, min(100.0, total_score))

    # Formulate short explainable recruitment reason
    reasons = []
    if required_set:
        if len(matched_skills) == len(required_set):
            reasons.append(f"Complete skill match on {', '.join(matched_skills)}")
        elif len(matched_skills) > 0:
            reasons.append(
                f"Partial skill match ({len(matched_skills)}/{len(required_set)}: {', '.join(matched_skills)}; missing: {', '.join(missing_skills)})"
            )
        else:
            reasons.append(f"No matching required skills (missing: {', '.join(missing_skills)})")

    reasons.append(exp_status)
    reasons.append(avail_status)

    if matched_culture:
        reasons.append(f"Culture alignment on {', '.join(matched_culture)}")

    quirk = candidate.get("quirk")
    if quirk:
        reasons.append(f"Quirk note: {quirk}")

    full_reason = ". ".join(reasons) + "."

    return {
        "job_id": job.get("id"),
        "candidate_id": candidate.get("id"),
        "overall_score": total_score,
        "skill_score": round(skill_score, 1),
        "experience_score": round(exp_score, 1),
        "availability_score": round(avail_score, 1),
        "culture_score": round(culture_score, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_culture": matched_culture,
        "reason": full_reason,
    }


def rank_candidates_for_job(
    job: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    min_score: float = 0.0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Ranks candidates for a given job, sorting by score, skill_score, experience_score,
    and candidate name for deterministic tie-breaking.
    """
    matches = []
    for cand in candidates:
        match_info = compute_match(cand, job)
        if match_info["overall_score"] >= min_score:
            matches.append({"candidate": cand, "match": match_info})

    # Tie-breaking sort
    matches.sort(
        key=lambda item: (
            -item["match"]["overall_score"],
            -item["match"]["skill_score"],
            -item["match"]["experience_score"],
            item["candidate"]["name"],
        )
    )

    return matches[:limit]


def rank_jobs_for_candidate(
    candidate: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    min_score: float = 0.0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Ranks jobs for a given candidate, sorting by score, skill_score, experience_score,
    and job title for deterministic tie-breaking.
    """
    matches = []
    for job in jobs:
        match_info = compute_match(candidate, job)
        if match_info["overall_score"] >= min_score:
            matches.append({"job": job, "match": match_info})

    # Tie-breaking sort
    matches.sort(
        key=lambda item: (
            -item["match"]["overall_score"],
            -item["match"]["skill_score"],
            -item["match"]["experience_score"],
            item["job"]["title"],
        )
    )

    return matches[:limit]
