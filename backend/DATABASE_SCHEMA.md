# Database Schema Documentation

## Overview

This document describes the complete database schema for the Loan Application Processing Agent system. The schema consists of 13 tables organized into three main categories:

1. **User & Applicant Management** (users, applicants)
2. **Application Processing** (applications, documents, ocr_results)
3. **Processing Results & Decision Making** (validation_reports, scores, recommendations, fairness_checks, human_reviews, audit_logs)
4. **Policy Management** (policy_rules)

---

## Table Specifications

### 1. **users** Table
**Purpose**: Stores all system users with role-based access control

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique user identifier |
| full_name | VARCHAR(100) | NOT NULL | User's full name |
| email | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | User's email (login credential) |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt-hashed password |
| role | VARCHAR(50) | NOT NULL | User role: Applicant, Underwriter, CreditManager, Auditor |
| is_active | BOOLEAN | NOT NULL, DEFAULT=true | Account status flag |
| created_at | DATETIME | NOT NULL | Record creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Relationships**:
- One-to-one with `applicants` (optional, only for Applicant role users)
- One-to-many with `audit_logs` (as creator of actions)
- One-to-many with `human_reviews` (as reviewer)

**Indexing**:
- PK on id
- UNIQUE INDEX on email
- INDEX on id (auto-created with primary key)

---

### 2. **applicants** Table
**Purpose**: Extends user data with applicant-specific financial and demographic information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, FK→users.id (CASCADE) | References the User ID; serves as primary key |
| phone | VARCHAR(20) | NULLABLE | Applicant's phone number |
| date_of_birth | VARCHAR(20) | NULLABLE | DOB in YYYY-MM-DD format |
| address | VARCHAR(255) | NULLABLE | Residential address |
| gender | VARCHAR(20) | NULLABLE | Gender identity |
| monthly_income | FLOAT | NOT NULL, DEFAULT=0.0 | Gross monthly income in INR |
| employer_name | VARCHAR(100) | NULLABLE | Current employer name |
| employment_type | VARCHAR(50) | NOT NULL, DEFAULT='Salaried' | Salaried / Self-Employed / Unemployed |
| employment_stability_months | INTEGER | NOT NULL, DEFAULT=0 | Months in current employment |
| credit_score | INTEGER | NOT NULL, DEFAULT=0 | Credit bureau score (300-900 range) |
| created_at | DATETIME | NOT NULL | Record creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Relationships**:
- One-to-one with `users` (many-to-one, but typically one per applicant)
- One-to-many with `applications`

**Cascade Behavior**: Deleting a user cascades to delete the applicant and all their applications

---

### 3. **applications** Table
**Purpose**: Represents a loan application submitted by an applicant

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique application identifier |
| applicant_id | INTEGER | FK→applicants.id (CASCADE), NOT NULL, INDEX | Applicant who submitted |
| loan_amount | FLOAT | NOT NULL | Requested loan amount in INR |
| loan_purpose | VARCHAR(255) | NULLABLE | Purpose of loan (e.g., Home, Education, Debt Consolidation) |
| term_months | INTEGER | NOT NULL | Desired repayment period in months |
| monthly_debt_obligations | FLOAT | NOT NULL, DEFAULT=0.0 | Existing monthly debt payments in INR |
| status | VARCHAR(50) | NOT NULL, DEFAULT='DRAFT' | Application state: DRAFT, SUBMITTED, IN_PROGRESS, PENDING_REVIEW, APPROVED, DECLINED, REFER |
| created_at | DATETIME | NOT NULL | Application submission timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Relationships**:
- Many-to-one with `applicants`
- One-to-many with `documents`
- One-to-many with `validation_reports`
- One-to-many with `scores`
- One-to-many with `recommendations`
- One-to-many with `fairness_checks`
- One-to-many with `human_reviews`
- One-to-many with `audit_logs`

**Cascade Behavior**: Deleting an application cascades to all related documents, reports, and logs

---

