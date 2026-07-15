# Loan Application Processing Agent - Architecture Documentation

## Project Overview

The Loan Application Processing Agent is a FastAPI-based backend system designed to process loan applications using AI agents for decision-making, validation, and fairness checking. It integrates with document processing, credit scoring, and policy-based underwriting.

**Stack**:
- **Framework**: FastAPI 0.110+
- **Database**: SQLAlchemy ORM with Alembic migrations (SQLite for dev, PostgreSQL for prod)
- **Authentication**: JWT tokens via python-jose
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.6+

---

## Folder Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependency injection (get_db, get_current_user)
│   │   ├── security.py          # Password hashing, JWT tokens
│   │   ├── logging.py           # Centralized logging configuration
│   │   └── exceptions.py        # Exception handlers and custom exceptions
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py              # Users with role-based access
│   │   ├── applicant.py         # Applicant profiles
│   │   ├── application.py       # Loan applications
│   │   ├── document.py          # Uploaded documents
│   │   ├── ocr_result.py        # OCR extraction results
│   │   ├── validation_report.py # Document validation results
│   │   ├── scores.py            # Credit & risk scores
│   │   ├── recommendation.py    # AI agent recommendations
│   │   ├── fairness_check.py    # Bias testing results
│   │   ├── human_review.py      # Underwriter reviews
│   │   ├── audit_log.py         # Audit trail
│   │   └── policy_rule.py       # Policy thresholds
│   │
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── common.py            # Standard API response models
│   │   ├── user.py
│   │   ├── applicant.py
│   │   ├── application.py
│   │   ├── document.py
│   │   ├── ocr_result.py
│   │   ├── validation_report.py
│   │   ├── scores.py
│   │   ├── recommendation.py
│   │   ├── fairness_check.py
│   │   ├── human_review.py
│   │   ├── audit_log.py
│   │   └── policy_rule.py
│   │
│   ├── routers/                 # API endpoint routers
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── applications.py      # Application management
│   │   └── policy.py            # Policy rule management
│   │
│   ├── database.py              # Database configuration & session
│   ├── main.py                  # FastAPI app initialization
│   └── seed.py                  # Database seeding script
│
├── alembic/                     # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   ├── versions/
│   │   └── f6b17df50e69_initial_schema_setup.py
│   └── README
│
├── tests/                       # (Future) Unit & integration tests
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_applications.py
│   └── test_endpoints.py
│
├── logs/                        # Application logs (created at runtime)
│   └── app_20260715.log
│
├── .env                         # Environment configuration
├── alembic.ini                  # Alembic configuration
├── requirements.txt             # Python dependencies
├── loan_agent.db                # SQLite database (dev only)
│
└── docs/
    ├── DATABASE_SCHEMA.md       # Complete schema documentation
    ├── DATABASE_ER_DIAGRAM.md   # Entity-relationship diagram
    ├── PHASE3_VERIFICATION_REPORT.md
    └── architecture.md          # This file
```

---

## Database Architecture

### Schema Design

The database follows a layered domain model:

1. **User Management Layer** (`users`, `applicants`)
   - User authentication and profile management
   - Role-based access control (Applicant, Underwriter, CreditManager, Auditor)
   - Applicant profile with financial and demographic information

2. **Application Processing Layer** (`applications`, `documents`)
   - Loan application data and status tracking
   - Document uploads and tracking
   - OCR extraction results

3. **Validation & Analysis Layer** (`ocr_results`, `validation_reports`, `scores`)
   - Document OCR extraction and parsing
   - Cross-document validation (name matching, date consistency)
   - Income verification and document quality scoring

4. **Decision-Making Layer** (`recommendations`, `fairness_checks`, `human_reviews`)
   - AI agent recommendations based on policy rules
   - Bias/fairness testing using blind scoring
   - Human underwriter reviews

5. **Audit & Compliance Layer** (`audit_logs`, `policy_rules`)
   - Immutable audit trail with state snapshots
   - Policy rule management for underwriting

### Relationship Map

```
User (1) ──────────────────── (1) Applicant
 │
 ├─→ (1) ──── (N) Application ─────┬─→ (N) Document ──→ (N) OCRResult
 │                                 ├─→ (N) ValidationReport
 │                                 ├─→ (N) Scores
 │                                 ├─→ (N) Recommendation
 │                                 ├─→ (N) FairnessCheck
 │                                 ├─→ (N) HumanReview ←─── User [reviewer]
 │                                 └─→ (N) AuditLog
 │
 └─→ (N) AuditLog [as actor]
 └─→ (N) HumanReview [as reviewer]

