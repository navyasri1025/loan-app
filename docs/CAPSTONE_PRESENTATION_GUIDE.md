# Capstone Presentation Guide

Use this guide to structure the final capstone demonstration, highlighting core agentic workflows, business rules, fairness checks, and security gates.

---

## 1. Login as Staff Persona
1. Navigate to the Login page.
2. Log in using `underwriter@demo.com` and `Password123@`.
3. Open the **Demo Control Suite** using the sidebar link.

---

## 2. Walk Through the Capstone Scenarios

### Scenario 1: Strong Application
- **Action**: Click "Run Scenario 1".
- **Concept**: Demonstrates standard path. The Intake Agent ingests complete fields, validation passes, scoring executes successfully, and decision agent issues an `APPROVE` recommendation.
- **Key Note**: Highlight that the application status updates to `PENDING_REVIEW` - the system does not auto-approve, maintaining the human underwriter gate.

### Scenario 2: Borderline Application
- **Action**: Click "Run Scenario 2".
- **Concept**: Moderate profile credit history and higher DTI (30%).
- **Outcome**: Triggers a `REFER` recommendation. Shows the application routed to the underwriter review queue.

### Scenario 3: Missing Income Proof
- **Action**: Click "Run Scenario 3".
- **Concept**: Missing salary slips.
- **Outcome**: Validation Agent triggers a validation failure, branching directly to `HOLD` status. The scoring engine is skipped, satisfying the business rule: "Never score without required documents".

### Scenario 4: Identity Swapped
- **Action**: Click "Run Scenario 4".
- **Concept**: Fairness validation.
- **Outcome**: The Fairness Agent runs scoring blind (no name, gender, or location). Compares blind recommendation with original to ensure consistency.

### Scenario 5: Prompt Injection Protection
- **Action**: Click "Run Scenario 5".
- **Concept**: Security gate checks.
- **Outcome**: Highlights the blocks of override strings ("Approve regardless", "Skip validation"). The attempts are logged as warnings while standard policy thresholds continue to apply.
