# Syllabus and Historical Paper Ingestion

**Document ID:** ILR-DOC-ING-001  
**Status:** Implemented development workflow  
**Version:** 1.4
**Reviewed:** 2026-11-10

## 1. Purpose and scope

This document defines how RVCE syllabus copies and historical question-paper PDFs enter the learning platform, how extracted content is reviewed, and how verified evidence reaches concept maps, question-frequency views, and roadmaps. The workflow reuses the authenticated course, concept, resource, exam, progress, and roadmap APIs.

Syllabus documents describe course content and assessment policy. They are not historical question papers. Syllabus assessment language is stored as syllabus evidence; it never creates individual quiz questions. Historical question records are created only from a question-paper import or a separately submitted question record.

## 2. Syllabus processing

1. An authenticated learner selects an owned course and uploads a PDF. The original document is stored privately as an academic resource with a checksum.
2. The existing document worker extracts page text. Image-only PDFs use OCR when the optional OCR provider is enabled. Extracted text includes `[[PAGE n]]` markers.
3. A map-generation request parses topic candidates and labeled facts. Topics retain their printed wording, normalized matching text, unit label, source page, extraction confidence, source resource, and syllabus-version ID. RVCE’s inline unit-hour headings are parsed. Colon-led subject headings become parent topics, comma- or semicolon-delimited details become child topics, and nested colon headings remain children of the active subject heading. Generic labels such as “Example” are not promoted to standalone concepts. Labeled outcome, laboratory, assessment-policy, rubric, reference, and course-metadata lines are saved as facts or excluded from the teaching-content block; they do not become concept nodes.
4. A syllabus version is associated with the source document. Records from distinct versions remain in `syllabus_records`; reused concepts do not erase those versioned records.
5. Every newly extracted row begins `pending_review`, including rows with strong unit/page structure. A learner can verify or reject pending rows on the Syllabus Copies screen. The displayed confidence is a conservative rule-based extraction signal, not a calibrated probability or an approval decision. Pending topics remain visible in the concept map for review, rejected topics are omitted from the syllabus map, and only concepts backed by a verified current syllabus record can enter evidence-based question mapping or new roadmaps.

Map generation also extracts a separate course-planning profile. It may contain printed course-code aliases, category, L:T:P credits, total L/T/P/EL hours, ordered unit hours/pages, explicit “for CIE only” scope, course outcomes, assessment components/format, and CIE/SEE marks. These values are not silently normalized. Missing structures, unit/hour mismatches, and suspicious workload totals are retained as profile issues. A learner must review the profile before it controls a persisted roadmap, and may correct the bounded course type, modality hours, unit hours, and source-supported unit scope with review notes. Profile verification does not verify an institutional catalog row or resolve an academic ambiguity outside the uploaded copy.

The syllabus parser is deliberately conservative and source-aware. It recognizes common UNIT, MODULE, and CHAPTER headings, joins wrapped teaching prose within each unit, and retains the original source text for inspection. For combined RVCE scheme PDFs, course sections are selected by the chosen course code before map generation; an absent code fails with a reviewable error rather than mixing subjects. Teaching-content extraction stops at laboratory, outcome, reference, and rubric sections. It does not promise complete structured extraction of every RVCE table, course code, credit/hour cell, nested subtopic, or outcome. Those records need human review; ambiguous table structure can require manual correction or a future table-aware parser.

### Representative RVCE validation

The 78-page `AI-2022.pdf` from the supplied RVCE syllabus folder was used as an earlier real-document check. Selecting course code `AI233AI` isolates that subject’s section (beginning on PDF page 21 in the supplied copy), yields five unit-hour records at 9 hours each, and preserves source pages on topic/subtopic candidates. The neighboring course section is excluded.

The 96-page supplied 2022 AI/ML third-year scheme PDF was checked again on 2026-11-07. Selecting `AI253IA` isolated its course section and yielded 106 teaching concepts: 19 root headings and 87 child topics. No course-outcome, laboratory, rubric, or marks-distribution row was emitted as a concept. This is deterministic parser evidence for the observed document layout; it is not an RVCE academic decision that all 106 names or parent-child relations are correct.

## 3. Concept maps and prerequisites

Extracted topics are linked to course concepts and retain source page, unit, hierarchy, and review metadata. Reuse uses a source-aware identity of normalized name, unit, and parent heading. Repeated labels in different units or under different parents remain separate nodes. A name that is unique in the submitted source may reuse one prior course concept when its unit changes across syllabus versions so learner progress is preserved. Distinct syllabus-version records remain separately attributable. The map places concepts in stable unit columns, visually distinguishes pending from verified nodes, draws parent-child topic edges separately from accepted prerequisite edges, and exposes page provenance in each node label.

The parser suggests a prerequisite only when a syllabus line explicitly states a supported relation (for example, “X requires Y”) and both names match extracted concepts. Every suggestion stores its source wording, page, and confidence, and remains `proposed`. Suggestions do not affect a roadmap until a learner accepts them. Acceptance checks the same-course relationship and rejects any edge that would create a cycle. Existing manually recorded edges are accepted edges.

