from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Department, RoleEnum, User
from app.schemas.schemas import DepartmentOut, UserOut
from app.services.deps import get_current_user

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Department).all()


@router.get("/public", response_model=list[DepartmentOut])
def list_departments_public(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.get("/staff/doctors", response_model=list[UserOut])
def list_doctors(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(User).filter(User.role == RoleEnum.doctor).all()
