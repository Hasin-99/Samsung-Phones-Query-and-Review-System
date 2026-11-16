import os
from dotenv import load_dotenv
from crewai import LLM, Agent
from crewai.tools import tool
from sqlalchemy import select
from db import SessionLocal, Phone, PhoneFeature

load_dotenv(".env")

llm = LLM(
    model="openai/openai/gpt-oss-120b",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.3,
    max_tokens=4000,
)


@tool("fetch_phone_specs")
def fetch_phone_specs(phone_name: str) -> str:
    """Fetch a Samsung phone's key specifications from the PostgreSQL database.

    Args:
        phone_name: The phone name, e.g. "Samsung Galaxy S23" or "Galaxy S24".
                    Partial matches are accepted.
    """
    with SessionLocal() as s:
        phone = s.scalar(
            select(Phone).where(Phone.name.ilike(f"%{phone_name}%"))
        )
        if not phone:
            return f"No phone found matching '{phone_name}'."
        f = s.scalar(
            select(PhoneFeature).where(PhoneFeature.phone_id == phone.id)
        )
        if not f:
            return f"Phone '{phone.name}' has no feature data."
        # Pull the raw camera block from specifications for full detail
        from db import Specification
        cam_rows = s.scalars(
            select(Specification).where(
                Specification.phone_id == phone.id,
                Specification.category == "Main Camera",
            )
        ).all()
        cam_text = "; ".join(f"{r.label}: {r.value}" for r in cam_rows) or "n/a"

        return (
            f"Phone: {phone.name}\n"
            f"Release year: {f.release_year}\n"
            f'Display: {f.display_size_in}" {f.display_type}\n'
            f"Resolution: {f.resolution}\n"
            f"Chipset: {f.chipset}\n"
            f"OS: {f.os}\n"
            f"RAM: {f.ram_gb} GB\n"
            f"Storage: {f.storage_options}\n"
            f"Main camera: {f.main_camera_mp} MP ({cam_text[:200]})\n"
            f"Selfie camera: {f.selfie_camera_mp} MP\n"
            f"Battery: {f.battery_mah} mAh\n"
            f"Charging: {f.charging_w} W\n"
            f"Endurance: {f.endurance_rating_h} h\n"
            f"Active use: {f.active_use_score_h} h\n"
            f"Weight: {f.weight_g} g"
        )


spec_retriever = Agent(
    role="Samsung Phone Specification Retriever",
    goal="Fetch accurate, complete specifications for the requested Samsung phone from the database.",
    backstory=(
        "You are a meticulous data engineer. You only report what the database "
        "returns. You never invent numbers or specs. You always call the "
        "fetch_phone_specs tool exactly once with the phone name the user asked about."
    ),
    tools=[fetch_phone_specs],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)


review_writer = Agent(
    role="Samsung Phone Product Reviewer",
    goal="Write clear, engaging 300-400 word product reviews based strictly on provided specifications.",
    backstory=(
        "You are a tech journalist who turns dry spec sheets into readable reviews. "
        "You highlight strengths (camera, battery, performance) and any weaknesses "
        "(missing features, heavy weight, old OS). You NEVER invent features not in the specs provided."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)
