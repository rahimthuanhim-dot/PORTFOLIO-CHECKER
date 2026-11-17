"""FastAPI endpoints and static UI for the synthetic internship matcher."""

from __future__ import annotations

import csv
import json
import sys
from io import BytesIO
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_FILE = ROOT / "results" / "metrics.json"
WEB_DIR = ROOT / "web"
MAX_RESUME_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 100
sys.path.insert(0, str(ROOT / "src"))

from baseline import rank_baseline  # noqa: E402
from extractor import extract_skills  # noqa: E402
from matcher import extract_posting_skill_sets, missing_skill_groups, rank_matcher  # noqa: E402


app = FastAPI(title="Skill-based Internship Matcher", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class MatchRequest(BaseModel):
    profile_text: str = Field(min_length=1, description="Free-text student profile")
    threshold: float | None = Field(default=None, ge=0.0, le=1.0, description="Embedding similarity threshold; defaults to the evaluator's saved threshold")


def _configured_threshold(requested: float | None) -> float:
    if requested is not None:
        return requested
    config_path = ROOT / "results" / "evaluation_config.json"
    if config_path.exists():
        try:
            configured = float(json.loads(config_path.read_text(encoding="utf-8"))["similarity_threshold"])
            if 0.0 <= configured <= 1.0:
                return configured
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            pass
    return 0.55


def _read_internships() -> list[dict[str, str]]:
    path = DATA_DIR / "internships.csv"
    if not path.exists():
        raise FileNotFoundError(f"Internship data not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


@lru_cache(maxsize=4)
def _internship_vectors(threshold: float) -> tuple[list[dict[str, str]], list[set[str]]]:
    """Extract posting vectors once; all text is from the explicitly synthetic CSV."""
    postings = _read_internships()
    vectors = extract_posting_skill_sets(postings, threshold, extract_skills)
    return postings, vectors


def _posting_result(index: int, posting: dict[str, str], score: float, detected: set[str], posting_skills: set[str]) -> dict[str, Any]:
    gaps = missing_skill_groups(detected, posting, posting_skills)
    required_missing = gaps["required"]
    preferred_missing = gaps["preferred"]
    required_summary = ", ".join(required_missing) if required_missing else "None detected"
    preferred_summary = ", ".join(preferred_missing) if preferred_missing else "None detected"
    return {
        "internship_id": f"I{index + 1:06d}",
        "title": posting.get("title", ""),
        "company": posting.get("company", ""),
        "description": posting.get("description", ""),
        "score": round(float(score), 4),
        "extracted_posting_skills": sorted(posting_skills),
        "gap_report": (
            "Skills extracted from the posting but not evidenced in the profile — "
            f"required: {required_summary}; preferred: {preferred_summary}."
        ),
        "missing_required_skills": required_missing,
        "missing_preferred_skills": preferred_missing,
    }


@app.post("/match")
def match(request: MatchRequest) -> dict[str, Any]:
    profile = request.profile_text.strip()
    if not profile:
        raise HTTPException(status_code=422, detail="profile_text must contain non-whitespace text")
    return _match_profile(profile, _configured_threshold(request.threshold))


def _match_profile(profile: str, threshold: float) -> dict[str, Any]:
    try:
        extracted = extract_skills(profile, method="hybrid", threshold=threshold)
        postings, posting_vectors = _internship_vectors(threshold)
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Could not load matcher data or model: {exc}") from exc

    profile_skills = {item["skill"] for item in extracted}
    matcher_order = rank_matcher(profile_skills, postings, posting_vectors, top_k=5)
    baseline_order = rank_baseline(profile, postings, top_k=5)
    matcher_rows = [_posting_result(index, postings[index], score, profile_skills, posting_vectors[index]) for score, index in matcher_order]
    baseline_rows = [_posting_result(index, postings[index], score, profile_skills, posting_vectors[index]) for score, index in baseline_order]
    return {
        "extracted_skills": extracted,
        "matcher": matcher_rows,
        "baseline": baseline_rows,
        "synthetic_data": True,
        "threshold": threshold,
        "score_definitions": {
            "matcher": "Required/preferred skill coverage over hybrid-extracted posting skills; required weight 0.7, preferred weight 0.3",
            "baseline": "Stopword-filtered unigram TF-IDF cosine similarity over profile and posting title/description",
        },
    }


def _extract_pdf_text(filename: str | None, content: bytes) -> str:
    if not filename or Path(filename).suffix.casefold() != ".pdf":
        raise HTTPException(status_code=415, detail="Upload a PDF file with a .pdf extension")
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds the maximum upload size")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file does not have a valid PDF signature")
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content), strict=False)
        if len(reader.pages) > MAX_PDF_PAGES:
            raise HTTPException(status_code=413, detail="PDF exceeds the maximum supported page count")
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read text from this PDF: {exc}") from exc
    if not text:
        raise HTTPException(
            status_code=422,
            detail="No selectable text was found. Image-only scanned PDFs need OCR, which is not enabled in this app.",
        )
    return text


@app.post("/match/upload")
async def match_upload(
    resume: UploadFile = File(..., description="PDF resume with selectable text"),
    threshold: float | None = Form(default=None, ge=0.0, le=1.0),
) -> dict[str, Any]:
    try:
        content = await resume.read(MAX_RESUME_BYTES + 1)
        extracted_text = _extract_pdf_text(resume.filename, content)
        result = _match_profile(extracted_text, _configured_threshold(threshold))
        result["input_source"] = "pdf_resume"
        result["filename"] = Path(resume.filename or "resume.pdf").name
        return result
    finally:
        await resume.close()


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    if not RESULTS_FILE.exists():
        raise HTTPException(status_code=404, detail="Evaluation not run yet")
    try:
        with RESULTS_FILE.open(encoding="utf-8") as stream:
            content = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Could not read metrics file: {exc}") from exc
    if not isinstance(content, dict):
        raise HTTPException(status_code=500, detail="Metrics file must contain a JSON object")
    return content


if not WEB_DIR.exists():
    WEB_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
