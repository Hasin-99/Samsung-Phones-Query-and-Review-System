import re
from sqlalchemy import select
from db import SessionLocal, Phone, PhoneFeature, Specification

def num(pattern, text, cast=float):
    m = re.search(pattern, text or "", re.I)
    return cast(m.group(1).replace(",", "")) if m else None

def hours(text):
    m = re.search(r"(\d+):(\d+)\s*h", text or "")
    if m:
        return round(int(m.group(1)) + int(m.group(2)) / 60, 2)
    return num(r"(\d+(?:\.\d+)?)\s*h", text)

def backfill(session):
    phones = session.scalars(select(Phone)).all()
    for phone in phones:
        specs = session.scalars(
            select(Specification).where(Specification.phone_id == phone.id)
        ).all()
        by_cat = {}
        for s in specs:
            by_cat.setdefault(s.category, {})[s.label] = s.value

        feat = session.scalar(
            select(PhoneFeature).where(PhoneFeature.phone_id == phone.id)
        )
        if not feat:
            continue

        changed = []

        # Main camera MP (Triple/Quad/Single/Dual/Penta row)
        if feat.main_camera_mp is None:
            cam_cat = by_cat.get("Main Camera", {})
            for label in ("Triple", "Quad", "Penta", "Dual", "Single"):
                if label in cam_cat:
                    feat.main_camera_mp = num(r"([\d.]+)\s*MP", cam_cat[label])
                    if feat.main_camera_mp:
                        changed.append("main_camera_mp")
                    break

        # Selfie camera MP
        if feat.selfie_camera_mp is None:
            selfie_cat = by_cat.get("Selfie camera", {})
            for label in ("Single", "Dual", "Triple"):
                if label in selfie_cat:
                    feat.selfie_camera_mp = num(r"([\d.]+)\s*MP", selfie_cat[label])
                    if feat.selfie_camera_mp:
                        changed.append("selfie_camera_mp")
                    break

        # Endurance rating (Our Tests / Battery (old))
        if feat.endurance_rating_h is None:
            end_val = by_cat.get("Our Tests", {}).get("Battery (old)")
            if end_val:
                feat.endurance_rating_h = hours(end_val)
                if feat.endurance_rating_h:
                    changed.append("endurance_rating_h")

        # Active use score (Our Tests / Battery)
        if feat.active_use_score_h is None:
            use_val = by_cat.get("Our Tests", {}).get("Battery")
            if use_val:
                feat.active_use_score_h = hours(use_val)
                if feat.active_use_score_h:
                    changed.append("active_use_score_h")

        # Charging watts (Battery / Charging)
        if feat.charging_w is None:
            charging = by_cat.get("Battery", {}).get("Charging", "")
            feat.charging_w = (
                num(r"(\d+)\s*W\s*wired", charging, int)
                or num(r"(\d+)\s*W", charging, int)
            )
            if feat.charging_w:
                changed.append("charging_w")

        print(f"{phone.name:32} -> {changed or 'already complete'}")

    session.commit()

if __name__ == "__main__":
    with SessionLocal() as s:
        backfill(s)
    print("\nBackfill committed.")
