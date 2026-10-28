# Accessibility and Performance Acceptance

**Document ID:** ILR-FE-002  
**Version:** 1.0  
**Status:** Automated baseline; manual acceptance pending  
**Last reviewed:** 2026-10-28

## 1. Automated controls

- Playwright provisions Chromium in CI and verifies login labels, navigation, and authenticated resource workflows.
- Lighthouse runs against the built frontend with accessibility threshold `0.90` and performance threshold `0.70`.
- The frontend build enforces a 450 KiB maximum JavaScript asset budget.
- The production build uses a locked `package-lock.json` and `npm ci`.

## 2. Manual acceptance checklist

The release owner must record results for keyboard-only navigation, visible focus order, screen-reader announcements, color contrast, zoom to 200%, reduced motion, touch targets, slow-network behavior, and error recovery. The automated checks do not prove complete WCAG conformance or device compatibility.

## 3. Performance evidence

Run `python scripts/load_test.py --url http://staging-api/health/ready --requests 100 --workers 10` against staging, record p95 latency and error rate, and compare with the approved SLO. Repeat after material frontend, API, database, or worker changes.
