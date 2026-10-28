# Release Acceptance Record

**Document ID:** ILR-REL-002  
**Version:** 1.0  
**Status:** Template; staging evidence required  
**Last reviewed:** 2026-10-28

## Acceptance evidence

| Area | Evidence required | Status |
|---|---|---|
| Source and build | Approved revision, frontend build, C++ build/test, Python quality checks | Pending staging/CI run |
| Data lifecycle | Migration output, export/deletion verification, retention approval | Pending operator evidence |
| Reliability | Backup/restore drill, measured RPO/RTO, SLO review, alert routing | Pending operator evidence |
| Security | Dependency audit, image scan, SBOM, DAST, independent penetration test | Repository automation implemented; independent test pending |
| Privacy | Approved PIA, lawful basis, retention, processor and breach procedures | Pending legal/data-owner approval |
| Learning quality | Licensed/de-identified corpus, benchmark version, metric thresholds, regression decision | Pending approved corpus |
| Accessibility | Automated gates plus manual keyboard/screen-reader review | Automated gates implemented; manual review pending |

## Approval

The release owner may approve production only after every pending item is evidenced, explicitly accepted as residual risk, or marked blocked with an accountable owner and due date. This template must be copied into the release record; credentials, personal data, and backup files must not be committed.
