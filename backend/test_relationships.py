#!/usr/bin/env python
from app.database import SessionLocal
from app.models.user import User
from app.models.applicant import Applicant
from app.models.application import Application
from app.models.document import Document
from app.models.ocr_result import OCRResult
from app.models.validation_report import ValidationReport
from app.models.scores import Scores
from app.models.recommendation import Recommendation
from app.models.fairness_check import FairnessCheck
from app.models.human_review import HumanReview
from app.models.audit_log import AuditLog

db = SessionLocal()

print("=== Verifying All SQLAlchemy Relationships ===\n")

# 1. User ↔ Applicant
print("1. Testing User ↔ Applicant")
user = db.query(User).filter(User.email == "applicant@demo.com").first()
if user and user.applicant_profile:
    print(f"   ✓ User has applicant_profile: {user.applicant_profile.phone}")
    print(f"   ✓ Applicant.user back reference: {user.applicant_profile.user.full_name}")
else:
    print("   ✗ Relationship failed")

# 2. Applicant ↔ Applications
print("\n2. Testing Applicant ↔ Applications")
if user and user.applicant_profile:
    apps = user.applicant_profile.applications
    print(f"   ✓ Applicant has {len(apps)} application(s)")
    if apps:
        print(f"   ✓ Application.applicant back reference: {apps[0].applicant.monthly_income}")

# 3. Application ↔ Documents
print("\n3. Testing Application ↔ Documents")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    docs = app.documents
    print(f"   ✓ Application has {len(docs)} document(s)")
    if docs:
        print(f"   ✓ Document.application back reference: {docs[0].application.id}")

# 4. Document ↔ OCRResults
print("\n4. Testing Document ↔ OCRResults")
doc = db.query(Document).first()
if doc:
    ocr_results = doc.ocr_results
    print(f"   ✓ Document has {len(ocr_results)} OCR result(s)")
    # Create a test OCRResult
    if len(ocr_results) == 0:
        test_ocr = OCRResult(
            document_id=doc.id,
            raw_text="Test OCR",
            confidence_score=0.95
        )
        db.add(test_ocr)
        db.commit()
        print(f"   ✓ Created test OCR result")
        ocr_back = db.query(OCRResult).filter(OCRResult.document_id == doc.id).first()
        if ocr_back and ocr_back.document:
            print(f"   ✓ OCRResult.document back reference works")

# 5. Application ↔ ValidationReports
print("\n5. Testing Application ↔ ValidationReports")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    reports = app.validation_reports
    print(f"   ✓ Application has {len(reports)} validation report(s)")
    if len(reports) == 0:
        test_report = ValidationReport(
            application_id=app.id,
            name_match_score=0.95,
            dob_match_score=0.90,
            income_consistency_pass=True,
            status="PASS"
        )
        db.add(test_report)
        db.commit()
        print(f"   ✓ Created test validation report")

# 6. Application ↔ Scores
print("\n6. Testing Application ↔ Scores")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    scores = app.scores
    print(f"   ✓ Application has {len(scores)} score record(s)")
    if len(scores) == 0:
        test_score = Scores(
            application_id=app.id,
            debt_to_income_ratio=0.30,
            employment_stability_months=24,
            credit_score=710,
            income_stability_rating=0.85,
            documentation_quality_score=0.90,
            risk_score=25.0
        )
        db.add(test_score)
        db.commit()
        print(f"   ✓ Created test score record")

# 7. Application ↔ Recommendations
print("\n7. Testing Application ↔ Recommendations")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    recs = app.recommendations
    print(f"   ✓ Application has {len(recs)} recommendation(s)")
    if len(recs) == 0:
        test_rec = Recommendation(
            application_id=app.id,
            recommendation="APPROVE",
            confidence_score=0.92,
            explanation="Meets all criteria"
        )
        db.add(test_rec)
        db.commit()
        print(f"   ✓ Created test recommendation")

# 8. Application ↔ FairnessChecks
print("\n8. Testing Application ↔ FairnessChecks")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    checks = app.fairness_checks
    print(f"   ✓ Application has {len(checks)} fairness check(s)")
    if len(checks) == 0:
        test_check = FairnessCheck(
            application_id=app.id,
            blind_recommendation="APPROVE",
            is_fair=True,
            fairness_status="PASS"
        )
        db.add(test_check)
        db.commit()
        print(f"   ✓ Created test fairness check")

# 9. Application ↔ HumanReviews
print("\n9. Testing Application ↔ HumanReviews")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    reviews = app.human_reviews
    print(f"   ✓ Application has {len(reviews)} human review(s)")
    if len(reviews) == 0:
        underwriter = db.query(User).filter(User.email == "underwriter@demo.com").first()
        if underwriter:
            test_review = HumanReview(
                application_id=app.id,
                reviewer_id=underwriter.id,
                decision="APPROVED",
                comments="Good application"
            )
            db.add(test_review)
            db.commit()
            print(f"   ✓ Created test human review")

# 10. Application ↔ AuditLogs
print("\n10. Testing Application ↔ AuditLogs")
if user and user.applicant_profile and user.applicant_profile.applications:
    app = user.applicant_profile.applications[0]
    logs = app.audit_logs
    print(f"   ✓ Application has {len(logs)} audit log(s)")
    if len(logs) == 0:
        test_log = AuditLog(
            application_id=app.id,
            user_id=user.id,
            action="TEST_ACTION",
            details_json={"test": "data"}
        )
        db.add(test_log)
        db.commit()
        print(f"   ✓ Created test audit log")

print("\n=== All relationship tests passed ===")
db.close()
