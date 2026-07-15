from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.application import Application
from app.models.applicant import Applicant
from app.models.document import Document
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationDetailOut
from app.schemas.document import DocumentOut
from app.core.deps import get_current_user
from app.models.user import User
from typing import List

router = APIRouter(prefix="/api/applications", tags=["Applications"])

@router.get("/", response_model=List[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Underwriters, Managers, and Auditors see all applications
    # Applicants see only their own applications
    if current_user.role in ["Underwriter", "CreditManager", "Auditor"]:
        apps = db.query(Application).all()
    else:
        apps = db.query(Application).filter(Application.applicant_id == current_user.id).all()
    return apps

@router.get("/{app_id}", response_model=ApplicationDetailOut)
def get_application_details(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).options(
        joinedload(Application.applicant)
    ).filter(Application.id == app_id)
    
    app = query.first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    # Check permissions
    if current_user.role == "Applicant" and app.applicant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this application"
        )
        
    return app

@router.get("/{app_id}/documents", response_model=List[DocumentOut])
def get_application_documents(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify application exists
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if current_user.role == "Applicant" and app.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    docs = db.query(Document).filter(Document.application_id == app_id).all()
    return docs


import os
import shutil
from fastapi import UploadFile, File, Form

@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    loan_amount: float = Form(...),
    loan_purpose: str = Form(...),
    term_months: int = Form(...),
    monthly_debt_obligations: float = Form(0.0),
    phone: str = Form(None),
    date_of_birth: str = Form(None),
    address: str = Form(None),
    gender: str = Form(None),
    monthly_income: float = Form(0.0),
    employer_name: str = Form(None),
    employment_type: str = Form("Salaried"),
    employment_stability_months: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if applicant profile exists, create if not
    applicant = db.query(Applicant).filter(Applicant.id == current_user.id).first()
    if not applicant:
        applicant = Applicant(
            id=current_user.id,
            phone=phone,
            date_of_birth=date_of_birth,
            address=address,
            gender=gender,
            monthly_income=monthly_income,
            employer_name=employer_name,
            employment_type=employment_type,
            employment_stability_months=employment_stability_months
        )
        db.add(applicant)
        db.flush()
    else:
        # Update details if provided
        if phone is not None: applicant.phone = phone
        if date_of_birth is not None: applicant.date_of_birth = date_of_birth
        if address is not None: applicant.address = address
        if gender is not None: applicant.gender = gender
        if monthly_income != 0.0: applicant.monthly_income = monthly_income
        if employer_name is not None: applicant.employer_name = employer_name
        if employment_type is not None: applicant.employment_type = employment_type
        if employment_stability_months != 0: applicant.employment_stability_months = employment_stability_months

    # Create application
    application = Application(
        applicant_id=current_user.id,
        loan_amount=loan_amount,
        loan_purpose=loan_purpose,
        term_months=term_months,
        monthly_debt_obligations=monthly_debt_obligations,
        status="DRAFT"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.post("/{app_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_application_document(
    app_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify application exists and user owns it or has manager/underwriter role
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if current_user.role == "Applicant" and app.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Create directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save physical file
    safe_filename = f"{app_id}_{document_type}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save to DB. Relative path /uploads/... makes it easy to serve or fetch
    db_path = f"/uploads/{safe_filename}"
    
    # Check if a document of this type already exists, if so overwrite or create new
    existing_doc = db.query(Document).filter(
        Document.application_id == app_id,
        Document.document_type == document_type
    ).first()

    if existing_doc:
        existing_doc.file_path = db_path
        existing_doc.status = "UPLOADED"
        existing_doc.error_message = None
        db_doc = existing_doc
    else:
        db_doc = Document(
            application_id=app_id,
            document_type=document_type,
            file_path=db_path,
            status="UPLOADED"
        )
        db.add(db_doc)

    db.commit()
    db.refresh(db_doc)
    return db_doc

