"""Required/preferred weighted matching in the extracted canonical skill space."""

from __future__ import annotations

from typing import Any, Callable


REQUIRED_WEIGHT = 0.7
PREFERRED_WEIGHT = 0.3


def parse_skill_field(value: str | None) -> set[str]:
    return {skill.strip() for skill in (value or "").split("|") if skill.strip()}


def extract_posting_skill_sets(
    postings: list[dict[str, str]],
    threshold: float = 0.55,
    extractor: Callable[..., list[dict[str, Any]]] | None = None,
) -> list[set[str]]:
    """Extract shared-space skills from posting descriptions, never from labels."""
    if extractor is None:
        from extractor import extract_skills

        extractor = extract_skills
    return [
        {item["skill"] for item in extractor(posting.get("description", ""), method="hybrid", threshold=threshold)}
        for posting in postings
    ]


def missing_skill_groups(
    student_skills: set[str],
    posting: dict[str, str],
    extracted_posting_skills: set[str],
) -> dict[str, list[str]]:
    """Report extracted posting skills not evidenced in the student profile.

    Required/preferred columns classify the extracted skills; they do not supply
    gap items. This prevents unmentioned ground-truth skills from appearing as
    profile gaps.
    """
    required_extracted = parse_skill_field(posting.get("required_skills")) & extracted_posting_skills
    preferred_extracted = parse_skill_field(posting.get("preferred_skills")) & extracted_posting_skills
    return {
        "required": sorted(required_extracted - student_skills),
        "preferred": sorted(preferred_extracted - student_skills),
    }


def weighted_match_score(
    student_skills: set[str],
    posting: dict[str, str],
    extracted_posting_skills: set[str],
    *,
    required_weight: float = REQUIRED_WEIGHT,
    preferred_weight: float = PREFERRED_WEIGHT,
) -> float:
    """Score coverage of extracted required/preferred skills; required is weighted higher."""
    if required_weight < 0 or preferred_weight < 0 or required_weight + preferred_weight <= 0:
        raise ValueError("Match weights must be non-negative and have a positive sum")
    required = parse_skill_field(posting.get("required_skills")) & extracted_posting_skills
    preferred = parse_skill_field(posting.get("preferred_skills")) & extracted_posting_skills
    components: list[tuple[float, float]] = []
    if required:
        components.append((required_weight, len(student_skills & required) / len(required)))
    if preferred:
        components.append((preferred_weight, len(student_skills & preferred) / len(preferred)))
    weight_sum = sum(weight for weight, _ in components)
    if not weight_sum:
        return 0.0
    return sum(weight * score for weight, score in components) / weight_sum


def rank_matcher(
    student_skills: set[str],
    postings: list[dict[str, str]],
    extracted_posting_skills: list[set[str]],
    *,
    top_k: int | None = None,
) -> list[tuple[float, int]]:
    """Return (score, posting index) in deterministic descending order."""
    if len(postings) != len(extracted_posting_skills):
        raise ValueError("One extracted skill set is required for every posting")
    scored = [
        (weighted_match_score(student_skills, posting, extracted_posting_skills[index]), index)
        for index, posting in enumerate(postings)
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored if top_k is None else scored[:top_k]
