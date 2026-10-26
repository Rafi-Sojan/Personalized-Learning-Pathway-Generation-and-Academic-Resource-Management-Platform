# Evaluation and Acceptance Plan

**Document ID:** ILR-EVAL-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Learning quality

| Area | Measures | Evidence required |
|---|---|---|
| Concept mapping | Precision, recall, F1, human validation | Labeled syllabus/concept set and review protocol |
| Prerequisite graph | Cycle rate, ordering correctness, expert agreement | Curated dependency benchmark |
| Roadmap quality | Completion rate, time-estimation error, deadline feasibility | Anonymized learner sessions and schedule outcomes |
| Ranking quality | Hit rate, NDCG, instructor agreement | Instructor-selected relevance set |
| Adaptation | Mastery change after quizzes and progress updates | Before/after learner state analysis |

## 2. Product acceptance

Acceptance requires authenticated route coverage, ownership isolation, upload validation, migration verification, frontend production build, ML unit tests, native scorer tests, and documented operational procedures. Security, privacy, accessibility, and performance acceptance criteria remain to be defined before production approval.

## 3. Evaluation controls

Evaluation data must be versioned, de-identified where possible, and separated from production learner records. Metrics must be reported with dataset scope, baseline comparison, confidence or error bounds where meaningful, and known limitations. A model or heuristic change requires a before/after comparison and rollback decision.
