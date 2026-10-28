# Document Control and Governance

**Document ID:** ILR-DOC-001
**System:** Intelligent Learning Roadmap
**Version:** 2.1
**Status:** Implementation-complete development baseline
**Owner:** Project maintainer
**Last reviewed:** 2026-10-28

## 1. Purpose

This document defines the controlled documentation set for the Intelligent Learning Roadmap platform. It establishes the authoritative location of system requirements, design decisions, operational procedures, security controls, test evidence, and known limitations.

The repository is an implementation-complete development baseline. A production release still requires operator-owned infrastructure, external security acceptance, and formal release approval identified in the traceability, security, operations, and testing documents.

## 2. Document hierarchy

| Document | ID | Authority |
|---|---|---|
| Requirements traceability | ILR-REQ-001 | Requirement coverage and gaps |
| Architecture | ILR-ARC-001 | System boundaries and component relationships |
| Frontend design | ILR-FE-001 | User interface and client behavior |
| ML and scoring design | ILR-ML-001 | Learning logic, scheduling, and ranking |
| API specification | ILR-API-001 | HTTP contract and endpoint behavior |
| Database design | ILR-DB-001 | Relational persistence contract |
| Data protection | ILR-DATA-001 | Data classification, retention, and privacy controls |
| Security baseline | ILR-SEC-001 | Required security controls |
| Security audit | ILR-AUD-001 | Findings, risks, and remediation status |
| Deployment and release | ILR-REL-001 | Build, release, and rollback procedures |
| Operations | ILR-OPS-001 | Runtime and incident procedures |
| Testing | ILR-TST-001 | Verification strategy and evidence |
| Evaluation | ILR-EVAL-001 | Quality and learning-outcome measures |
| Privacy impact assessment | ILR-PIA-001 | Personal-data flows, risks, rights, and approvals |
| Service-level objectives | ILR-SLO-001 | Reliability targets, metrics, and alert conditions |
| Operational readiness | ILR-OPS-002 | Release handoff controls, operator acceptance, and evidence package |
| Accessibility and performance acceptance | ILR-FE-002 | Automated and manual frontend acceptance criteria |
| Security acceptance | ILR-SEC-002 | Independent security testing and approval record |
| Release acceptance | ILR-REL-002 | Evidence-based production approval template |
| RVCE syllabus catalog | ILR-RVCE-001 | RVCE source authority, metadata, normalization, and course-row import contract |

## 3. Status definitions

- **Implemented:** Present in the repository and verified by an automated check or documented inspection.
- **Partial:** A development implementation exists, but production behavior, coverage, or operational controls are incomplete.
- **Planned:** Required by the target design but not implemented in the current baseline.
- **Blocked:** Cannot be completed until an external decision, service, credential, or infrastructure dependency is supplied.

## 4. Change control

Changes to authentication, authorization, persistence, uploads, roadmap generation, scoring, CI, or deployment configuration require:

1. An update to the relevant design document.
2. A corresponding test or verification record.
3. An update to `docs/requirements-traceability.md` when requirement coverage changes.
4. A security review for changes affecting trust boundaries, secrets, personal data, or file processing.

Generated files, local environment files, credentials, uploads, caches, and build products are not controlled design artifacts and must remain excluded by `.gitignore`.

## 5. Review cadence

The documentation set shall be reviewed at minimum before a tagged release, after a security incident, after a schema or API breaking change, and when a target requirement changes. The repository owner is responsible for approving the status of partial and planned items.
