# API Documentation

Apex Credit backend serves RESTful HTTP endpoints. All request bodies are JSON unless specified as multipart form uploads.

---

## 1. Authentication Endpoints

### Login Session
- **POST** `/api/auth/login`
- **Request**:
  ```json
  {
    "email": "underwriter@demo.com",
    "password": "Password123@"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "JWT_TOKEN_STRING",
    "refresh_token": "JWT_REFRESH_STRING",
    "token_type": "bearer"
  }
  ```

---

## 2. Credit Application Management

### Create Application
- **POST** `/api/applications/` (Multipart Form)
- **Parameters**:
  - `loan_amount` (float, required)
  - `loan_purpose` (string, required)
  - `term_months` (int, required)
  - `monthly_income` (float, optional)
  - `employer_name` (string, optional)

### Document Upload
- **POST** `/api/applications/{app_id}/documents` (Multipart Form)
- **Parameters**:
  - `document_type` (string, required: Aadhaar, PAN, SalarySlip, BankStatement, EmploymentLetter)
  - `file` (UploadFile, required)

---

## 3. Orchestrator Actions

### Run Workflow
- **POST** `/api/applications/{app_id}/process`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: returns `WorkflowOutput` JSON containing scores, validation report, and audit logs.

### Submit Human Review (HITL Gate)
- **POST** `/api/applications/{app_id}/human-review`
- **Query Params**:
  - `decision` (string, required: `APPROVE` or `DECLINE`)
  - `comment` (string, optional)

---

## 4. Reports & Audits

### Get System Analytics
- **GET** `/api/reports/analytics`
- **Response**: status counts, monthly statistics, risk averages, and fairness violations count.

### Get Evaluation Framework Metrics
- **GET** `/api/evaluation/report`
- **Response**: trace correctness, tool call accuracy, groundedness, and fairness consistency percentages.
