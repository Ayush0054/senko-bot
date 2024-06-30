import asyncio
from fastapi import FastAPI
from bot.client import run_discord_bot
from api.routes import router
from services.message_store import MessageStore
from services.rag_service import RAGService
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.include_router(router)

message_store = MessageStore(os.getenv("DATABASE_URL"))
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    await message_store.init_db()
    await rag_service.init_pinecone()
    asyncio.create_task(run_discord_bot())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)