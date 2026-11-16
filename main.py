from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from db import SessionLocal, Phone, PhoneFeature

app = FastAPI(
    title="Samsung Phone Query & Review System",
    description="RAG chatbot + CrewAI review generator over 13 Samsung phones scraped from GSMArena.",
    version="1.0.0",
)

# ── Schemas ────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

class ReviewRequest(BaseModel):
    phone_name: str

class ReviewResponse(BaseModel):
    phone_name: str
    review: str

class PhoneSummary(BaseModel):
    name: str
    release_year: int | None
    chipset: str | None
    display_in: float | None
    main_camera_mp: float | None
    battery_mah: int | None
    ram_gb: int | None
    active_use_h: float | None
    endurance_h: float | None

# ── Endpoints ──────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/phones", response_model=list[PhoneSummary])
def list_phones():
    with SessionLocal() as s:
        rows = s.execute(
            select(
                Phone.name, PhoneFeature.release_year, PhoneFeature.chipset,
                PhoneFeature.display_size_in, PhoneFeature.main_camera_mp,
                PhoneFeature.battery_mah, PhoneFeature.ram_gb,
                PhoneFeature.active_use_score_h, PhoneFeature.endurance_rating_h,
            ).join(PhoneFeature, Phone.id == PhoneFeature.phone_id)
            .order_by(Phone.name)
        ).all()
    return [
        PhoneSummary(
            name=n, release_year=y, chipset=c, display_in=d, main_camera_mp=mc,
            battery_mah=bat, ram_gb=r, active_use_h=au, endurance_h=en,
        )
        for n, y, c, d, mc, bat, r, au, en in rows
    ]

@app.post("/ask", response_model=ChatResponse)
def ask(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(400, "query must not be empty")
    from rag_chat import answer          # lazy import — slow at startup
    return ChatResponse(**answer(req.query))

@app.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    if not req.phone_name.strip():
        raise HTTPException(400, "phone_name must not be empty")
    from crew_runner import generate_review   # lazy import — heavy crewai deps
    try:
        text = generate_review(req.phone_name)
    except Exception as e:
        raise HTTPException(500, f"review generation failed: {e}")
    return ReviewResponse(phone_name=req.phone_name, review=text)