PolicyRule (referenced by Recommendation via policy_citations)
```

### Cascade Behavior

**DELETE CASCADE** (Parent → Children):
- User → Applicant → Applications → Documents, Reports, Scores, Recommendations, Reviews
- Document → OCRResults

**DELETE SET NULL** (Soft References):
- HumanReview.reviewer_id (when underwriter deleted)
- AuditLog.user_id (when user deleted)
- AuditLog.application_id (preserves audit history)

---

## Request/Response Flow

### Typical Application Submission Flow

```
1. User Registration
   POST /api/auth/register
   └─→ Create User + Applicant profile

2. Authentication
   POST /api/auth/login
   └─→ JWT token issued

3. Application Submission
   POST /api/applications
   └─→ Create Application (status: DRAFT)

4. Document Upload
   POST /api/applications/{id}/documents
   └─→ Create Document (status: UPLOADED)
   └─→ Trigger OCR processing

5. Validation & Scoring (AI Agent - Phase 4)
   - Extract OCR data
   - Validate documents (ValidationReport)
   - Calculate scores (Scores)
   - Check policies (Recommendation)
   - Perform fairness check (FairnessCheck)

6. Human Review (if needed)
   PUT /api/applications/{id}/human-review
   └─→ Create HumanReview

7. Audit Trail
   All operations logged to AuditLog with state snapshots
```

---

## Authentication & Authorization

### JWT Token-Based Authentication

**Token Structure**:
```python
{
    "sub": "user_email",
    "role": "Applicant|Underwriter|CreditManager|Auditor",
    "exp": 1620000000
}
```

**Flow**:
1. User submits email + password to `POST /api/auth/login`
2. Backend validates credentials against `password_hash` in database
3. JWT token generated with user role embedded
4. Token returned to client
5. Client includes `Authorization: Bearer <token>` in all requests

**Dependency Injection**:
```python
# In core/deps.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validate JWT and extract user
    # Return User from database
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Applicant** | View own applications, submit documents, view status |
| **Underwriter** | View all applications, create human reviews, update applications |
| **CreditManager** | Manage policy rules, view analytics |
| **Auditor** | View audit logs, generate reports |

**Authorization Example**:
```python
@router.get("/api/policy/rules/{rule_key}")
async def get_rule(
    rule_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["CreditManager"]))
):
    # Only CreditManager can access this
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | None |
| POST | `/api/auth/login` | Login & get JWT | None |
| POST | `/api/auth/refresh` | Refresh token | Bearer |
| GET | `/api/auth/me` | Get current user | Bearer |

### Applications

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/applications` | List applications | Bearer |
| GET | `/api/applications/{id}` | Get application details | Bearer |
| POST | `/api/applications` | Create application | Bearer |
| PUT | `/api/applications/{id}` | Update application | Bearer |
| GET | `/api/applications/{id}/documents` | List documents | Bearer |
| POST | `/api/applications/{id}/documents` | Upload document | Bearer |

### Policy Rules

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/policy/rules` | List all rules | Bearer |
| GET | `/api/policy/rules/{key}` | Get specific rule | Bearer |
| PUT | `/api/policy/rules/{key}` | Update rule | Bearer, CreditManager |

### Utility

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | API info | None |
| GET | `/health` | Health check | None |
| GET | `/docs` | Swagger UI | None |
| GET | `/redoc` | ReDoc UI | None |

---

## Exception Handling

### Exception Hierarchy

```
Exception
├── AppException (400-level)
│   ├── AuthenticationException (401)
│   ├── AuthorizationException (403)
│   ├── NotFoundException (404)
│   └── ValidationException (422)
├── DatabaseException (500)
└── SQLAlchemyError (caught and converted to 500)
```

### Global Exception Handlers

Located in `app/core/exceptions.py`:

```python
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    # Custom exceptions → JSON with error details

