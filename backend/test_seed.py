#!/usr/bin/env python
from app.database import SessionLocal
from app.seed import seed_demo_users, seed_policy_rules
from app.models.user import User
from app.models.applicant import Applicant
from app.models.application import Application
from app.models.document import Document
from app.models.policy_rule import PolicyRule

db = SessionLocal()

print("Testing seed script...")
print()

# Run seed
try:
    seed_demo_users(db)
    print()
    seed_policy_rules(db)
    print()
except Exception as e:
    print(f"✗ Seed error: {e}")
    import traceback
    traceback.print_exc()
    db.close()
    exit(1)

# Verify data
print("\n=== Verification ===")
user_count = db.query(User).count()
applicant_count = db.query(Applicant).count()
app_count = db.query(Application).count()
doc_count = db.query(Document).count()
rule_count = db.query(PolicyRule).count()

print(f"✓ Users: {user_count}")
print(f"✓ Applicants: {applicant_count}")
print(f"✓ Applications: {app_count}")
print(f"✓ Documents: {doc_count}")
print(f"✓ Policy Rules: {rule_count}")

# Check for duplicates
print("\n=== Checking for duplicates ===")
users = db.query(User).all()
for user in users:
    if user.email in ['applicant@demo.com', 'strong@demo.com', 'borderline@demo.com', 'missingdocs@demo.com']:
        print(f"User: {user.email} - {user.full_name}")
        if user.applicant_profile:
            print(f"  Applicant: {user.applicant_profile.monthly_income} income, {user.applicant_profile.credit_score} credit")
            apps = user.applicant_profile.applications
            for app in apps:
                print(f"    Application: {app.loan_amount}, {len(app.documents)} docs")

db.close()
print("\n✓ Seed test completed successfully")