### 4. **documents** Table
**Purpose**: Stores metadata for uploaded documents supporting an application

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique document identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Associated application |
| document_type | VARCHAR(50) | NOT NULL | Document category: Aadhaar, PAN, SalarySlip, BankStatement, EmploymentLetter |
| file_path | VARCHAR(255) | NOT NULL | Path to uploaded file |
| status | VARCHAR(50) | NOT NULL, DEFAULT='UPLOADED' | Processing state: UPLOADED, PROCESSING, PASSED, FAILED |
| error_message | VARCHAR(255) | NULLABLE | Error details if status='FAILED' |
| uploaded_at | DATETIME | NOT NULL | Upload timestamp |

**Relationships**:
- Many-to-one with `applications`
- One-to-many with `ocr_results`

**Processing Pipeline**: UPLOADED → PROCESSING → PASSED/FAILED

---

### 5. **ocr_results** Table
**Purpose**: Stores OCR (Optical Character Recognition) extraction results from documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique OCR result identifier |
| document_id | INTEGER | FK→documents.id (CASCADE), NOT NULL, INDEX | Source document |
| raw_text | TEXT | NOT NULL | Complete OCR extracted text |
| parsed_json | JSON | NULLABLE | Structured extraction: {name, id_number, salary, dates, etc.} |
| confidence_score | FLOAT | NOT NULL, DEFAULT=1.0 | OCR confidence (0.0-1.0) |
| extracted_at | DATETIME | NOT NULL | Extraction timestamp |

**Relationships**:
- Many-to-one with `documents`

**Purpose**: Enables document validation and information extraction

---

### 6. **validation_reports** Table
**Purpose**: Stores document and data validation results

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique report identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Associated application |
| name_match_score | FLOAT | NOT NULL, DEFAULT=1.0 | Name consistency across documents (0-1) |
| dob_match_score | FLOAT | NOT NULL, DEFAULT=1.0 | DOB consistency across documents (0-1) |
| income_consistency_pass | BOOLEAN | NOT NULL, DEFAULT=true | Bank deposits match declared salary? |
| is_expired | BOOLEAN | NOT NULL, DEFAULT=false | Any documents expired? |
| is_unreadable | BOOLEAN | NOT NULL, DEFAULT=false | Any unreadable documents? |
| status | VARCHAR(50) | NOT NULL, DEFAULT='PASS' | Overall validation: PASS, FAIL, HOLD |
| details_json | JSON | NULLABLE | Full validation report with checksums |
| created_at | DATETIME | NOT NULL | Report generation timestamp |

**Relationships**:
- Many-to-one with `applications`

**Decision Flag**: Status used to route application for human review if validation fails

---

### 7. **scores** Table
**Purpose**: Stores calculated credit and risk assessment scores

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique score record identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Associated application |
| debt_to_income_ratio | FLOAT | NOT NULL | Monthly debt obligations / monthly income |
| employment_stability_months | INTEGER | NOT NULL | Extracted from applicant profile |
| credit_score | INTEGER | NOT NULL | Extracted from applicant profile |
| income_stability_rating | FLOAT | NOT NULL | Calculated from bank deposits (0-1) |
| documentation_quality_score | FLOAT | NOT NULL | Document readability assessment (0-1) |
| risk_score | FLOAT | NOT NULL | Composite risk score (0-100) |
| calculated_at | DATETIME | NOT NULL | Calculation timestamp |

**Relationships**:
- Many-to-one with `applications`

**Scoring Inputs**:
- Applicant profile data
- Document validation results
- Bank statement analysis
- Income consistency checks

---

### 8. **recommendations** Table
**Purpose**: Stores AI agent recommendations on loan approval/decline

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique recommendation identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Associated application |
| recommendation | VARCHAR(50) | NOT NULL | Decision: APPROVE, REFER, DECLINE |
| confidence_score | FLOAT | NOT NULL | Decision confidence (0.0-1.0) |
| explanation | TEXT | NOT NULL | Detailed markdown explanation of decision |
| policy_citations | JSON | NULLABLE | Policies evaluated: [{rule_key, threshold_value, applicant_value, pass/fail}] |
| reasons_json | JSON | NULLABLE | Key decision factors: [{factor, impact, severity}] |
| generated_at | DATETIME | NOT NULL | Generation timestamp |

