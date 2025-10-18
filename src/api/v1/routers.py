from fastapi import APIRouter

api_v1 = APIRouter(prefix="/v1", tags=["v1"])

@api_v1.get("/healthz")
async def healthz():
    return {"status": "ok"}

# TODO: Add actual endpoints here.