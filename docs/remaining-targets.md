# Project Completion and Acceptance Register

**Document ID:** ILR-REG-001  
**Version:** 1.5
**Status:** Development implementation complete; release acceptance actions open  
**Owner:** Project maintainer  
**Last reviewed:** 2026-11-07
**Authority:** This register is the consolidated source for outstanding project targets. Requirement-level detail remains in `requirements-traceability.md`; approval evidence is recorded in `release-acceptance.md` and the referenced domain records.

## 1. Purpose

This register distinguishes repository implementation work from decisions and evidence that must come from RVCE academic reviewers, authorized data owners, independent assessors, or a deployed staging environment. An automated repository check does not close an external acceptance action. No target below is treated as accepted without the stated evidence.

## 2. Completion status

| ID | Target | Status | Accountable role | Required evidence and closure condition |
|---|---|---|---|---|
| DEV-01 | Core platform, personal subject/syllabus onboarding, RVCE catalog workflow, explainable learning engine, source provenance, branch mapping, learner enrollment, migrations, and operational controls | Local regression baseline verified; release workflow pending | Project maintainer | Local 2026-11-07 checks recorded 55 passed/1 skipped Python tests, perfect results on the eight-case synthetic matcher regression set, migration `0013` fresh/downgrade/re-upgrade checks, and passing Ruff, mypy, frontend build, and bundle checks. Earlier checks recorded seven Playwright scenarios reporting `ok` plus a live walkthrough; the below-policy browser runner required termination. Closure still requires a clean Release gates run at the candidate revision with the declared Node/npm and retained artifacts. |
| APP-01 | Validate syllabus-to-concept-map extraction against the selected RVCE syllabus formats and review topic quality | Open; source identity improved, academic validation pending | Project maintainer and RVCE academic reviewer | Course scoping, unit/parent-aware identity, hierarchy, review gating, and non-topic exclusion are implemented; one supplied `AI253IA` layout check yielded 106 clean teaching nodes, but expected-topic annotations, precision/recall, provenance review, and documented academic decisions are still required |
| APP-02 | Validate historical question parsing and topic-frequency attribution across authorized RVCE past-paper layouts | Open; hybrid matching and abstention implemented, corpus evaluation pending | Project maintainer and learning-quality reviewer | One supplied packet yielded 64 clean question rows with the expected 19/45 quiz/main and 32/32 CIE/SEE splits. The v2 matcher records ranked evidence and abstains on ambiguity, but authorization, OCR/layout breadth, row-level human review, topic-mapping agreement, and a multi-year frequency baseline remain required. |
| APP-03 | Add archive filters across RVCE program/branch, scheme, and semester when question-paper provenance is available | Open; metadata/model decision | Project maintainer and RVCE data owner | Versioned paper-scope metadata, migrated question records, and filter acceptance across the approved RVCE catalog |
| AI-01 | Add AI-generated website links to concepts | Deferred by product decision | Product owner and project maintainer | Select provider and model, configure a server-side API key, define trusted-link validation/grounding, and record quality review before implementation |
| RVCE-01 | Select the target admission cohort, branch set, scheme year, and semester scope | Open; external decision | RVCE academic owner | Signed scope record naming cohort, branches, scheme, and semesters |
| RVCE-02 | Review 207 extracted candidate rows for identity, title, credit interpretation, semester, and source-page accuracy | Open; academic review | RVCE academic owner | Row-level decisions with reviewer, date, outcome, and source reference; approved rows imported only after review |
| RVCE-03 | Reconcile two quarantined same-identity/different-title conflicts | Open; academic decision | RVCE academic owner | Recorded decision for each conflict, authoritative source page, and updated validated data |
| RVCE-04 | Map `BE-UNMAPPED` first-year rows to every applicable selected branch and confirm catalog coverage | Open; depends on RVCE-01/02 | RVCE academic owner | Approved branch mappings and a coverage report against the signed scope, with unresolved rows listed |
| DATA-01 | Confirm lawful access and completeness of the syllabus source set for the chosen RVCE scope | Open; external source confirmation | RVCE data owner | Source authorization or provenance note and signed completeness statement; inventory alone is not proof of institutional completeness |
| EVAL-01 | Provide a licensed or otherwise authorized, de-identified historical-question corpus and establish an evaluation baseline | Open; computed synthetic regression gate exists, data-owner action remains | Data owner and learning-quality reviewer | Corpus license/authorization record, version and de-identification statement, benchmark report, metric thresholds, calibration/abstention review, and reviewer decision. The eight synthetic CI cases do not satisfy this evidence. |
| SEC-01 | Complete independent security assessment of the deployed release candidate and remediate findings | Open; independent assessment | Security assessor and project maintainer | Assessment report with scope, severity, evidence, remediation, retest, and residual-risk acceptance |
| PRIV-01 | Approve privacy impact assessment, lawful basis, retention schedule, processors, rights handling, and incident procedures | Open; legal/data-owner approval | Privacy or legal owner | Dated approval against `privacy-impact-assessment.md`; any conditions tracked to closure |
| OPS-01 | Deploy a representative staging environment and collect load, latency, backup/restore, RPO/RTO, monitoring, and alert-routing evidence | Open; infrastructure dependent | Operations owner | Staging identifier and revision, retained workflow/run reports, measured results, backup restore evidence, alert test, and SLO decision |
| UX-01 | Complete manual keyboard, screen-reader, responsive, and user-flow acceptance | Open; human review | Accessibility reviewer and product owner | Completed checklist in `accessibility-and-performance.md`, browser/device scope, findings, and disposition |
| REL-01 | Review the complete evidence package and authorize, reject, or defer production release | Open; release decision | Named release owner | Completed `release-acceptance.md` with each gate evidence link, accepted residual risks, decision, reviewer, and date |

## 3. Repository verification procedure

Run the workflow named **Release gates** on a release candidate or push a version tag. It performs Python tests and quality checks, RVCE source validation, controlled-artifact verification, frontend build and browser acceptance, native scoring-engine tests, dependency audit, container runtime smoke checks, a bounded readiness load check, and database backup/restore verification. Retain the workflow URL and artifacts in the release acceptance record.

For local review, run `scripts/verify_release.py`, `scripts/validate_rvce_courses.py database/rvce_course_candidates.json`, the backend/ML test commands in `docs/testing.md`, `npm ci && npm run build && npm run test:e2e` from `frontend`, and the CMake/CTest commands in `scoring-engine/README.md`. Local checks do not substitute for the external evidence in Section 2.

## 4. Change control

When a target closes, update its status and evidence reference here, update the relevant detailed record, and preserve the approval artifact in the controlled release evidence store. Do not commit credentials, personal data, licensed exam material, assessment exploit details, or production backups. Record blockers as a named dependency and owner role; do not represent a blocked external action as completed repository work.

## 5. Related controlled documents

- `requirements-traceability.md` — requirement coverage and implementation status.
- `implementation-record.md` — RVCE extraction, import, academic review, and enrollment procedure.
- `release-acceptance.md` — candidate-specific production approval record.
- `operational-readiness.md` — deployment and operational evidence.
- `security-acceptance.md` — independent security assessment.
- `privacy-impact-assessment.md` — personal-data processing and approval.
- `accessibility-and-performance.md` — manual and automated frontend acceptance.
- `evaluation.md` — learning-quality metrics and benchmark requirements.
