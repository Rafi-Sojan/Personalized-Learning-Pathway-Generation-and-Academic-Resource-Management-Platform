# Evaluation and Acceptance Plan

**Document ID:** ILR-EVAL-001
**Version:** 2.3
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-07

## 1. Learning quality

| Area | Measures | Evidence required |
|---|---|---|
| Concept mapping | Precision, recall, F1, human validation | Labeled syllabus/concept set and review protocol |
| Prerequisite graph | Cycle rate, ordering correctness, expert agreement | Curated dependency benchmark |
| Roadmap quality | Completion rate, time-estimation error, deadline feasibility | Anonymized learner sessions and schedule outcomes |
| Ranking quality | Hit rate, NDCG, instructor agreement | Instructor-selected relevance set |
| Adaptation | Mastery change after quizzes and progress updates | Before/after learner state analysis |

## 2. Product acceptance

Acceptance requires authenticated route coverage, ownership isolation, upload validation, migration verification, frontend production build, ML unit tests, native scorer tests, historical-question import checks, role checks, privacy workflows, and documented operational procedures. Security, privacy, accessibility, and performance acceptance still require release-owner approval and environment-specific evidence before production deployment.

## 3. Evaluation controls

Evaluation data must be versioned, de-identified where possible, and separated from production learner records. Metrics must be reported with dataset scope, baseline comparison, confidence or error bounds where meaningful, and known limitations. A model or heuristic change requires a before/after comparison and rollback decision.

## 4. Reproducible benchmark harness

`python scripts/evaluate_learning.py <benchmark.json>` evaluates a JSON array of cases. Each case may contain `mapping`, `concept_matching`, `roadmap`, `ranking`, and `historical_ranking` sections. A `concept_matching` case supplies raw prompt text, candidate concept records, expected concept IDs (or `null` for required abstention), and an optional expected status. The harness invokes the matcher itself; it does not trust a pre-filled prediction.

Reported matcher measures are exact accuracy, accepted-match precision, mapped-case recall/F1, coverage, abstention accuracy, status accuracy, and mean reciprocal rank. The release gate requires matcher precision, F1, and abstention accuracy of at least `0.90` on the source-controlled regression fixture, in addition to the existing mapping F1 and ranking NDCG gates. Coverage is reported but not thresholded so CI does not reward unsafe forced matching.

The eight supplied matcher cases test specificity, generic labels, derived acronyms, two-topic ambiguity, no-evidence abstention, hierarchy context, same-name ambiguity, and OCR/spelling damage. They are synthetic engineering regressions and produced perfect scores on 2026-11-07. They are deliberately small and are not evidence of RVCE academic accuracy, population validity, calibration, fairness, or production quality. EVAL-01 remains open until an authorized, versioned, de-identified, academically annotated corpus and acceptance thresholds exist.

## 5. Chronological historical-frequency evaluation

`ml.evaluation.chronological_ranking.evaluate_chronological_frequency` uses an expanding-window evaluation. For each held-out year it ranks concepts using only verified historical records from earlier years, then reports Hit Rate@K and NDCG@K against topics occurring in the held-out year. Unmapped rows and invalid years are ignored. The result includes per-year metrics and macro means, making temporal leakage visible. This offline evaluator is a metric utility; it does not claim predictive validity without a representative, academically reviewed multi-year paper archive.

## 6. Supplied-layout conformance checks

The 2026-11-07 implementation pass used two supplied PDFs as read-only layout checks. The combined 20-page CIE/scheme/SEE packet declares `21CS45`, yielded 64 questions (19 quiz and 45 main; 32 CIE/test and 32 SEE), and contributed no scheme/solution prompts. The selected `AI253IA` section of the separate supplied 96-page AI/ML scheme yielded 106 concepts (19 roots and 87 children) and no outcome, lab, rubric, or marks-distribution concepts. These files represent different courses and are intentionally rejected if an operator attempts to combine them under one course record.

These counts are regression anchors for the current parser and the observed files. They do not supply expected-row annotations, precision/recall, topic-mapping agreement, source authorization, multi-year frequency validity, or expert approval. APP-01, APP-02, and EVAL-01 therefore remain open.
