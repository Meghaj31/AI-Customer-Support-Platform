from app.repositories.document_repo import create_document, save_chunks
from app.services.embedding_service import extract_text_from_pdf, chunk_text, generate_embeddings
from app.models.document_chunk import DocumentChunk
from fastapi import HTTPException
from app.repositories.document_repo import create_document, save_chunks, get_document_by_company, get_document_by_id, delete_document

async def process_and_save_document(db, company_id, filename: str, file_bytes: bytes):
    text = extract_text_from_pdf(file_bytes)
    document = await create_document(db, company_id, filename)

    chunks = chunk_text(text)
    embeddings = generate_embeddings(chunks)

    chunk_objects = [
        DocumentChunk(
            document_id=document.id,
            company_id=company_id,
            content=chunk,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    await save_chunks(db, chunk_objects)
    return document

async def get_company_documents(db, company_id):
    return await get_document_by_company(db, company_id)

async def delete_company_document(db, document_id, company_id):
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    await delete_document(db, document)