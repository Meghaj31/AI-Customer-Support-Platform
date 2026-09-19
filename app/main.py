from fastapi import FastAPI
from app.routers import auth,documents,chat

app=FastAPI(title="AI Customer Support Platform")

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
