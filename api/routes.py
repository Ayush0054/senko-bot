from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Discord Bot API is running"}

# Add more API routes as needed