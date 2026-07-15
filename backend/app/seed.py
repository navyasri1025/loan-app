from sqlalchemy.orm import Session
from app.models.user import User
from app.models.applicant import Applicant
from app.models.application import Application
from app.models.document import Document
from app.models.policy_rule import PolicyRule
from app.core.security import get_password_hash
import datetime

def seed_demo_users(db: Session):
    # Check if user table is already seeded
    user_count = db.query(User).count()
    if user_count > 0:
        print("Database already has users. Skipping user seeding...")
        return
        
    print("Database is empty. Seeding default demo users...")
    
    # 1. Seed Core Role Users
    demo_users = [
        {
            "email": "applicant@demo.com",
            "full_name": "Alice Applicant",
            "role": "Applicant",
            "password": "Password123@",
            "profile": {
                "phone": "+919876543210",
                "date_of_birth": "1992-05-15",
                "address": "123, Park Lane, Mumbai, Maharashtra",
                "gender": "Female",
                "monthly_income": 85000.0,
                "employer_name": "Infosys Technologies",
                "employment_type": "Salaried",
                "employment_stability_months": 28,
                "credit_score": 710
            }
        },
        {
            "email": "underwriter@demo.com",
            "full_name": "Bob Underwriter",
            "role": "Underwriter",
            "password": "Password123@",
            "profile": None
        },
        {
            "email": "manager@demo.com",
            "full_name": "Charlie Manager",
            "role": "CreditManager",
            "password": "Password123@",
            "profile": None
        },
        {
            "email": "auditor@demo.com",
            "full_name": "Diane Auditor",
            "role": "Auditor",
            "password": "Password123@",
            "profile": None
        },
        # Scenario 1: Strong Applicant (Alice will also be our strong applicant in tests, but let's make a dedicated test set)
        {
            "email": "strong@demo.com",
            "full_name": "Siddharth Strong",
            "role": "Applicant",
            "password": "Password123@",
            "profile": {
                "phone": "+919998887770",
                "date_of_birth": "1988-08-20",
                "address": "Sector 4, Noida, UP",
                "gender": "Male",
                "monthly_income": 120000.0,
                "employer_name": "Google India",
                "employment_type": "Salaried",
                "employment_stability_months": 45,
                "credit_score": 790
            }
        },
        # Scenario 2: Borderline Applicant
        {
            "email": "borderline@demo.com",
            "full_name": "Bipin Borderline",
            "role": "Applicant",
            "password": "Password123@",
            "profile": {
                "phone": "+919998887771",
                "date_of_birth": "1994-11-03",
                "address": "Marathahalli, Bangalore, Karnataka",
                "gender": "Male",
                "monthly_income": 45000.0,
                "employer_name": "Startup Corp",
                "employment_type": "Salaried",
                "employment_stability_months": 13,
                "credit_score": 660
            }
        },
        # Scenario 3: Missing Docs Applicant
        {
            "email": "missingdocs@demo.com",
            "full_name": "Meera Missing",
            "role": "Applicant",
            "password": "Password123@",
            "profile": {
                "phone": "+919998887772",
                "date_of_birth": "1990-01-30",
                "address": "T Nagar, Chennai, Tamil Nadu",
                "gender": "Female",
                "monthly_income": 60000.0,
                "employer_name": "TCS",
                "employment_type": "Salaried",
                "employment_stability_months": 24,
                "credit_score": 720
            }
        }
    ]
    
    for u in demo_users:
        db_user = User(
            email=u["email"],
            full_name=u["full_name"],
            role=u["role"],
            password_hash=get_password_hash(u["password"]),
            is_active=True
        )
        db.add(db_user)
        db.flush() # Flush to get User ID
        
        if u["profile"]:
            prof = u["profile"]
            db_profile = Applicant(
                id=db_user.id,
                phone=prof["phone"],
                date_of_birth=prof["date_of_birth"],
                address=prof["address"],
                gender=prof["gender"],
                monthly_income=prof["monthly_income"],
                employer_name=prof["employer_name"],
                employment_type=prof["employment_type"],
                employment_stability_months=prof["employment_stability_months"],
                credit_score=prof["credit_score"]
            )
            db.add(db_profile)
            
            # Seed Sample Application for this applicant
            # Siddharth Strong: requests 500k, has monthly debt of 10k (DTI = 10k/120k = 8.3%)
            # Bipin Borderline: requests 800k, has monthly debt of 19.5k (DTI = 19.5k/45k = 43.3%)
            # Meera Missing: requests 600k, has monthly debt of 15k (DTI = 15k/60k = 25%)
            loan_amount = 500000.0
            debt = 10000.0
            purpose = "Home Improvement"
            
            if "borderline" in u["email"]:
                loan_amount = 800000.0
                debt = 19500.0
                purpose = "Debt Consolidation"
            elif "missing" in u["email"]:
                loan_amount = 600000.0
                debt = 15000.0
                purpose = "Education Loan"
                
            db_app = Application(
                applicant_id=db_user.id,
                loan_amount=loan_amount,
                loan_purpose=purpose,
                term_months=36,
                monthly_debt_obligations=debt,
                status="SUBMITTED"
            )
            db.add(db_app)
            db.flush() # Flush to get Application ID
            
            # Seed Document references
            # We seed documents. For Missing Docs applicant, we skip SalarySlip and BankStatement.
            docs_to_create = [
                {"type": "PAN", "path": f"/uploads/{db_user.id}_pan.pdf"},
                {"type": "Aadhaar", "path": f"/uploads/{db_user.id}_aadhaar.pdf"},
            ]
            
            if "missing" not in u["email"]:
                docs_to_create.extend([
                    {"type": "SalarySlip", "path": f"/uploads/{db_user.id}_salary.pdf"},
                    {"type": "BankStatement", "path": f"/uploads/{db_user.id}_bank.pdf"},
                    {"type": "EmploymentLetter", "path": f"/uploads/{db_user.id}_emp.pdf"}
                ])
                
            for d in docs_to_create:
                db_doc = Document(
                    application_id=db_app.id,
                    document_type=d["type"],
                    file_path=d["path"],
                    status="UPLOADED"
                )
                db.add(db_doc)

    db.commit()
    print("Users, applicants, applications, and documents seeded successfully.")


