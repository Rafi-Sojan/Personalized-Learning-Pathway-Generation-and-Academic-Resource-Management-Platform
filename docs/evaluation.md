# Evaluation and Acceptance Plan

**Document ID:** ILR-EVAL-001
**Version:** 2.0
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

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

`python scripts/evaluate_learning.py <benchmark.json>` evaluates a JSON array of cases. Each case may contain `mapping`, `roadmap`, `ranking`, and `historical_ranking` sections. The harness reports average mapping precision, roadmap completion rate, normal ranking hit rate, historical ranking hit rate, and case count. Historical exam ranking inputs should record source/year and concept coverage. It is intentionally deterministic and is suitable for CI regression fixtures once a reviewed, de-identified benchmark set is supplied.
