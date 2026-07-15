# User Guide

Apex Credit supports four user perspectives, each accessing distinct console dashboards.

---

## 1. Applicant Guide

- **Step 1: Submit Application**: Enter loan request parameters (amount, purpose, terms) along with income and employment details.
- **Step 2: Upload Documents**: Drag or select files for PAN, Aadhaar, Salary, Bank Statement, and Employment Letter.
- **Step 3: Verification status**: Watch verification progress (Intake -> OCR -> Validation). If a document is missing or expired, the timeline shows a HOLD state.

---

## 2. Underwriter Guide

- **Step 1: Active Queue**: Check the sidebar list showing review requests. Select a card to view their profile.
- **Step 2: Inspect AI Decisions**: Review DTI, credit history, and read OCR raw extracts. Assess policy rule citations.
- **Step 3: Submit Final Decision**: Use the decision card to select APPROVE or DECLINE. Input rationale comments and submit to complete processing.

---

## 3. Credit Manager Guide

- **Step 1: Policy Rules**: View active business rules (DTI thresholds, score weights). Edit thresholds inline to dynamically update database values.
- **Step 2: Analytics KPI**: Monitor total volumes, average risk distributions, average decision timelines, and chart approvals trends.

---

## 4. Auditor Guide

- **Step 1: Integrity Auditing**: Check application logs verification statuses. Green banner indicates that audit logs match their cryptographic hashes.
- **Step 2: Inspect Execution Traces**: View detailed JSON objects representing tool inputs/outputs, model configurations, and times.
