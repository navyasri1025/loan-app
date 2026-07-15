from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, LoginRequest, Token, RefreshTokenRequest, UserUpdate
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists in the system."
        )
    
    # Hash password
    hashed_password = get_password_hash(user_in.password)
    
    # Create user
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hashed_password,
        role=user_in.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == credentials.email).first()
    if not db_user or not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
        
    access_token = create_access_token(subject=db_user.id, role=db_user.role)
    refresh_token = create_refresh_token(subject=db_user.id, role=db_user.role)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": db_user.role,
        "full_name": db_user.full_name,
        "email": db_user.email
    }

@router.post("/refresh", response_model=Token)
def refresh(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims"
        )
        
    db_user = db.query(User).filter(User.id == int(user_id_str)).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
        
    access_token = create_access_token(subject=db_user.id, role=db_user.role)
    # Re-issue new refresh token (rotating refresh tokens)
    new_refresh_token = create_refresh_token(subject=db_user.id, role=db_user.role)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "role": db_user.role,
        "full_name": db_user.full_name,
        "email": db_user.email
    }

@router.post("/logout")
def logout():
    # Since JWT is stateless, logout on backend is a success status.
    # Frontend will clear local tokens.
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