**Relationships**:
- Many-to-one with `applications`

**Decision Logic**: Based on policy rules, risk scores, and validation results

---

### 9. **fairness_checks** Table
**Purpose**: Stores fairness/bias testing results using blind scoring

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique fairness check identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Associated application |
| blind_recommendation | VARCHAR(50) | NOT NULL | Recommendation without demographic data: APPROVE, REFER, DECLINE |
| is_fair | BOOLEAN | NOT NULL | Does blind match regular recommendation? |
| fairness_status | VARCHAR(50) | NOT NULL | Overall fairness assessment: PASS, FAIRNESS_FAILURE |
| blind_scores_json | JSON | NULLABLE | Scores calculated in blind simulation |
| checked_at | DATETIME | NOT NULL | Check timestamp |

**Relationships**:
- Many-to-one with `applications`

**Purpose**: Ensures non-discriminatory lending decisions

**Fairness Logic**: 
- Recalculate scores without name, DOB, gender, address
- Compare blind recommendation with original
- Flag if results differ significantly

---

### 10. **human_reviews** Table
**Purpose**: Stores human underwriter review decisions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique review identifier |
| application_id | INTEGER | FK→applications.id (CASCADE), NOT NULL, INDEX | Application being reviewed |
| reviewer_id | INTEGER | FK→users.id (SET NULL), NULLABLE, INDEX | Underwriter who reviewed (set to NULL if user deleted) |
| decision | VARCHAR(50) | NOT NULL | Review decision: APPROVED, DECLINED, REFER |
| comments | TEXT | NULLABLE | Reviewer's notes and justification |
| reviewed_at | DATETIME | NOT NULL | Review timestamp |

**Relationships**:
- Many-to-one with `applications`
- Many-to-one with `users` (as reviewer)

**When Used**: Applications flagged by AI (REFER), or high-risk cases requiring human judgment

---

### 11. **audit_logs** Table
**Purpose**: Immutable audit trail of all application processing actions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique log entry identifier |
| application_id | INTEGER | FK→applications.id (SET NULL), NULLABLE, INDEX | Associated application (preserved if deleted) |
| action | VARCHAR(100) | NOT NULL | Action type: UPLOAD, OCR_EXTRACT, POLICY_CHECK, BIAS_TEST, HUMAN_DECISION |
| user_id | INTEGER | FK→users.id (SET NULL), NULLABLE, INDEX | User who triggered action (NULL if user deleted) |
| details_json | JSON | NULLABLE | Complete state snapshot at time of action |
| snapshot_hash | VARCHAR(64) | NULLABLE | SHA-256 hash for integrity verification |
| created_at | DATETIME | NOT NULL | Action timestamp |

**Relationships**:
- Many-to-one with `applications`
- Many-to-one with `users` (as actor)

**Audit Features**:
- Complete record of all processing steps
- State snapshots for rollback capability
- Integrity checksums to detect tampering
- Preserved even after application deletion

---

### 12. **policy_rules** Table
**Purpose**: Stores underwriting policy thresholds and business rules

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Unique rule identifier |
| rule_name | VARCHAR(100) | NOT NULL | Human-readable rule name |
| rule_key | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Machine-readable key (e.g., MIN_CREDIT_SCORE) |
| threshold_value | FLOAT | NOT NULL | Policy threshold value |
| rule_description | VARCHAR(255) | NULLABLE | Detailed explanation of rule |
| is_active | BOOLEAN | NOT NULL, DEFAULT=true | Enable/disable rule without deletion |
| created_at | DATETIME | NOT NULL | Rule creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Relationships**:
- Referenced by recommendations and scoring logic
- No direct foreign keys (referenced in recommendations.policy_citations)

**Example Rules**:
- MIN_CREDIT_SCORE: 650
- MAX_DTI: 0.45 (45%)
- MIN_EMPLOYMENT_MONTHS: 12
- MAX_LOAN_LIMIT: 5000000

