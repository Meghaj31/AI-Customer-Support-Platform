from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import CompanyRegister,CompanyResponse,TokenResponse
from app.database import get_db
from app.models.company import Company
from sqlalchemy.future import select
from app.services.auth_service import hash_password,verify_password,create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=CompanyResponse, status_code=201)
async def register(body: CompanyRegister, db: AsyncSession = Depends(get_db)):
    #checking if the email alerady exists
    result=await db.execute(select(Company).where(Company.email==body.email))
    existing=result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    #adding new company
    company=Company(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    return company

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),db: AsyncSession = Depends(get_db)):
    #find the company by email
    result=await db.execute(select(Company).where(Company.email==form_data.username))
    company=result.scalar_one_or_none()
    #if not found throw exception
    if not company:
        raise HTTPException(status_code=404,detail="Email not registered")
    #verify password
    if not verify_password(form_data.password,company.hashed_password):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    #generate JWT token
    token = create_access_token({"sub": str(company.id)})
    return {"access_token": token, "token_type": "bearer"}
    