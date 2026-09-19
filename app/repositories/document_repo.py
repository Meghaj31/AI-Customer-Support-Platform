from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

async def create_document(db:AsyncSession,company_id,filename:str):
    document=Document(company_id=company_id,filename=filename)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document

async def get_document_by_company(db:AsyncSession,comany_id):
    result = await db.execute(select(Document).where(Document.company_id==comany_id))
    return result.scalars().all()

async def get_document_by_id(db:AsyncSession,document_id):
    result = await db.execute(select(Document).where(Document.id==document_id))
    return result.scalar_one_or_none()

async def delete_document(db: AsyncSession, document: Document):
    await db.delete(document)
    await db.commit()

async def save_chunks(db:AsyncSession, chunks:list):
    db.add_all(chunks)
    await db.commit()

