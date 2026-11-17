# Skill-based internship matcher data

## Synthetic data notice

`data/internships.csv` and `data/students.csv` contain synthetic examples created for development and evaluation. They do not describe real employers, vacancies, students, or employment outcomes. The `required_skills`, `preferred_skills`, and `true_skills` columns are synthetic ground-truth labels generated from the taxonomy; they are not human-annotated judgments.

## Generation

Run `python src/generate_data.py` from the project root. The script uses a fixed random seed for reproducible output, writes `data/skills.json` from the curated taxonomy in the script, and creates varied paraphrased descriptions and profiles alongside pipe-separated ground-truth skill names. The skill taxonomy contains canonical names, categories, and aliases. Generated prose is intentionally varied, but is template-based synthetic text rather than collected language.

## Run the app

Install project dependencies with `python -m pip install -r requirements.txt`, then start the API and static frontend from the project root with `python -m uvicorn api.main:app --reload`. Open the local server URL printed by Uvicorn. The demo accepts pasted text through `POST /match` or a PDF resume through `POST /match/upload`. PDF text is extracted in memory and not saved. PDFs with no selectable text need OCR, which is not enabled. The Results tab fetches `GET /metrics` and displays “Evaluation not run yet” until `results/metrics.json` has been produced from completed human-label templates.

The matcher weights extracted required skills above extracted preferred skills. The keyword baseline lowercases and tokenizes technical terms, removes English and project boilerplate stopwords, then ranks with unigram TF-IDF cosine similarity. Gap reports only include skills extracted from the posting description and classified as required or preferred; they do not add unmentioned ground-truth skills. Treat gaps as suggestions for review, not claims about a student's actual ability.

Run `python src/evaluate.py --tune --regenerate-templates` to create a synthetic development split disjoint from the human-evaluation student sample, tune the embedding threshold against that development split's synthetic `true_skills`, and regenerate blank label templates. The command refuses to overwrite any existing label or annotator entries. Fill all label columns and annotator names by hand, then rerun `python src/evaluate.py` to compute evaluation metrics.
