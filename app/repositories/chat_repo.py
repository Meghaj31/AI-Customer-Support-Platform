from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.message import Message

async def create_conversation(db:AsyncSession,company_id):
    conversation=Conversation(company_id=company_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation

async def get_conversations_by_company(db: AsyncSession, company_id):
    result = await db.execute(select(Conversation).where(Conversation.company_id == company_id))
    return result.scalars().all()

async def get_conversation_by_id(db: AsyncSession, conversation_id):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()

async def save_message(db: AsyncSession, conversation_id, role: str, content: str, escalated: bool = False):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        escalated=escalated,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def get_messages_by_conversation(db: AsyncSession, conversation_id):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()

async def search_similar_chunks(db: AsyncSession, company_id, query_embedding, limit: int = 5):
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.company_id == company_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return result.scalars().all()