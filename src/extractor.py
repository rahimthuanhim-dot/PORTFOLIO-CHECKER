"""Skill extraction by curated aliases, sentence embeddings, or both.

Embedding mode requires ``sentence-transformers`` and downloads/loads the
``all-MiniLM-L6-v2`` model through that package on first use.
"""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_SKILLS_PATH = Path(__file__).resolve().parents[1] / "data" / "skills.json"
DEFAULT_MODEL = "all-MiniLM-L6-v2"


def _load_skills(skills_path: str | Path = DEFAULT_SKILLS_PATH) -> list[dict[str, Any]]:
    """Load and minimally validate the shared taxonomy."""
    path = Path(skills_path)
    with path.open(encoding="utf-8") as stream:
        skills = json.load(stream)
    if not isinstance(skills, list):
        raise ValueError(f"Expected a list of skills in {path}")
    for entry in skills:
        if not isinstance(entry, dict) or not isinstance(entry.get("canonical_name"), str):
            raise ValueError(f"Invalid skill entry in {path}: {entry!r}")
        if not isinstance(entry.get("aliases", []), list):
            raise ValueError(f"Aliases must be a list for {entry['canonical_name']!r}")
    return skills


def _terms_for(entry: dict[str, Any]) -> list[str]:
    """Return distinct canonical name and aliases, preserving their order."""
    terms = [entry["canonical_name"], *entry.get("aliases", [])]
    seen: set[str] = set()
    result = []
    for term in terms:
        if isinstance(term, str) and term.strip() and term.casefold() not in seen:
            seen.add(term.casefold())
            result.append(term.strip())
    return result


def _alias_pattern(alias: str) -> re.Pattern[str]:
    # Allow flexible whitespace in multiword aliases but otherwise match the
    # literal alias. Unicode-aware \w boundaries prevent matching inside words.
    escaped = r"\s+".join(re.escape(part) for part in alias.strip().split())
    return re.compile(rf"(?<!\w){escaped}(?!\w)", flags=re.IGNORECASE)


def extract_dictionary(
    text: str,
    skills: list[dict[str, Any]] | None = None,
    *,
    skills_path: str | Path = DEFAULT_SKILLS_PATH,
) -> dict[str, float]:
    """Match canonical names and aliases with case-insensitive word boundaries.

    Overlapping matches are resolved in favor of the longest alias. A matching
    skill receives confidence 1.0 because this method reports literal evidence.
    """
    if not isinstance(text, str) or not text.strip():
        return {}
    taxonomy = skills if skills is not None else _load_skills(skills_path)
    matches: list[tuple[int, int, int, str]] = []
    for entry in taxonomy:
        canonical = entry["canonical_name"]
        for alias in _terms_for(entry):
            pattern = _alias_pattern(alias)
            for found in pattern.finditer(text):
                matches.append((found.start(), found.end(), len(alias), canonical))

    # Resolve span collisions globally so e.g. a multiword skill supersedes a
    # shorter contained term. Equal-span aliases can still yield distinct skills.
    accepted: list[tuple[int, int, int, str]] = []
    for match in sorted(matches, key=lambda item: (-(item[2]), item[0], item[3])):
        start, end, _, canonical = match
        if any(start < other_end and other_start < end for other_start, other_end, _, _ in accepted):
            continue
        accepted.append(match)
    return {canonical: 1.0 for _, _, _, canonical in sorted(accepted, key=lambda item: item[0])}


def _split_phrases(text: str) -> list[str]:
    """Split prose into short candidate phrases without dropping abbreviations."""
    parts = re.split(r"[\n\r;.!?]+|,(?=\s)|\s+\band\b\s+|\s+\bwith\b\s+", text, flags=re.IGNORECASE)
    phrases = [re.sub(r"\s+", " ", part).strip(" \t:-–—") for part in parts]
    # Ignore very short fragments and cap pathological inputs before encoding.
    return [phrase for phrase in phrases if len(phrase) >= 2][:250]


