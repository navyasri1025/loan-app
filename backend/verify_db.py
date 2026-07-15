#!/usr/bin/env python
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.applicant import Applicant
from app.models.application import Application
from app.models.document import Document
from app.models.ocr_result import OCRResult
from app.models.validation_report import ValidationReport
from app.models.policy_rule import PolicyRule
from app.models.scores import Scores
from app.models.recommendation import Recommendation
from app.models.fairness_check import FairnessCheck
from app.models.human_review import HumanReview
from app.models.audit_log import AuditLog

print('✓ All models imported successfully')

# Create tables
Base.metadata.create_all(bind=engine)
print('✓ Tables created via Base.metadata.create_all()')

# Check database
db = SessionLocal()
from sqlalchemy import text
result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
tables = [row[0] for row in result]
print(f'✓ Tables in database: {len(tables)}')
for t in sorted(tables):
    print(f'  - {t}')
db.close()
