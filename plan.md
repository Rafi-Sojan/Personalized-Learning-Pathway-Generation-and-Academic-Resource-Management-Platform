# Project Plan and Outstanding Targets

**Document type:** Cross-model project plan  
**Version:** 1.5
**Plan snapshot:** 2026-11-07  
**Status:** Local repository regression baseline verified; candidate workflow and external acceptance remain open  
**Status authority:** [`docs/remaining-targets.md`](docs/remaining-targets.md)

## 1. Objective

Deliver an RVCE-focused learning platform whose syllabus-derived concepts, roadmaps, and historical question frequencies have traceable sources and have been validated by the appropriate academic, data, security, privacy, accessibility, and operations owners.

The repository contains a broad development implementation. Work is complete only when both repository checks and required external evidence are recorded. Do not describe the project as production-ready solely because the application builds or runs locally.

The learner onboarding implementation supports private branch/scheme/semester subject creation and immediate syllabus attachment. Learning-engine v2 now adds explainable hybrid matching, conservative abstention, source-aware repeated-topic identity, and versioned dependency-safe roadmap priority. These repository changes do not close RVCE-01 through RVCE-04 or APP-01/APP-02/EVAL-01: official scope, catalog publication, and academic quality remain controlled by authorized evidence and review.

## 2. Recommended work sequence

### Phase A — Establish scope and evidence rights

| ID | Target | Current status | Closure evidence |
|---|---|---|---|
| RVCE-01 | Select the admission cohort, branches, scheme year, and semester scope. | Open; RVCE academic decision required. | Dated scope record naming the cohort, branch set, scheme, and semesters. |
| DATA-01 | Confirm source authorization and syllabus-set completeness for that scope. | Open; RVCE data-owner confirmation required. | Authorization or provenance note plus a signed completeness statement. |

These decisions define which catalog rows and source documents can be reviewed. An inventory of files alone does not establish institutional completeness or permission to use them.

### Phase B — Review and publish the RVCE catalog

| ID | Target | Dependency | Closure evidence |
|---|---|---|---|
| RVCE-02 | Review the 207 extracted candidate rows for identity, title, credits, semester, and source-page accuracy. | RVCE-01, DATA-01 | Row-level reviewer, date, decision, and source reference; only approved rows are published. |
| RVCE-03 | Resolve the two quarantined same-identity/different-title conflicts. | Authoritative RVCE decision | Recorded disposition for each conflict and validated source page. |
| RVCE-04 | Map first-year `BE-UNMAPPED` rows to applicable selected branches and verify catalog coverage. | RVCE-01, RVCE-02 | Approved branch mappings and coverage report listing unresolved rows. |

Keep uncertain records pending review. Do not infer a conflict resolution or branch mapping from course names alone.

### Phase C — Validate learning and question-paper quality

| ID | Target | Dependency | Closure evidence |
|---|---|---|---|
| APP-01 | Evaluate syllabus extraction and concept mapping on representative RVCE syllabi. | Approved scope and source set | Human-annotated expected topics, extraction precision/recall, unit/page provenance review, and correction decisions. |
| APP-02 | Evaluate question parsing and topic-frequency attribution on authorized RVCE past papers. | Authorized paper corpus; APP-01 topics where needed | Part A/Part B and OCR review, row-level parsing review, topic-mapping agreement, and year-frequency baseline. |
| EVAL-01 | Establish a licensed or otherwise authorized, de-identified historical-question benchmark. | Data-owner approval | Corpus authorization, version and de-identification record, benchmark report, metric thresholds, and reviewer decision. |
| APP-03 | Add archive filters for program/branch, scheme, and semester when paper provenance is available. | Paper-scope metadata decision and source provenance | Versioned schema, migration, populated test records, and accepted filters over the approved RVCE catalog. |

The current product rule is Part A = quiz and Part B = main questions when the source or uploader establishes those sections. Frequency claims must remain traceable to reviewed records mapped to verified concepts in the current syllabus version. The eight computed matcher cases and supplied-layout checks are regression anchors, but they do not close APP-01, APP-02, or EVAL-01 without authorization, row-level academic annotations, agreement metrics, calibration review, and accepted thresholds.

### Phase D — Complete independent readiness reviews

| ID | Target | Accountable role | Closure evidence |
|---|---|---|---|
| DEV-01 | Verify the implemented core platform and operational controls at a release candidate. | Project maintainer | Passing Release gates workflow with retained test and build artifacts. |
| SEC-01 | Assess the deployed release candidate independently and remediate findings. | Security assessor and maintainer | Scoped report, findings, remediation, retest, and accepted residual risks. |
| PRIV-01 | Approve lawful basis, retention, processors, rights handling, and incident procedures. | Privacy/legal owner | Dated approval against `docs/privacy-impact-assessment.md`; conditions tracked. |
| OPS-01 | Run a representative staging service and gather operational evidence. | Operations owner | Revision and environment identity, load/latency, backup/restore, RPO/RTO, monitoring, alert test, and SLO decision. |
| UX-01 | Complete human keyboard, screen-reader, responsive, and user-flow acceptance. | Accessibility reviewer and product owner | Completed `docs/accessibility-and-performance.md` checklist with browser/device scope and findings. |
| REL-01 | Make the production release decision. | Named release owner | Completed `docs/release-acceptance.md` with evidence links, residual risks, decision, reviewer, and date. |

### Deferred by product decision

| ID | Target | Status | Re-entry conditions |
|---|---|---|---|
| AI-01 | Generate concept-related website links with an AI service. | Deferred. | Product owner selects provider/model; server-side key management, link grounding/validation, and quality review are defined. |

Do not implement AI link generation or request an API key until the product owner reopens this target.

## 3. Dependencies and parallel work

```text
RVCE-01 + DATA-01
       ├── RVCE-02 ── RVCE-04
       ├── RVCE-03
       └── APP-01 ── APP-02 + EVAL-01 ── APP-03

DEV-01 ── SEC-01 + PRIV-01 + OPS-01 + UX-01 ── REL-01
```

External scope and source authorization should be settled before academic conclusions are drawn. Independent security, privacy, operations, and accessibility work can proceed on separate paths once a stable candidate and the appropriate owners are available.

## 4. Immediate maintainer actions

1. Review and commit the integration-path and digest-pinned frontend runtime remediations without resetting unrelated work.
2. Apply migration `0013_matcher_evidence` to each intended staging or production database before starting the updated API; preserve a backup and verify the revision. The root local development database is already at `0013` with its six historical-question rows retained.
3. Repeat the seven-scenario Playwright pass in the declared Node 24.22.1/npm 11.21.1 CI toolchain; every earlier local scenario reported `ok`, but the below-policy full runner required termination after reporting.
4. Push and rerun the backend/service and security workflows after the documented `PYTHONPATH` and nginx runtime remediations; then run the repository Release gates workflow on the named candidate and preserve its test, build, audit, runtime, learning-quality, and restore artifacts.
5. Obtain the RVCE-01 scope decision and DATA-01 source authorization/completeness statement.
6. Arrange academic reviewers and prepare row-level review sheets for the 207 catalog candidates and two quarantined conflicts.
7. Request an authorized, de-identified paper corpus and define APP-01/APP-02/EVAL-01 annotation protocols and acceptance thresholds, using the synthetic matcher and recorded 64-question/106-concept checks only as engineering baselines.

## 5. Change control

This plan summarizes the outstanding targets; it does not replace the acceptance register. When a target's state changes, update [`docs/remaining-targets.md`](docs/remaining-targets.md), its detailed domain document, and the evidence link. Record a target as complete only when its stated closure evidence exists. Record external decisions with the accountable owner and date.

