from app.database import get_db
from fastapi import APIRouter,Depends,UploadFile,File
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.schemas.document import DocumentResponse
from app.services.auth_service import get_current_company
from app.services.document_service import (
    process_and_save_document,
    get_company_documents,
    delete_company_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    file_bytes = await file.read()
    document = await process_and_save_document(db, current_company.id, file.filename, file_bytes)
    return document

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return await get_company_documents(db, current_company.id)

@router.delete("/{document_id}", status_code=204)
async def remove_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    await delete_company_document(db, document_id, current_company.id)