def seed_policy_rules(db: Session):
    rule_count = db.query(PolicyRule).count()
    if rule_count > 0:
        print("Database already has policy rules. Skipping rule seeding...")
        return
        
    print("Seeding underwriting policy rules...")
    
    rules = [
        {
            "name": "Minimum Credit Score",
            "key": "MIN_CREDIT_SCORE",
            "val": 650.0,
            "desc": "The applicant's credit score must be at least 650 to qualify for standard processing."
        },
        {
            "name": "Maximum Debt To Income Ratio",
            "key": "MAX_DTI",
            "val": 0.45,
            "desc": "The total monthly debt obligations including the new loan payment divided by gross income must not exceed 45%."
        },
        {
            "name": "Minimum Employment Stability Months",
            "key": "MIN_EMPLOYMENT_MONTHS",
            "val": 12.0,
            "desc": "Applicant must have at least 12 months of employment stability in their current job."
        },
        {
            "name": "Maximum Single Loan Limit",
            "key": "MAX_LOAN_LIMIT",
            "val": 5000000.0,
            "desc": "Maximum permissible loan size is 5,000,000 INR."
        }
    ]
    
    for r in rules:
        db_rule = PolicyRule(
            rule_name=r["name"],
            rule_key=r["key"],
            threshold_value=r["val"],
            rule_description=r["desc"],
            is_active=True
        )
        db.add(db_rule)
        
    db.commit()
    print("Policy rules seeded successfully.")