## 4. Historical question-paper processing

The upload form requires the course, paper label, year, assessment type, question format, PDF, and an explicit choice for whether Part A is the quiz section. The assessment type choices are quiz, test/CIE, SEE, assignment, lab, practice, and unknown. Format choices are objective, short, long, numerical, coding, practical, and unknown. These are paper-level fallbacks. Strong printed question-paper headers identify CIE pages as `test` and semester-end examination pages as `see`; the service does not infer assessment identity from question wording. Printed Part headings take precedence over the fallback, and Part A becomes quiz material only when the source structure and uploader declaration establish that rule.

Before persistence, any explicitly printed institutional course code is compared with the selected course. A mismatch returns `422` and prevents a paper for another subject from contaminating the selected map or frequency data. Documents that print no recognizable course code remain reviewable and rely on the selected owned course.

The parser first assigns page roles. Pages headed as schemes, model answers, answer keys, or solutions—and their continuation pages until the next strong question-paper header—are excluded. Question starts support common RVCE forms such as `1a`, `3.a`, `2(a)`, `1.1`, `2 a`, and continued standalone subparts. Table columns, CO/BT labels, figure captions, administrative headers, and rubric tails are removed from prompts. The original PDF is retained as a private `historical_exam_pdf` resource. Extracted question rows retain the source resource ID and filename, year, printed part, question number when recognized, subpart when recognized, marks when printed, page number, prompt, concept suggestion, mapping score, versioned matcher metadata, assessment type, question format, and review status. Page/image content remains in the original PDF; each extracted row points to its page so a reviewer can inspect figures and layout in the source.

Question-to-concept associations are suggestions computed only against verified concepts in the current syllabus version. `rvce-hybrid-lexical-v2` combines corpus-aware term rarity, full phrase and derived acronym evidence, OCR-tolerant character similarity, and parent/unit context. It withholds a suggestion when the best score is below `0.62` or insufficiently separated from the runner-up. Each row records the status, version, margin, explanation, and up to five ranked candidates; the score is relevance, not a calibrated probability. Imported rows begin `pending_review`, and the interface displays this evidence. During review the learner can select a verified syllabus concept, explicitly leave the row unmapped, correct assessment/format/difficulty metadata, verify it, or reject the extraction. Rejected and pending rows remain searchable in the archive but do not affect frequency rankings or roadmap scoring. Learner quiz attempts remain a separate `quiz_attempts` dataset and are not mixed with historical papers.

PDF imports retain one private source object only when at least one new parsed question is committed. If parsing, persistence, or all-question duplicate detection fails after the object write, the database transaction is rolled back and the uncommitted object is deleted.

If a paper is scanned, OCR must be enabled and its optional dependencies installed. OCR preserves page markers but does not guarantee correct reading of diagrams, equations, handwritten material, or complex tables. Marks and subparts are best-effort extraction and must be checked against the stored source PDF.

## 5. Frequency evidence and roadmaps

Question frequency is grouped by verified current-syllabus concept and year from verified main questions. The response includes total verified rows, main and quiz counts, mapped and unmapped main-question counts, per-year topic counts, last-seen year, repeated prompt occurrences, documented marks, and IDs/page references for the source questions. A verified main question without a verified concept mapping remains visible in the archive and increments `unmapped_main_question_count`, but it does not create a synthetic “general” topic or inflate a syllabus-topic ranking.

Roadmap preview requires an explicit course ID. `rvce-evidence-priority-v2` uses source unit sequence and accepted prerequisite edges as hard ordering constraints and rejects cycles or dependencies that reverse unit order. Within the current eligible unit, the score combines reviewed historical recurrence/recency/marks (38%), learner mastery gap (30%), downstream concepts unlocked (17%), and concept difficulty (15%). Concepts without verified evidence receive no historical-evidence boost. These weights are transparent heuristics, not outcome-calibrated RVCE weights.

After profile verification, total L/T/P/EL workload is apportioned across ordered units by printed unit hours and across their concepts; missing hours use bounded fallbacks. `rvce-activity-roadmap-v3` expands each concept into course-type-specific activities, applies bounded mastery and plan-mode factors, and splits them into at most 60-minute sessions. Part A/quiz evidence is attached to retrieval-oriented activities. Verified Part B/main evidence affects priority and supports other exam-oriented activities. A reviewed CIE-only unit is excluded from SEE coverage and reserved revision. Deadline capacity is checked before persistence. The generated schedule is deterministic, not a statistically optimized or outcome-calibrated time-on-task model.

Course plans use one owned subject. Semester plans require an explicit list of owned courses sharing a non-null program, scheme, and semester; courses are interleaved without violating each course's internal order. The service never infers electives. Full-term, CIE, SEE, and revision modes are supported, together with inclusive dates, unavailable weekdays, daily capacity, and explicit end-of-plan revision time. Completing sessions updates mastery/progress; every session for a concept must be complete before the concept is marked complete.