@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    # Pydantic validation errors → JSON with field errors

@app.exception_handler(SQLAlchemyError)
async def database_handler(request, exc):
    # Database errors → JSON with user-friendly message

@app.exception_handler(Exception)
async def general_handler(request, exc):
    # Catch-all for unhandled exceptions
```

### Error Response Format

```json
{
  "success": false,
  "error": "Error type",
  "detail": "Detailed explanation",
  "timestamp": "2026-07-15T18:00:00"
}
```

---

## Logging

### Configuration

Located in `app/core/logging.py`:

- **Console**: INFO level messages
- **File**: DEBUG level messages (rotated at 10MB)
- **Format**: `timestamp [LEVEL] logger_name: message`

### Log Files

- Created in `backend/logs/` directory
- Named by date: `app_20260715.log`
- Rotated when reaching 10MB (5 backup files kept)

### Logger Names

```
app.startup          # Application initialization
app.database         # Database operations
app.auth             # Authentication events
app.applications     # Application processing
app.exceptions       # Exception handling
app.sqlalchemy       # SQLAlchemy warnings (WARNING level)
app.alembic          # Migration execution
```

### Usage

```python
from app.core.logging import get_logger

logger = get_logger("module_name")
logger.info("User registered", extra={"user_id": 123})
logger.error("Database connection failed", exc_info=True)
```

---

## SQLAlchemy Best Practices Implemented

### 1. Lazy Loading Strategy

All relationships use **`lazy="select"`** (eager loading):
- Load related objects immediately when parent is queried
- Avoid N+1 query problems
- Optimize for typical use cases

```python
class User(Base):
    applicant_profile = relationship(
        "Applicant",
        back_populates="user",
        lazy="select"  # Eager load
    )
```

### 2. Cascade Behavior

Intentional cascade rules:
- **CASCADE**: Delete parent → delete children (tight coupling)
- **SET NULL**: Delete parent → nullify foreign key (soft reference)

```python
applicant = relationship(
    "Applicant",
    back_populates="user",
    cascade="all, delete-orphan"  # Delete when parent deleted
)
```

### 3. Back-Populate Relationships

All bidirectional relationships have `back_populates`:
```python
# Parent side
children = relationship("Child", back_populates="parent")

# Child side
parent = relationship("Parent", back_populates="children")
```

### 4. Nullable Field Declarations

Explicit `nullable=True/False`:
```python
# Required field
email = Column(String(100), nullable=False)

# Optional field
phone = Column(String(20), nullable=True)
```

---

## Database Migration Strategy

### Alembic Configuration

- **Location**: `backend/alembic/`
- **Version Control**: Tracked in migrations directory
- **Auto-Generation**: `alembic revision --autogenerate`

### Migration Workflow

```bash
# Create migration (after model changes)
alembic revision --autogenerate -m "description"

# Review generated migration
# Edit if needed for custom logic

# Apply to database
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Production Deployment

Always run migrations before deploying:
```bash
alembic upgrade head  # Apply all pending migrations
```

### Empty Environment Setup

To setup database from scratch:
```bash
# 1. Create empty database (PostgreSQL)
createdb loan_db

# 2. Apply migrations
alembic upgrade head

# 3. Seed demo data (optional)
python app/seed.py
```

---

## Pydantic Schema Design

### Request Models (Create/Update)

Used for incoming API requests:

```python
class ApplicationCreate(BaseModel):
    loan_amount: float
    loan_purpose: Optional[str] = None
    term_months: int
    monthly_debt_obligations: float = 0.0
```

### Response Models (Out)

Used for outgoing API responses:

