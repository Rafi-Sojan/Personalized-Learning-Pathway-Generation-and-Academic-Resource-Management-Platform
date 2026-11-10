# ML, Scheduling, and Scoring Design Specification

**Document ID:** ILR-ML-001
**Version:** 3.1
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-10

## 1. Purpose

The learning logic converts source-backed syllabus and question-paper information into reviewable concept suggestions and explainable roadmaps. The implementation favors deterministic, offline behavior over an opaque or network-dependent model. It is an engineering baseline, not an academically validated RVCE model.

## 2. Processing pipeline

```text
syllabus text/PDF
        |
        v
preprocessing -> topic extraction -> concept matching
        |                         |
        v                         v
dependency graph ----------> validation and crosswalk
        |
        v
reviewed workload profile -> hard unit/dependency ordering
        |
        v
evidence/mastery priority -> typed activity demands -> balanced calendar scheduling
        |
        v
API response and persisted study plan
```

## 3. Module responsibilities

| Module | Responsibility |
|---|---|
| `ml/preprocessing` | Text extraction, OCR boundary, and question parsing |
| `ml/concept_mapping` | Cleaning, topic classification, semantic matching, and mapping validation |
| `ml/graph` | Prerequisite graph construction, ordering, prioritization, and syllabus crosswalk |
| `ml/scheduling` | Time estimates, deadline-aware scheduling, and schedule optimization |
| `ml/evaluation` | Mapping, roadmap, and ranking metrics |
| `backend/app/services` | API-facing orchestration and persistence |
| `backend/app/integrations` | Backend boundary for ML and scoring calls |
| `scoring-engine` | Native C++ ranking primitive and command-line demonstration |

## 4. Hybrid concept matcher

Historical-question attribution uses matcher version `rvce-hybrid-lexical-v2`. One matcher is built for the verified concepts in the selected course and reused for every question in an import. The feature ensemble is:

1. Unicode NFKC normalization, technical punctuation normalization, conservative morphology, and removal of common examination-command words.
2. Corpus-aware BM25-style term rarity so specific syllabus phrases outrank generic parent labels.
3. Token-boundary full-phrase and alias matching, plus acronyms derived from the syllabus wording rather than a fabricated global taxonomy.
4. Character trigram similarity over phrase-sized windows to tolerate bounded OCR and spelling damage.
5. Parent-topic and unit context to distinguish repeated labels in different syllabus hierarchies.

The default acceptance score is `0.62`. A normal match must exceed the runner-up by `0.08`; a score of at least `0.88` may use a `0.04` margin. The matcher returns `matched`, `ambiguous`, `low_confidence`, `no_candidates`, or `no_evidence`. An ambiguous or weak result has no `concept_id`. The numeric score is a deterministic relevance score, not a calibrated probability.

Matching work is capped at the first 512 normalized prompt tokens before character-window scoring. The complete source prompt remains stored unchanged. If decisive wording occurs only outside the scoring bound, the safe outcome is an abstention followed by human review.

Each imported row stores bounded metadata containing the decision status, algorithm version, margin, explanation, and up to five ranked candidates. Prompt text is not duplicated in this metadata. The learner review interface displays the evidence, while the row remains `pending_review`. Human assignment records `human-review` provenance and confidence `1.0`; clearing a mapping records an explicit human decision.

## 5. Source-aware map identity

Concept reuse uses normalized name, printed unit, and parent heading. Same-named topics in different units or under different parents remain separate nodes. A topic name that occurs only once in the new source may reuse one prior concept across syllabus versions so learner progress survives a publisher moving the topic. Parent links and explicit prerequisite candidates are resolved only when the current source contains an unambiguous target.

## 6. Course-aware roadmap model

Concept ordering uses `rvce-evidence-priority-v2`; persisted activity sessions use `rvce-activity-roadmap-v3`. Printed unit sequence and accepted prerequisites are hard constraints. A dependency that requires a later unit before an earlier unit produces a reviewable error. Within the currently eligible unit, the bounded score combines reviewed historical evidence (38%), learner mastery gap (30%), downstream concepts unlocked (17%), and concept difficulty (15%). Historical evidence is recency- and marks-weighted and saturates rather than growing without bound.

Map generation extracts a reviewable course profile containing course aliases, category, L:T:P credits, L/T/P/EL hours, ordered unit hours and source pages, CIE-only unit declarations, outcomes, assessment components/format, and CIE/SEE marks where printed. Inconsistent totals are retained as issues. A profile with extracted metadata cannot control a persisted plan until it is verified; reviewer modality-hour, unit-hour, course-type, and unit-scope corrections are stored with notes and an audit event.

Verified workload is distributed across ordered concepts by unit-hour weight. If explicit hours are unavailable, the scheduler uses unit hours and then a bounded difficulty fallback. Mastery adapts the concept estimate: scores at or above 85, 70, and 50 use factors 0.55, 0.72, and 0.90; scores below 30 use 1.15. Full-term, CIE, SEE, and revision modes apply factors 1.00, 0.55, 0.45, and 0.30. Every result remains at least ten minutes.