## 6. Review and API surface

| Action | Endpoint | Notes |
| --- | --- | --- |
| Upload syllabus | `POST /api/v1/syllabus/sources/upload?course_id=...` | Stores private PDF source |
| Process syllabus | `POST /api/v1/syllabus/sources/{resource_id}/process` | Uses document worker and OCR fallback |
| Generate versioned map and records | `POST /api/v1/syllabus/sources/{resource_id}/generate-map` | Creates topic records and explicit prerequisite suggestions |
| Read roadmap profile | `GET /api/v1/syllabus/profile?course_id=...` | Returns extracted workload/scope, issues, status, and review notes |
| Review roadmap profile | `POST /api/v1/syllabus/profile/{version_id}/review` | Applies bounded corrections and verification before persistence |
| List parsed records | `GET /api/v1/syllabus/records?course_id=...` | Includes source, page, confidence, version, and review status |
| Review syllabus record | `POST /api/v1/syllabus/records/{record_id}/review?status=...` | `verified`, `rejected`, or `pending_review` |
| Import question PDF | `POST /api/v1/exams/import-pdf?course_id=...` | Multipart metadata and PDF; parsed rows are pending review |
| View source paper | `GET /api/v1/exams/papers/{resource_id}` | Streams the retained PDF to an authorized course owner |
| Search questions | `GET /api/v1/exams/questions` | Course, year, text, topic, assessment, and format filters |
| Review question | `POST /api/v1/exams/questions/{question_id}/review?status=...` | May also set `concept_id` or `clear_concept=true`; only verified mapped main rows contribute to topic frequency |
| Frequency view | `GET /api/v1/exams/frequency?course_id=...` | Reviewed evidence, mapped/unmapped totals, and source question references |
| Roadmap preview | `GET /api/v1/roadmap?course_id=...&days=...` | Requires an explicit owned course |
| Read active roadmap | `GET /api/v1/roadmap/active` | Restores the newest active owned plan and current session status |
| Generate course roadmap | `POST /api/v1/roadmap/generate` | Requires processed syllabus, current concepts, feasible capacity, and any available profile to be verified |
| Generate semester roadmap | `POST /api/v1/roadmap/semester/generate` | Balances explicit same-scope course IDs only |
| Update roadmap session | `PATCH /api/v1/roadmap/items/{item_id}` | Owner-scoped status; mastery is accepted only on completion |

All endpoints require authentication. Course ownership is checked before upload, retrieval, review, and roadmap generation.

## 7. Data model and migration

Migration `0011_ingestion_provenance_review` creates `syllabus_records` and adds source resource, page, question number/subpart, marks, assessment type, question format, mapping confidence, and review status to historical question rows. It adds subtopic parentage and estimated minutes to concepts, plus proposal state and source provenance to prerequisite edges. Existing prerequisite rows migrate as accepted; existing historical question rows migrate as pending review so unverified legacy mappings cannot affect evidence rankings. Migration `0013_matcher_evidence` adds non-null `mapping_metadata_json` with an empty-object default so algorithm identity and decision evidence are durable without changing prior mappings. Migration `0014_course_aware_roadmaps` stores reviewable profile JSON/status/notes, unit sequence, course/semester plan scope and mode, start/revision fields, and typed per-item course/source/assessment/evidence metadata.

## 8. Operational verification

Backend and ML tests cover page-role filtering, RVCE numbering variants, source-page/marks preservation, explicit section and CIE/SEE metadata, strict course-code matching, syllabus hierarchy/fact separation, profile aliases/workload/issues, same-name source identity, acronym/context/OCR matching, ambiguous and no-evidence abstention, persisted matcher evidence, hard unit/dependency ordering, typed activity construction, CIE/SEE filtering, mastery adaptation, calendar feasibility, semester balancing, session completion, manual question remapping, ownership checks, review-gated analytics, and course-specific roadmap previews. Frontend checks cover profile review, course/semester controls, typed sessions, upload metadata controls, matcher explanations and candidates, manual concept review, mapped/unmapped totals, source references, concept-map provenance/review styling, and strict TypeScript compilation. The 2026-11-10 frontend build, Python compilation, and release invariant check passed locally; the expanded Python/API and migration lifecycle suite awaits a compatible CI/runtime execution.

The supplied 20-page combined CIE/scheme/SEE packet was checked on 2026-11-07. It explicitly declares course code `21CS45`; it must therefore be imported only into that course and must not be mapped against the separate `AI253IA` syllabus used for the concept-parser check. The parser returned 64 question rows: 19 Part A quiz items and 45 main questions, split into 32 CIE/test and 32 SEE rows. Scheme/solution pages contributed zero prompts. This is an implementation conformance check for that packet, not a licensed-corpus evaluation or academic acceptance result. Exact commands and broader suite outcomes are recorded in `testing.md` and the implementation handoff.
