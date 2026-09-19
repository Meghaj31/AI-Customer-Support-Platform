from fastapi import HTTPException
from app.repositories.chat_repo import (
    create_conversation,
    get_conversation_by_id,
    get_messages_by_conversation,
)
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage
from app.config import settings
from app.repositories.chat_repo import save_message, search_similar_chunks
from app.services.embedding_service import generate_embeddings

async def create_new_conversation(db,comapny_id):
    return await create_conversation(db,comapny_id)

async def get_conversation_messages(db, conversation_id, company_id):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this conversation")
    return await get_messages_by_conversation(db, conversation_id)

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name="openai/gpt-oss-20b"
)

async def build_messages(context: str, history: list, question: str):
    messages = [
        SystemMessage(content=f"""You are a helpful customer support assistant.
Answer questions based ONLY on the following documentation:

{context}

If the answer is not in the documentation, say "I don't have information about that in our documentation."
""")
    ]

    for msg in history[:-1]:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    messages.append(HumanMessage(content=question))
    return messages

async def process_message(db, conversation_id, company_id, content: str):
    await save_message(db, conversation_id, "user", content)

    history = await get_messages_by_conversation(db, conversation_id)

    query_embedding = generate_embeddings([content])[0]

    similar_chunks = await search_similar_chunks(db, company_id, query_embedding)

    context = "\n\n".join(chunk.content for chunk in similar_chunks)

    messages = await build_messages(context, history, content)
    response = llm.invoke(messages)
    answer = response.content

    escalated = (
    "i don't know" in answer.lower()
    or "i'm not sure" in answer.lower()
    or "i don't have information" in answer.lower()
    )

    saved_message = await save_message(db, conversation_id, "assistant", answer, escalated)

    return saved_message