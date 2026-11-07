# Privacy Impact Assessment

**Document ID:** ILR-PIA-001  
**Version:** 1.2
**Status:** Development assessment  
**Last reviewed:** 2026-11-06

## 1. Scope and purpose

The platform processes account identity data, learner progress, quiz attempts, course content, uploaded syllabus documents, extracted text, roadmap recommendations, historical exam questions, and operational audit records. Processing is limited to authentication, syllabus-derived learning-plan generation, question-paper indexing and frequency analysis, evaluation, security, and support. Manual learning-resource catalog management is outside the learner workflow. AI-generated website recommendations are deferred; syllabus and learner data are not sent to an external AI provider by this release.

## 2. Data-flow assessment

| Flow | Data | Processing | Control |
|---|---|---|---|
| Account access | Email, name, password hash | Registration and JWT authentication | Argon2, short-lived tokens, server-side token revocation |
| Learning workflow | Course, concept, progress, quiz data | Roadmap and adaptation | Ownership checks, export, deletion |
| Syllabus workflow | PDF bytes, checksum, extracted text, syllabus version, derived concepts | Private storage and roadmap input generation | Ownership checks, PDF validation, size/page/text limits, checksum verification |
| Historical exams | Retained private PDF, checksum, extracted prompts, source document/page, year, section, marks, and topic mapping | Reviewable frequency analysis and roadmap evidence | Ownership checks, bounded parsing/OCR, generated private object keys, duplicate-import cleanup, source provenance, and verified-only analytics |
| Operations | Request IDs, status counters, audit events | Security and reliability monitoring | Redaction, restricted metrics, configurable retention |

## 3. Risks and mitigations

- Unauthorized access is mitigated by authenticated, user-scoped queries and role dependencies.
- Malicious documents are constrained by type, size, page, encryption, checksum, and worker processing limits.
- Excessive retention is mitigated by account deletion, object-storage lifecycle configuration, audit purge tooling, and documented retention ownership.
- Evaluation leakage is mitigated by requiring de-identified benchmark data separate from production learner records.
- Operational disclosure is mitigated by excluding credentials and document contents from logs and restricting `/metrics` at the network boundary.

## 4. User rights

Authenticated users can export their profile and complete relational learning/provenance record and request deletion using email confirmation. Deletion removes owned database records, audit actor references, and private storage objects, and anonymizes review references that must survive with another owner's data, subject to configured backup/object-storage retention windows.

## 5. Approval requirements

Before production use, the data owner must approve retention periods, lawful basis/consent language, processor agreements, backup deletion behavior, cross-region storage decisions, and incident-notification procedures.
