"""Stopword-filtered TF-IDF cosine keyword baseline."""

from __future__ import annotations

import re
from typing import Any

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_STOP_WORDS = {
    "synthetic", "posting", "profile", "intern", "internship", "student", "team", "teams",
    "work", "worked", "working", "project", "projects", "experience", "hands", "skill", "skills",
    "built", "build", "help", "learn", "learning", "used", "using",
}
STOP_WORDS = frozenset(word.casefold() for word in ENGLISH_STOP_WORDS) | PROJECT_STOP_WORDS
TOKEN_PATTERN = re.compile(r"(?u)[a-zA-Z0-9][a-zA-Z0-9_+#.]*")


def preprocess_text(text: str) -> list[str]:
    """Lowercase, tokenize words/technical forms, and remove English/project stopwords.

    Unigrams are used; punctuation inside forms such as C++, C#, and Node.js is
    retained. Single-letter C and R are kept as useful programming-language terms.
    """
    tokens = (token.casefold() for token in TOKEN_PATTERN.findall(text or ""))
    return [token for token in tokens if token not in STOP_WORDS and (len(token) > 1 or token in {"c", "r"})]


def rank_baseline(
    profile_text: str,
    postings: list[dict[str, str]],
    *,
    top_k: int | None = None,
) -> list[tuple[float, int]]:
    """Rank postings by unigram TF-IDF cosine similarity to the profile."""
    documents = [profile_text] + [" ".join((posting.get("title", ""), posting.get("description", ""))) for posting in postings]
    vectorizer = TfidfVectorizer(
        tokenizer=preprocess_text,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        norm="l2",
    )
    try:
        matrix = vectorizer.fit_transform(documents)
        scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel().tolist()
    except ValueError as exc:
        if "empty vocabulary" not in str(exc).lower():
            raise
        scores = [0.0] * len(postings)
    ranked = [(float(score), index) for index, score in enumerate(scores)]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked if top_k is None else ranked[:top_k]