@lru_cache(maxsize=2)
def _embedding_resources(model_name: str, skills_path: str) -> tuple[Any, list[dict[str, Any]], list[str], list[str], Any]:
    """Cache the model and normalized taxonomy-term embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "Embedding extraction requires sentence-transformers. Install it with "
            "`pip install sentence-transformers`."
        ) from exc

    import numpy as np

    taxonomy = _load_skills(skills_path)
    terms: list[str] = []
    owners: list[str] = []
    for entry in taxonomy:
        for term in _terms_for(entry):
            terms.append(term)
            owners.append(entry["canonical_name"])
    model = SentenceTransformer(model_name)
    vectors = model.encode(terms, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return model, taxonomy, terms, owners, np.asarray(vectors)


def extract_embeddings(
    text: str,
    *,
    threshold: float = 0.55,
    skills_path: str | Path = DEFAULT_SKILLS_PATH,
    model_name: str = DEFAULT_MODEL,
) -> dict[str, float]:
    """Match text phrases to the closest canonical name/alias by cosine similarity.

    ``threshold`` is a cosine similarity cutoff for accepting a match. The
    returned confidence is the highest phrase-to-alias similarity per skill.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    phrases = _split_phrases(text) if isinstance(text, str) else []
    if not phrases:
        return {}

    import numpy as np

    path_key = str(Path(skills_path).resolve())
    model, _, _, owners, term_vectors = _embedding_resources(model_name, path_key)
    phrase_vectors = model.encode(phrases, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    similarities = np.asarray(phrase_vectors) @ term_vectors.T
    scores: dict[str, float] = {}
    for phrase_scores in similarities:
        best_by_skill: dict[str, float] = {}
        for index, similarity in enumerate(phrase_scores):
            skill = owners[index]
            score = float(similarity)
            if score > best_by_skill.get(skill, -1.0):
                best_by_skill[skill] = score
        for skill, score in best_by_skill.items():
            if score >= threshold and score > scores.get(skill, -1.0):
                scores[skill] = score
    return dict(sorted(scores.items(), key=lambda item: (-item[1], item[0])))


def extract_skills(
    text: str,
    method: str = "hybrid",
    *,
    threshold: float = 0.55,
    skills_path: str | Path = DEFAULT_SKILLS_PATH,
    model_name: str = DEFAULT_MODEL,
) -> list[dict[str, Any]]:
    """Return canonical skill predictions as ``[{skill, confidence}, ...]``.

    ``dictionary`` uses literal case-insensitive alias matching, ``embedding``
    uses phrase embeddings, and ``hybrid`` merges both (keeping the stronger
    confidence for duplicate skills). Embedding confidences are cosine
    similarities; literal dictionary matches receive confidence 1.0.
    """
    method = method.casefold().strip()
    if method not in {"dictionary", "embedding", "hybrid"}:
        raise ValueError("method must be 'dictionary', 'embedding', or 'hybrid'")
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    results: dict[str, float] = {}
    if method in {"dictionary", "hybrid"}:
        results.update(extract_dictionary(text, skills_path=skills_path))
    if method in {"embedding", "hybrid"}:
        embedded = extract_embeddings(text, threshold=threshold, skills_path=skills_path, model_name=model_name)
        for skill, confidence in embedded.items():
            results[skill] = max(confidence, results.get(skill, -1.0))
    return [
        {"skill": skill, "confidence": round(confidence, 4)}
        for skill, confidence in sorted(results.items(), key=lambda item: (-item[1], item[0]))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract taxonomy skills from a text sample.")
    parser.add_argument("text", nargs="*", help="Text to analyze; a demo sample is used when omitted.")
    parser.add_argument("--method", choices=["dictionary", "embedding", "hybrid"], default="hybrid")
    parser.add_argument("--threshold", type=float, default=0.55, help="Embedding cosine similarity cutoff.")
    args = parser.parse_args()
    sample = "Built REST services in Python and JavaScript, analyzed product data with SQL, and collaborated with designers."
    text = " ".join(args.text) if args.text else sample
    print(json.dumps(extract_skills(text, method=args.method, threshold=args.threshold), indent=2))


if __name__ == "__main__":
    main()