```python
class ApplicationOut(ApplicationBase):
    id: int
    applicant_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode (v2)
```

### Standard Responses

```python
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str
```

---

## Security Considerations

### 1. Password Hashing

- Using `passlib[bcrypt]` with bcrypt algorithm
- Salted hashes stored in database
- Never store plaintext passwords

### 2. JWT Token Security

- Tokens include user role for authorization
- Expiration set to 60 minutes (configurable via `.env`)
- Refresh token endpoint available for extended sessions

### 3. CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Input Validation

- Pydantic validates all request data
- SQL injection prevented by parameterized queries
- XSS protection via JSON encoding

### 5. Rate Limiting

- TODO: Implement rate limiting in Phase 4+

---

## Performance Optimization

### 1. Database Indexes

Created on:
- Primary keys (auto)
- Foreign keys (for joins)
- Unique constraints (email, rule_key)
- Frequently queried columns (applicant_id, application_id)

### 2. Query Optimization

- Eager loading via `lazy="select"` prevents N+1 queries
- Selective column loading when possible
- Connection pooling via SQLAlchemy engine

### 3. Caching

- TODO: Implement Redis caching in Phase 4+

---

## Testing Strategy

### Unit Tests (To Be Added)

- `tests/test_auth.py` - Authentication endpoints
- `tests/test_applications.py` - Application CRUD
- `tests/test_models.py` - SQLAlchemy models

### Integration Tests (To Be Added)

- End-to-end application workflow
- Database transaction rollback testing
- Authorization checks

### Run Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=app  # With coverage
```

---

## Deployment Considerations

### Prerequisites

1. PostgreSQL 12+ (production)
2. Python 3.10+
3. Environment variables configured

### Environment Setup

```bash
# .env file (production)
DATABASE_URL=postgresql://user:pass@host:5432/loan_db
USE_SQLITE=false
JWT_SECRET=<strong-secret-key>
OPENAI_API_KEY=<your-api-key>
ENVIRONMENT=production
```

### Startup Sequence

1. Load environment variables
2. Connect to database
3. Run Alembic migrations (`alembic upgrade head`)
4. Run seed script (optional, for test data)
5. Start FastAPI app
6. Load OpenAPI documentation

### Monitoring

- Application logs stored in `logs/` directory
- Health check available at `GET /health`
- Request/response logging for audit trail

---

## Phase 4: AI Agents Integration

### Planned Components

1. **Document Processing Agent**
   - Uses OCR results to validate documents
   - Populates `validation_reports` table
   - Handles document failures and retries

2. **Scoring Agent**
   - Calculates scores based on applicant profile
   - Populates `scores` table
   - Computes DTI, risk_score, income stability

3. **Decision Agent**
   - Evaluates scores against `policy_rules`
   - Generates recommendations
   - Cites specific policies
   - Handles APPROVE, REFER, DECLINE

4. **Fairness Agent**
   - Implements blind scoring (without demographics)
   - Compares with regular recommendation
   - Flags fairness failures

5. **Human Review Workflow**
   - Routes REFER cases to underwriters
   - Collects decisions in `human_reviews`
   - Updates application status

### Integration Points

- LangChain/LangGraph for agent orchestration
- OpenAI GPT for reasoning
- Database operations through existing ORM
- Audit logging for all agent actions

---

## Related Documentation

- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Complete table specifications
- [DATABASE_ER_DIAGRAM.md](./DATABASE_ER_DIAGRAM.md) - Visual relationship diagram
- [PHASE3_VERIFICATION_REPORT.md](./PHASE3_VERIFICATION_REPORT.md) - Testing & verification results

---

## Contact & Support

For questions or issues, refer to:
1. API Documentation: `/docs` (Swagger UI)
2. ReDoc: `/redoc` (alternative documentation)
3. Application Logs: `backend/logs/app_YYYYMMDD.log`
4. Database Schema: See DATABASE_SCHEMA.md

**Last Updated**: 2026-07-15  
**Version**: 1.0.0
