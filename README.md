# Skill-based internship matcher

This university project maps profile text and internship descriptions into a shared curated skill taxonomy, ranks postings with required skills weighted above preferred skills, compares a TF-IDF keyword baseline, and reports skills found in postings but not in a profile.

## Synthetic data notice

`data/internships.csv` and `data/students.csv` contain synthetic examples created for development and evaluation. They do not describe real employers, vacancies, students, or employment outcomes. The `required_skills`, `preferred_skills`, and `true_skills` columns are synthetic ground-truth labels generated from the taxonomy, not human-annotated judgments.

## Static website

The live demo is a static website. Matching, skill extraction, ranking, and gap reports run in the visitor's browser; profile text and PDF contents are not sent to a server. The browser reads the generated files under `web/data/`.

The static demo uses case-insensitive, word-boundary-safe matches against the skill taxonomy's canonical names and aliases. Its matcher uses the synthetic required/preferred labels only to classify extracted posting skills and apply the required/preferred weights. Gap items themselves must first have been extracted from the posting description. The baseline uses stopword-filtered unigram TF-IDF cosine similarity. The static demo does not run sentence-transformers; paraphrases that do not contain a taxonomy alias can be missed. The Python extractor and evaluator remain available for research and labeled evaluation.

Refresh browser data from the existing source files with `python src/export_static_data.py`. This exports the taxonomy and synthetic internship postings; it does not create or modify labels or metrics.

## Deploy on Vercel

The root `vercel.json` config selects the `Other` framework preset, serves the `web/` output directory, and skips dependency installation and a server build. In Vercel, set Root Directory to the repository root (`.`), disable custom Install Command and Build Command overrides, and deploy the latest commit. No API or Python packages are needed to serve the website. The PDF parser is loaded by the browser from the pinned PDF.js CDN package; PDFs are parsed locally and selectable text only is supported (image-only scans need OCR).

## Run the website locally

From the repository root, run `python src/export_static_data.py` after changing source data, then start a local static server with `python -m http.server 8000 --directory web`. Open `http://localhost:8000` in a browser. The PDF parser and styles use web resources, so use an internet connection while viewing the demo.

## Research scripts and evaluation

Install `requirements.txt` to use the Python sentence-transformer extractor and evaluation tools. The keyword baseline lowercases and tokenizes technical terms, removes English and project boilerplate stopwords, then ranks with unigram TF-IDF cosine similarity. The weighted matcher gives required skills more weight than preferred skills. Treat gaps as suggestions for review, not claims about a student's actual ability.

Run `python src/evaluate.py --tune --regenerate-templates` to create a synthetic development split disjoint from the human-evaluation student sample, tune the embedding threshold using only that synthetic development split, and regenerate blank label templates. The command refuses to overwrite any existing label or annotator entries. Fill the label and annotator columns by hand, then run `python src/evaluate.py` to compute metrics from those annotations. Successful evaluation writes `results/metrics.json` and an identical `web/metrics.json` for the static Results tab. Until this happens, the website displays “Evaluation not run yet”; no labels or metrics are generated as placeholders.