**Modification**: Only Credit Managers can update rules

---

## Data Integrity & Constraints

### Cascade Delete Behavior
When a parent record is deleted:
1. **User Deletion** → Applicant deleted → Applications deleted → All related records deleted
2. **Application Deletion** → Documents, Reports, Scores, Recommendations, Reviews deleted
3. **Document Deletion** → OCR Results deleted

### Set Null Behavior
When a parent record is deleted:
- Reviewer deleted → HumanReview.reviewer_id set to NULL
- User deleted (as audit actor) → AuditLog.user_id set to NULL
- Application deleted → AuditLog.application_id set to NULL (preserves audit history)

### Unique Constraints
- users.email (prevents duplicate accounts)
- policy_rules.rule_key (prevents duplicate rules)

### Indexing Strategy
- All primary keys indexed (auto-created)
- All foreign keys indexed (for join performance)
- Unique constraints indexed (for lookups)
- Email indexed (login queries)
- rule_key indexed (policy lookups)

---

## Entity Relationships Summary

```
User (1) ──── (1) Applicant
  │
  ├─── (1) ──── (N) Application
  │                     │
  │                     ├─── (1) ──── (N) Document
  │                     │                   │
  │                     │                   └─── (1) ──── (N) OCRResult
  │                     │
  │                     ├─── (1) ──── (N) ValidationReport
  │                     ├─── (1) ──── (N) Scores
  │                     ├─── (1) ──── (N) Recommendation
  │                     ├─── (1) ──── (N) FairnessCheck
  │                     ├─── (1) ──── (N) HumanReview
  │                     │                  │
  │                     │                  └─── (N) ──── (1) User [reviewer]
  │                     │
  │                     └─── (1) ──── (N) AuditLog
  │
  └─── (N) ──── (1) HumanReview [reviewer]
  └─── (N) ──── (1) AuditLog [actor]

PolicyRule (exists independently, referenced by Recommendation)
```

---

## Default Values & Status Values

### Application Status Values
- `DRAFT` - Initial state, not yet submitted
- `SUBMITTED` - Submitted by applicant
- `IN_PROGRESS` - Being processed
- `PENDING_REVIEW` - Awaiting human review
- `APPROVED` - Approved by system or human
- `DECLINED` - Rejected
- `REFER` - Needs human review

### Document Status Values
- `UPLOADED` - File received
- `PROCESSING` - OCR and validation running
- `PASSED` - Validation successful
- `FAILED` - Validation failed

### Validation Status Values
- `PASS` - All validations passed
- `FAIL` - One or more validations failed
- `HOLD` - Needs manual review

### Fairness Status Values
- `PASS` - Fair decision (matches without demographics)
- `FAIRNESS_FAILURE` - Potential bias detected

### Recommendation Values
- `APPROVE` - Recommend approval
- `REFER` - Refer for human review
- `DECLINE` - Recommend decline

### Role Values
- `Applicant` - Person applying for loan
- `Underwriter` - Reviews applications
- `CreditManager` - Manages policy rules
- `Auditor` - Reviews audit logs

---

## Database Statistics

| Metric | Value |
|--------|-------|
| Total Tables | 13 |
| Primary Keys | 13 |
| Foreign Keys | 11 |
| Unique Constraints | 2 |
| Indexes | 25+ |
| Relationships | 20+ |
| Cascade Rules | 8 |
| Set Null Rules | 3 |

---

## Migration History

### Initial Migration (f6b17df50e69)
- Created all 13 tables with complete schema
- Established all foreign key relationships
- Applied cascade and set null rules
- Created all necessary indexes
- Date: 2026-07-15

---

## Next Steps for Development

1. **Phase 4 - AI Agents**: Implement agent logic for document analysis, scoring, recommendations
2. **Phase 5 - Frontend Integration**: Build React UI for applicants and underwriters
3. **Archival Strategy**: Plan for historical data retention and audit log archiving
4. **Reporting**: Add views or tables for analytics and reporting
5. **Performance Tuning**: Monitor query performance and optimize indexes as needed
