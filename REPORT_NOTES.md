# Evaluation report notes

## Pipeline

The data generator writes synthetic student profiles and internship descriptions. The curated taxonomy in `data/skills.json` maps text to canonical skills. The extractor combines case-insensitive, word-boundary alias matching with phrase-level embeddings from `all-MiniLM-L6-v2`; hybrid extraction keeps the higher confidence for duplicate canonical skills.

The matcher is implemented in `src/matcher.py`. It extracts posting skills from each description, classifies only those extracted skills as required or preferred, and scores student coverage with required skills weighted above preferred skills. The baseline is implemented in `src/baseline.py`: it lowercases and tokenizes profile and posting title/description text, retains technical forms such as C++, C#, and Node.js, removes scikit-learn English stopwords plus project boilerplate, creates unigram TF-IDF vectors with L2 normalization, and ranks by cosine similarity.

Gap reports are derived only from skills extracted from the posting description. The required/preferred columns classify these extracted skills; skills in those columns that the extractor did not find are not reported as gaps. Gaps say that a skill was not evidenced in the profile text, not that the student lacks it.

`src/evaluate.py` produces pooled, shuffled top-five relevance judgments, manually annotated extraction documents, and gap usefulness ratings. It computes human evaluation metrics only after labels and annotator names are complete. The deployed demo is static: `web/app.js` loads exported taxonomy/postings JSON and runs dictionary extraction, weighted skill ranking, gap reporting, and a stopword-filtered TF-IDF baseline in the browser. The separate Python extractor and evaluator retain embedding-based hybrid extraction for research evaluation. PDF.js extracts selectable PDF text on the user's device.

## Design choices and threshold

- The evaluation sample and development split are reproducibly selected from different student records. The current synthetic dev split and the human-evaluation students are disjoint.
- `--tune` evaluates the threshold grid using only `results/dev_split_synthetic.csv` and its generated `synthetic_true_skills`. Its objective is micro-F1; ties select the stricter cutoff. The held-out evaluation students and human-label sheets are not used for tuning.
- The selected embedding threshold is recorded in `results/evaluation_config.json`; the Python evaluator reads it by default unless `--threshold` overrides it. The static browser demo does not use an embedding threshold because it matches curated aliases.
- Relevance, extraction, and gap-rating templates each include a blank `annotator` field. Evaluation records distinct annotator counts from completed templates; annotator entries are blank at present, so no actual annotator count is available.

## Limitations and current evaluation state

- All student and internship content is synthetic and template-generated. Synthetic `true_skills`, `required_skills`, and `preferred_skills` are useful for development but do not represent human judgments or real labor-market language.
- The current planned human evaluation is small: the relevance sheet has 500 candidate judgments across 50 evaluation students, and the extraction and gap sheets each contain 50 rows. All label and annotator fields are currently blank, and `results/metrics.json` has not been produced. No human Precision@5, extraction F1, or gap usefulness result is available.
- The synthetic dev split contains 50 students and has no student IDs in common with the 50-student human-evaluation sample. It is used only for threshold selection; its generated-label micro-F1 is not a human evaluation result.
- The annotator count is unknown until the templates are completed. The sheets capture annotator names but do not yet contain inter-annotator agreement or adjudication fields.
- TF-IDF is a lexical baseline and may miss paraphrases. The matcher depends on extraction quality and the synthetic posting skill classification. Both ranker scores are ranking signals, not probabilities.
- Threshold tuning uses generated development labels. It may overfit the synthetic writing patterns and should not be presented as validation on real students.
- The public static demo does not run sentence-transformer embeddings. It uses literal taxonomy aliases, so paraphrased skills may be missed. PDF scanning supports selectable text; image-only documents need OCR, which is not provided.

## Failure cases from evaluated results

No failure cases can yet be cited from actual human evaluation: all label fields are blank and no human-evaluation metrics exist. The entries below are intentionally empty. After completing the human labels and running `python src/evaluate.py`, replace these rows with five concrete mismatches, citing the profile/posting and label evidence. Do not infer cases from generated labels alone.

| Evidence (file and row or IDs) | Matcher output | Human judgment / expected skills | Observed failure |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
