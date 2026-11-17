"""Export the existing synthetic source data for the static browser demo."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WEB_DATA_DIR = ROOT / "web" / "data"


def main() -> None:
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    skills = json.loads((DATA_DIR / "skills.json").read_text(encoding="utf-8"))
    with (DATA_DIR / "internships.csv").open(newline="", encoding="utf-8-sig") as stream:
        internships = list(csv.DictReader(stream))

    (WEB_DATA_DIR / "skills.json").write_text(
        json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (WEB_DATA_DIR / "internships.json").write_text(
        json.dumps(internships, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    metrics_path = ROOT / "results" / "metrics.json"
    if metrics_path.exists():
        (ROOT / "web" / "metrics.json").write_bytes(metrics_path.read_bytes())
    print(f"Exported existing taxonomy and {len(internships)} synthetic postings to web/data/")


if __name__ == "__main__":
    main()
