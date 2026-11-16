"""Rebuild the database from data/seed/*.csv — no scraping, no GSMArena calls.

Usage:
    python seed_from_csv.py

Prereqs:
    .env contains DATABASE_URL pointing at a Postgres + pgvector instance
    Tables phones/specifications/phone_features/prices exist (db.py creates them)

After seeding, run `python embed_specs.py` to regenerate spec_chunks vectors.
"""
import csv
from datetime import datetime
from sqlalchemy import text
from db import Base, engine, SessionLocal, Phone, Specification, PhoneFeature, Price


def load(name):
    with open(f"data/seed/{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def fv(v):
    return float(v) if v not in (None, "", "None", "NaN") else None


def iv(v):
    return int(float(v)) if v not in (None, "", "None", "NaN") else None


def sv(v):
    return v if v not in (None, "", "None") else None


def main():
    Base.metadata.create_all(engine)

    with SessionLocal() as sess:
        print("Truncating tables...")
        sess.execute(text(
            "TRUNCATE phones, specifications, phone_features, prices "
            "RESTART IDENTITY CASCADE"
        ))
        sess.commit()

        # --- Phones ---
        old_to_name = {}
        name_to_new_id = {}
        for row in load("phones"):
            old_id = int(row["id"])
            old_to_name[old_id] = row["name"]
            p = Phone(
                name=row["name"],
                gsmarena_id=iv(row.get("gsmarena_id")),
                url=sv(row.get("url")),
                image_url=sv(row.get("image_url")),
                scraped_at=parse_dt(row.get("scraped_at")),
            )
            sess.add(p)
            sess.flush()
            name_to_new_id[row["name"]] = p.id
        sess.commit()
        old_to_new = {old: name_to_new_id[name] for old, name in old_to_name.items()}
        print(f"phones: {len(name_to_new_id)} inserted")

        # --- Specifications ---
        spec_count = 0
        for row in load("specifications"):
            new_pid = old_to_new.get(int(row["phone_id"]))
            if not new_pid:
                continue
            sess.add(Specification(
                phone_id=new_pid,
                category=row["category"],
                label=row["label"],
                value=row["value"],
            ))
            spec_count += 1
        sess.commit()
        print(f"specifications: {spec_count} inserted")

        # --- PhoneFeatures ---
        feat_count = 0
        for row in load("phone_features"):
            new_pid = old_to_new.get(int(row["phone_id"]))
            if not new_pid:
                continue
            sess.add(PhoneFeature(
                phone_id=new_pid,
                release_year=iv(row.get("release_year")),
                os=sv(row.get("os")),
                chipset=sv(row.get("chipset")),
                display_size_in=fv(row.get("display_size_in")),
                display_type=sv(row.get("display_type")),
                resolution=sv(row.get("resolution")),
                ram_gb=iv(row.get("ram_gb")),
                storage_options=sv(row.get("storage_options")),
                main_camera_mp=fv(row.get("main_camera_mp")),
                selfie_camera_mp=fv(row.get("selfie_camera_mp")),
                weight_g=fv(row.get("weight_g")),
                battery_mah=iv(row.get("battery_mah")),
                charging_w=iv(row.get("charging_w")),
                active_use_score_h=fv(row.get("active_use_score_h")),
                endurance_rating_h=fv(row.get("endurance_rating_h")),
            ))
            feat_count += 1
        sess.commit()
        print(f"phone_features: {feat_count} inserted")

        # --- Prices ---
        price_count = 0
        for row in load("prices"):
            new_pid = old_to_new.get(int(row["phone_id"]))
            if not new_pid:
                continue
            sess.add(Price(
                phone_id=new_pid,
                amount=fv(row.get("amount")),
                currency=sv(row.get("currency")),
                variant=sv(row.get("variant")),
                store=sv(row.get("store")),
                source=row["source"],
                raw_text=sv(row.get("raw_text")),
                scraped_at=parse_dt(row.get("scraped_at")),
            ))
            price_count += 1
        sess.commit()
        print(f"prices: {price_count} inserted")

        print("\nDone. Run `python embed_specs.py` to regenerate 740 spec_chunks vectors.")


if __name__ == "__main__":
    main()