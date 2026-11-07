# ML, Scheduling, and Scoring Design Specification

**Document ID:** ILR-ML-001
**Version:** 2.2
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-06

## 1. Purpose

The learning logic converts syllabus and concept information into explainable recommendations. The current implementation favors deterministic, testable utilities over opaque model behavior.

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
prioritization -> time estimation -> roadmap scheduling
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

## 4. Explainability requirements

Each recommendation should be attributable to available evidence such as prerequisite status, learner progress, estimated effort, deadline proximity, or resource relevance. Production model adoption must define input features, model version, confidence, fallback behavior, and evaluation thresholds before it replaces deterministic logic.

## 5. Current implementation status

- Text cleaning, topic extraction, graph ordering, scheduling, and metric primitives are implemented and tested.
- PDF text extraction is supported through the backend processing path.
- OCR is integrated as an optional Tesseract/PyMuPDF provider and is invoked only for image-only documents when enabled. Its dependencies are deliberately excluded from the base API image and must be supplied by a dedicated OCR-enabled image/provider with binary patching and worker metrics.
- Semantic matching is deterministic and suitable for a baseline; it is not a validated domain model.
- The C++ scorer is independently testable and exposes a line-oriented stdin contract. The backend uses the native executable when `SCORING_ENGINE_PATH` is configured; the Python fallback now applies the same difficulty, mastery-gap, prerequisite-readiness multiplier, and descending ordering contract.
- Roadmap estimates are never capped to one day. Concepts that exceed remaining daily capacity are split into ordered segments, persisted plans require capacity for the complete estimate, and previews may show a clearly labeled partial final concept.
- Stored syllabus copies are processed into bounded, page-tagged text; a conservative unit/module/chapter parser creates source-aware topic candidates and links them to a syllabus version. The baseline does not infer prerequisite edges from headings or ordering. Topic quality and completeness still require review against the applicable RVCE syllabus.
- Historical exam imports accept text or PDF, preserve Part A quiz items and Part B main questions separately, associate prompts with same-course concepts using exact phrase and token-overlap matching, and calculate topic frequency/rankings from main questions only. The archive reports quiz counts separately.
- The historical-question topic association is best-effort and must be evaluated against RVCE papers before its frequency totals are treated as authoritative. Scanned PDFs require OCR to be enabled.
- AI-generated website recommendations for concepts are deferred. A provider, server-side key configuration, URL verification policy, and recommendation-quality evaluation remain future work.
- Background document processing, bounded OCR, reproducible evaluation, and native scorer integration are implemented. External model serving and model monitoring are optional future extensions rather than required baseline components.

## 6. Safety and quality constraints

- Reject cyclic prerequisite graphs before generating a plan.
- Bound input size and processing time for uploaded or extracted text.
- Do not treat generated mappings as authoritative without validation.
- Preserve the source syllabus and mapping version when results affect a persisted roadmap.
- Keep page and unit provenance attached to concept records so learners and reviewers can trace each extracted item to its source copy.
- Record evaluation data without exposing learner-identifying information unnecessarily.
