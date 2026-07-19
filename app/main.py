from fastapi import FastAPI
from app.routers import auth

app=FastAPI(title="AI Customer Support Platform")

app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
