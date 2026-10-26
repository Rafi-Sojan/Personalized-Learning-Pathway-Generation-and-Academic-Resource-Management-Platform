# ML, Scheduling, and Scoring Design Specification

**Document ID:** ILR-ML-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

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
- The C++ scorer is independently testable and exposes a line-oriented stdin contract. The backend uses the native executable when `SCORING_ENGINE_PATH` is configured and falls back to the Python contract when it is unavailable.
- Background processing, model serving, feature storage, and model monitoring remain planned.

## 6. Safety and quality constraints

- Reject cyclic prerequisite graphs before generating a plan.
- Bound input size and processing time for uploaded or extracted text.
- Do not treat generated mappings as authoritative without validation.
- Preserve the source syllabus and mapping version when results affect a persisted roadmap.
- Record evaluation data without exposing learner-identifying information unnecessarily.