Course type selects an explainable activity mix:

| Course type | Representative activities |
|---|---|
| Theory | Learn, application, retrieval, review |
| Numerical theory | Learn, worked examples, problem practice, retrieval |
| Theory/lab | Learn, experiential application, lab practice, lab review |
| Programming | Learn, code-along, coding practice, mini-project, retrieval |
| Project | Plan, prototype, test, document, demonstrate |
| CAD/graphics | Learn, guided drawing, CAD practice, mock drawing |
| Language | Diagnostic, listening, speaking, reading, writing, retrieval |
| Objective HSS | Learn, case study, retrieval, mock objective test |
| Health/practice | Learn, guided practice, demonstration, reflection |

Part A/quiz evidence is attached to retrieval or mock-objective activities. Verified Part B/main evidence affects priority and supports other exam-oriented activities. SEE mode excludes a reviewed `cie_only` unit from both coverage and final revision; CIE mode similarly excludes a reviewed `see_only` unit. Missing scope never creates an exclusion.

The calendar accepts inclusive start/target dates, daily capacity, unavailable weekdays, and reserved end-of-plan revision minutes. Each activity is split into at most 60-minute sessions. Semester plans round-robin explicit same-scope course queues while preserving each course's internal unit/activity order. A persisted plan must fit completely; previews may return a clearly disclosed partial allocation.

The weight values are transparent product heuristics. They have not been calibrated against RVCE learner outcomes and must remain versioned when changed.

## 7. Explainability requirements

Each recommendation should be attributable to available evidence such as prerequisite status, learner progress, estimated effort, deadline proximity, or resource relevance. Production model adoption must define input features, model version, confidence, fallback behavior, and evaluation thresholds before it replaces deterministic logic.

## 8. Current implementation status

- Text cleaning, topic extraction, graph ordering, scheduling, and metric primitives are implemented and tested.
- PDF text extraction is supported through the backend processing path.
- OCR is integrated as an optional Tesseract/PyMuPDF provider and is invoked only for image-only documents when enabled. Its dependencies are deliberately excluded from the base API image and must be supplied by a dedicated OCR-enabled image/provider with binary patching and worker metrics.
- Concept matching is corpus-aware, acronym-aware, OCR-tolerant, hierarchy-aware, and abstention-capable. It remains a deterministic baseline pending a representative, authorized, human-annotated RVCE benchmark.
- The C++ scorer is independently testable and exposes a line-oriented stdin contract. The backend uses the native executable when `SCORING_ENGINE_PATH` is configured; the Python fallback now applies the same difficulty, mastery-gap, prerequisite-readiness multiplier, and descending ordering contract.
- Roadmap estimates are never capped to one day. Concepts that exceed remaining daily capacity are split into ordered sessions, persisted plans require capacity for the complete estimate, and previews may show a clearly labeled partial allocation.
- Course/semester generation, course-profile review, assessment-mode filtering, typed activities, explicit revision time, unavailable weekdays, and mastery feedback are implemented. Their academic workload quality remains subject to APP-04 review.
- Stored syllabus copies are processed into bounded, page-tagged text; a conservative unit/module/chapter parser creates source-aware topic candidates and links them to a syllabus version. The baseline does not infer prerequisite edges from headings or ordering. Topic quality and completeness still require review against the applicable RVCE syllabus.
- Historical exam imports accept text or PDF, preserve Part A quiz items and Part B main questions separately, associate prompts only with verified same-course concepts through the v2 matcher, and calculate topic frequency/rankings from verified main questions only. The archive reports quiz counts separately.
- The historical-question topic association is best-effort and must be evaluated against RVCE papers before its frequency totals are treated as authoritative. Scanned PDFs require OCR to be enabled.
- AI-generated website recommendations for concepts are deferred. A provider, server-side key configuration, URL verification policy, and recommendation-quality evaluation remain future work.
- Background document processing, bounded PDF/OCR extraction, computed matching evaluation, and native scorer integration are implemented. External embeddings or model serving are not selected. Introducing one requires an authorized labeled dataset, model/license/version record, offline fallback, privacy and threat review, before/after evaluation, and rollback criteria.

## 9. Safety and quality constraints

- Reject cyclic prerequisite graphs before generating a plan.
- Reject accepted dependencies that reverse reviewed source-unit order.
- Never allow an unreviewed extracted workload profile or inferred elective choice to control a persisted plan.
- Bound input size and processing time for uploaded or extracted text.
- Do not treat generated mappings as authoritative without validation.
- Preserve the source syllabus and mapping version when results affect a persisted roadmap.
- Keep page and unit provenance attached to concept records so learners and reviewers can trace each extracted item to its source copy.
- Record evaluation data without exposing learner-identifying information unnecessarily.
- Never convert a relevance score or synthetic-regression result into an academic-validity claim.
